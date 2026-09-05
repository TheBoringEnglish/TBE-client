# -*- coding: utf-8 -*-
"""
TBE 本地算力代跑与任务守护后台线程 (QThread)
主动连接云端服务器，领取用户自身或社区的 TTS/音频合成任务，使用本地 GPU/CPU 算力处理并回传。
"""

import os
import time
import json
import base64
import asyncio
import traceback
from typing import Optional
from PySide6.QtCore import QThread, Signal

from ..config import config
from .tts_engine import LocalTTSManager


class ComputeWorkerThread(QThread):
    """分布式算力节点后台守护线程"""

    # 信号定义
    log_signal = Signal(str)            # 日志行输出
    status_signal = Signal(str, str)    # (status_code, status_text)
    task_done_signal = Signal(dict)     # 任务完成信息

    def __init__(self):
        super().__init__()
        self._is_running = False
        self.tts_engine = LocalTTSManager()
        self.total_completed = 0
        self.start_time = 0

    def run(self):
        self._is_running = True
        self.start_time = time.time()
        self.status_signal.emit("connecting", "正在连接算力分发中心...")
        self.log_signal.emit(f"[{time.strftime('%H:%M:%S')}] 🚀 算力代跑节点已启动")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(self._main_loop())
        except Exception as e:
            self.log_signal.emit(f"[{time.strftime('%H:%M:%S')}] ❌ 守护线程异常退出: {e}")
        finally:
            loop.close()
            self._is_running = False
            self.status_signal.emit("stopped", "算力节点已停止")

    def stop(self):
        """外部请求终止线程"""
        self._is_running = False
        self.wait(1500)

    async def _main_loop(self):
        server_url = config.get("server_url", "https://theboringenglish.com").rstrip("/")
        token = config.get("token", "")

        # 派生 WebSocket 协议
        ws_url = server_url.replace("http://", "ws://").replace("https://", "wss://") + "/ws/compute"

        import websockets

        retry_interval = 3
        while self._is_running:
            try:
                self.log_signal.emit(f"[{time.strftime('%H:%M:%S')}] 正在连入算力调度总线: {ws_url}...")
                headers = {}
                if token:
                    headers["Authorization"] = f"Bearer {token}"

                async with websockets.connect(
                    ws_url,
                    extra_headers=headers,
                    ping_interval=20,
                    ping_timeout=20,
                    close_timeout=5
                ) as ws:
                    self.status_signal.emit("running", "算力在线 (挂机运行中)")
                    self.log_signal.emit(f"[{time.strftime('%H:%M:%S')}] ✅ 握手成功！节点已加入分布式算力网")

                    while self._is_running:
                        try:
                            msg_str = await asyncio.wait_for(ws.recv(), timeout=30.0)
                            data = json.loads(msg_str)
                            action = data.get("action") or data.get("type")

                            if action == "ping":
                                await ws.send(json.dumps({"action": "pong", "time": time.time()}))
                            elif action == "task":
                                await self._handle_task(ws, data)
                        except asyncio.TimeoutError:
                            # 30秒无消息，主动探测心跳
                            await ws.send(json.dumps({"action": "heartbeat", "time": time.time()}))
                        except Exception as inner_e:
                            if not self._is_running:
                                break
                            raise inner_e

            except Exception as conn_err:
                if not self._is_running:
                    break
                self.status_signal.emit("reconnecting", f"连接中断，{retry_interval}s 后自动重连")
                self.log_signal.emit(f"[{time.strftime('%H:%M:%S')}] ⚠️ 调度连接异常: {conn_err}，等待重试...")
                await asyncio.sleep(retry_interval)
                retry_interval = min(retry_interval * 1.5, 15)

    async def _handle_task(self, ws, task_data: dict):
        """处理下发的算力代跑任务（如批量 TTS 生成）"""
        task_id = task_data.get("task_id", "unknown")
        task_type = task_data.get("task_type", "tts")
        payload = task_data.get("payload", {})

        self.log_signal.emit(f"[{time.strftime('%H:%M:%S')}] 📥 领取新任务: [{task_type.upper()}] ID={task_id}")

        if task_type == "tts":
            text = payload.get("text", "")
            voice = payload.get("voice", "en-US-JennyNeural")
            speed = float(payload.get("speed", 1.0))

            t0 = time.time()
            audio_bytes, err = await self.tts_engine.synthesize(text, voice_id=voice, speed=speed)
            elapsed = round(time.time() - t0, 2)

            if audio_bytes:
                b64_audio = base64.b64encode(audio_bytes).decode("utf-8")
                reply = {
                    "action": "task_result",
                    "task_id": task_id,
                    "success": True,
                    "cost_time": elapsed,
                    "audio_b64": b64_audio
                }
                await ws.send(json.dumps(reply))
                self.total_completed += 1
                self.log_signal.emit(f"[{time.strftime('%H:%M:%S')}] ✨ 任务完成: {task_id} (耗时: {elapsed}s)")
                self.task_done_signal.emit({"id": task_id, "cost": elapsed, "total": self.total_completed})
            else:
                reply = {
                    "action": "task_result",
                    "task_id": task_id,
                    "success": False,
                    "error": err or "合成失败"
                }
                await ws.send(json.dumps(reply))
                self.log_signal.emit(f"[{time.strftime('%H:%M:%S')}] ❌ 任务失败: {task_id}, 原因: {err}")
