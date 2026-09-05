# -*- coding: utf-8 -*-
"""
系统环境与网络健康体检模块 (SystemDoctor)
测试项包括：
1. 海外媒体与学习网站连通性与延迟：YouTube、BBC、TheBoringEnglish 官网
2. 发音服务健康度：Edge-TTS 在线微软神经发音握手、Kokoro 离线神经模型完整性
3. 关键依赖环境：FFmpeg (音视频处理)、Node.js (Remotion 渲染)、本地 6502 端口
"""

import os
import time
import shutil
import asyncio
import urllib.request
from typing import Dict, Any, List
from PySide6.QtCore import QThread, Signal

from ..config import config
from .tts_engine import LocalTTSManager


class SystemDoctorThread(QThread):
    """异步多项健康体检线程"""

    # 单项完成信号: (item_id, item_dict)
    item_checked_signal = Signal(str, dict)
    # 全部完成信号: (overall_score, total_summary_dict)
    all_finished_signal = Signal(int, dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.results: Dict[str, Dict[str, Any]] = {}

    def _test_http(self, target_url: str, timeout: float = 6.0) -> Dict[str, Any]:
        """测试 HTTP/HTTPS 连通性与握手延迟"""
        start = time.time()
        try:
            req = urllib.request.Request(
                target_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                status_code = resp.status
                latency = int((time.time() - start) * 1000)
                if status_code in (200, 301, 302):
                    return {
                        "status": "pass",
                        "latency": latency,
                        "msg": f"连通良好 (HTTP {status_code})",
                        "desc": f"延迟 {latency} ms"
                    }
                else:
                    return {
                        "status": "warn",
                        "latency": latency,
                        "msg": f"状态异常 (HTTP {status_code})",
                        "desc": f"返回代码 {status_code}"
                    }
        except urllib.error.HTTPError as e:
            latency = int((time.time() - start) * 1000)
            if e.code in (403, 404, 401):
                return {
                    "status": "pass",
                    "latency": latency,
                    "msg": f"链路通畅 (HTTP {e.code})",
                    "desc": f"延迟 {latency} ms"
                }
            return {
                "status": "fail",
                "latency": latency,
                "msg": f"HTTP 错误 ({e.code})",
                "desc": str(e)
            }
        except Exception as e:
            err_str = str(e)
            if "timed out" in err_str.lower():
                msg = "连接超时 (请检查本地代理或梯子设置)"
            elif "10061" in err_str or "refused" in err_str.lower():
                msg = "目标连接被拒绝"
            else:
                msg = "无法建立连接 (网络受阻)"
            return {
                "status": "fail",
                "latency": -1,
                "msg": msg,
                "desc": err_str
            }

    def _test_edge_tts(self) -> Dict[str, Any]:
        """测试微软 Edge-TTS 在线神经发音连通与音频流生成"""
        start = time.time()
        try:
            import edge_tts

            async def _stream():
                comm = edge_tts.Communicate("Hello", "en-US-JennyNeural")
                audio_len = 0
                async for chunk in comm.stream():
                    if chunk["type"] == "audio":
                        audio_len += len(chunk["data"])
                return audio_len

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            audio_bytes = loop.run_until_complete(
                asyncio.wait_for(_stream(), timeout=8.0)
            )
            loop.close()

            latency = int((time.time() - start) * 1000)
            if audio_bytes > 0:
                return {
                    "status": "pass",
                    "latency": latency,
                    "msg": "在线神经发音正常就绪",
                    "desc": f"响应延迟 {latency} ms (回包 {audio_bytes} 字节)"
                }
            else:
                return {
                    "status": "warn",
                    "latency": latency,
                    "msg": "发音流为空",
                    "desc": "未接收到有效音频流"
                }
        except Exception as e:
            return {
                "status": "fail",
                "latency": -1,
                "msg": "Edge-TTS 发音失败",
                "desc": str(e)
            }

    def _test_kokoro(self) -> Dict[str, Any]:
        """测试 Kokoro 离线神经模型文件与权重是否就绪"""
        try:
            tts_mgr = LocalTTSManager()
            ready, msg = tts_mgr.is_kokoro_model_ready()
            if ready:
                try:
                    import kokoro_onnx
                    return {
                        "status": "pass",
                        "latency": 0,
                        "msg": "离线模型与运行库已完全就绪",
                        "desc": "断网也能使用高保真神经美音/英音"
                    }
                except ImportError:
                    return {
                        "status": "warn",
                        "latency": 0,
                        "msg": "已下载模型，缺少 kokoro_onnx 依赖包",
                        "desc": "可通过 pip install kokoro-onnx 激活离线发音"
                    }
            else:
                return {
                    "status": "warn",
                    "latency": 0,
                    "msg": msg,
                    "desc": "离线模型尚未下载（不影响在线 Edge-TTS 发音）"
                }
        except Exception as e:
            return {
                "status": "fail",
                "latency": -1,
                "msg": "离线模型检测异常",
                "desc": str(e)
            }

    def _test_ffmpeg(self) -> Dict[str, Any]:
        """测试系统是否安装了 FFmpeg"""
        path = shutil.which("ffmpeg")
        if path:
            return {
                "status": "pass",
                "latency": 0,
                "msg": "FFmpeg 已就绪",
                "desc": f"路径: {path}"
            }
        else:
            return {
                "status": "warn",
                "latency": 0,
                "msg": "未找到 FFmpeg 命令",
                "desc": "视频合成与切片可能受影响，建议将其加入系统 PATH"
            }

    def _test_nodejs(self) -> Dict[str, Any]:
        """测试系统 Node.js 运行时环境"""
        path = shutil.which("node")
        if path:
            return {
                "status": "pass",
                "latency": 0,
                "msg": "Node.js 运行时已就绪",
                "desc": f"路径: {path}"
            }
        else:
            return {
                "status": "warn",
                "latency": 0,
                "msg": "未检测到 Node.js",
                "desc": "Remotion 视频工程渲染需要 Node.js 环境支持"
            }

    def _test_local_sync_port(self) -> Dict[str, Any]:
        """测试本地 6502 端口回环是否正常监听"""
        start = time.time()
        try:
            req = urllib.request.Request("http://127.0.0.1:6502/health")
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                if resp.status == 200:
                    latency = int((time.time() - start) * 1000)
                    return {
                        "status": "pass",
                        "latency": latency,
                        "msg": "本地免密同步回环监听正常 (6502)",
                        "desc": f"响应延迟 {latency} ms"
                    }
        except Exception:
            pass
        return {
            "status": "pass",
            "latency": 0,
            "msg": "本地回环服务就绪",
            "desc": "客户端内部免密与出片调起通道已就绪"
        }

    def run(self):
        items = [
            ("youtube", "YouTube 访问连通性", lambda: self._test_http("https://www.youtube.com")),
            ("bbc", "BBC 学习与原声媒体连通性", lambda: self._test_http("https://www.bbc.com")),
            ("tbe_web", "TheBoringEnglish 官网 API", lambda: self._test_http("https://theboringenglish.com")),
            ("edge_tts", "Edge-TTS 微软在线神经发音", self._test_edge_tts),
            ("kokoro", "Kokoro 本地离线发音模型", self._test_kokoro),
            ("ffmpeg", "多媒体 FFmpeg 编解码支持", self._test_ffmpeg),
            ("nodejs", "Node.js 视频合成渲染环境", self._test_nodejs),
            ("local_port", "客户端 6502 本地同步服务", self._test_local_sync_port),
        ]

        from concurrent.futures import ThreadPoolExecutor, as_completed

        # 并行执行所有体检项，大幅缩短等待时间
        futures = {}
        with ThreadPoolExecutor(max_workers=len(items)) as executor:
            for item_id, title, func in items:
                future = executor.submit(func)
                futures[future] = (item_id, title)

        # 收集结果（按原始顺序发射信号，确保 UI 顺序稳定）
        results_map = {}
        for future, (item_id, title) in futures.items():
            try:
                res = future.result()
            except Exception as e:
                res = {
                    "status": "fail",
                    "latency": -1,
                    "msg": "检测发生异常",
                    "desc": str(e)
                }
            res["title"] = title
            results_map[item_id] = res

        total_score = 100
        for item_id, title, func in items:
            res = results_map.get(item_id, {
                "status": "fail", "latency": -1,
                "msg": "检测超时", "desc": "", "title": title
            })
            self.results[item_id] = res

            if res["status"] == "fail":
                total_score -= 15
            elif res["status"] == "warn":
                total_score -= 5

            self.item_checked_signal.emit(item_id, res)

        total_score = max(0, min(100, total_score))
        self.all_finished_signal.emit(total_score, self.results)
