# -*- coding: utf-8 -*-
"""
Remotion 视频工程与实时预览桥接器
支持本地 Remotion 视频服务状态检测、足迹数据一键转视频 JSON、一键拉起 Remotion Studio 浏览器预览。
"""

import os
import json
import requests
import subprocess
import webbrowser
from typing import Dict, Any, List, Optional, Tuple
from ..config import config


class RemotionBridge:
    """Remotion 视频桥接管理中心"""

    def __init__(self, service_url: Optional[str] = None):
        self.service_url = (service_url or config.get("remotion_url", "http://localhost:6402")).rstrip("/")

    def update_url(self, new_url: str):
        self.service_url = new_url.rstrip("/")

    def check_health(self) -> Tuple[bool, str]:
        """检查后台 Remotion 服务是否连通"""
        try:
            resp = requests.get(f"{self.service_url}/health", timeout=2.5)
            if resp.status_code == 200:
                return True, "Remotion 视频服务在线"
            return False, f"服务响应异常: HTTP {resp.status_code}"
        except requests.exceptions.ConnectionError:
            return False, "Remotion 服务未启动 (默认端口 6402)"
        except Exception as e:
            return False, f"检测失败: {str(e)}"

    def get_projects(self) -> List[Dict[str, Any]]:
        """获取可用的 Remotion 模板工程列表"""
        try:
            resp = requests.get(f"{self.service_url}/api/remotion/projects", timeout=3.0)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("projects", [])
        except Exception as e:
            print(f"[RemotionBridge] 获取工程列表异常: {e}")

        # 默认预设工程模板兜底（保证离线或断网时界面依然展示）
        return [
            {"id": "remotion_text1", "name": "纯文字动画模板 (text1)", "port": 3000, "is_running": False},
            {"id": "remotion_video1", "name": "动态视频背景模板 (video1)", "port": 3001, "is_running": False},
            {"id": "remotion_video2", "name": "复古羊皮纸 Markdown (video2)", "port": 3002, "is_running": False},
            {"id": "pictalk", "name": "图说智能跟读卡片 (pictalk)", "port": 3003, "is_running": False},
            {"id": "remotion_scenario", "name": "连续情景互动视频 (scenario)", "port": 3004, "is_running": False},
            {"id": "remotion_cloze", "name": "完形填空互动精讲 (cloze)", "port": 3008, "is_running": False},
        ]

    def convert_footprint_to_remotion_json(
        self,
        title: str,
        segments: List[Dict[str, Any]],
        intro_text: str = "Welcome to this lesson"
    ) -> Dict[str, Any]:
        """将学习足迹转换为标准 Remotion 视频工程数据结构"""
        remotion_json = {
            "intro": {
                "video_url": "",
                "image_url": "",
                "keyframes": [],
                "sub_segments": [
                    {"text": title, "timestamp": [0, 40]},
                    {"text": intro_text, "timestamp": [40, 80]}
                ]
            },
            "chapters": [
                {
                    "title": title,
                    "paragraphs": []
                }
            ]
        }

        for seg in segments:
            en_text = seg.get("en") or seg.get("text_en") or seg.get("content") or ""
            cn_text = seg.get("cn") or seg.get("text_native") or seg.get("translation") or ""
            audio_url = seg.get("audio") or seg.get("audio_url") or ""

            # 解析单词同步字幕
            raw_sync = seg.get("words_sync") or seg.get("audio_metadata") or []
            formatted_sync = []
            for item in raw_sync:
                if isinstance(item, dict):
                    w = item.get("w") or item.get("word") or item.get("text") or ""
                    t = item.get("t")
                    if not t and "start" in item and "end" in item:
                        s = item["start"] / 1000.0 if item["start"] > 100 else item["start"]
                        e = item["end"] / 1000.0 if item["end"] > 100 else item["end"]
                        t = [round(s, 3), round(e, 3)]
                    if w and t:
                        formatted_sync.append({"w": w, "t": t, "cn": item.get("cn", "")})

            # 计算片段持续时长
            duration = 4.0
            if formatted_sync:
                duration = max(3.0, formatted_sync[-1]["t"][1] + 0.5)
            elif en_text:
                duration = max(3.0, len(en_text.split()) * 0.4)

            paragraph = {
                "audio": audio_url,
                "start_time": 0,
                "duration": round(duration, 2),
                "sentences": [
                    {
                        "en": en_text,
                        "cn": cn_text,
                        "words_sync": formatted_sync,
                        "grammar": seg.get("grammar", [])
                    }
                ],
                "keywords_cards": []
            }

            # 提取重点词汇卡片
            for kw in (seg.get("keywords") or []):
                if isinstance(kw, dict) and kw.get("word"):
                    paragraph["keywords_cards"].append({
                        "word": kw.get("word"),
                        "def": kw.get("def") or kw.get("translation") or "",
                        "phonetic": kw.get("phonetic", "")
                    })

            remotion_json["chapters"][0]["paragraphs"].append(paragraph)

        return remotion_json

    def launch_preview(
        self,
        project_id: str = "remotion_text1",
        port: int = 3000,
        payload_data: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """
        一键拉起 Remotion Studio 预览
        1. 如果提供了 payload_data，则先同步写入目标模板的 data.json
        2. 向本地服务请求拉起该模板的 Studio 端口，并在浏览器中自动打开
        """
        # 1. 尝试通过 API 同步数据并启动
        try:
            # 同步写入
            if payload_data:
                sync_url = f"{self.service_url}/api/remotion/transform"
                sync_body = {
                    "title": payload_data.get("title", "TBE Study Footprint"),
                    "segments": payload_data.get("segments", []),
                    "save_to": project_id
                }
                try:
                    requests.post(sync_url, json=sync_body, timeout=3.0)
                except Exception as sync_err:
                    print(f"[RemotionBridge] 自动同步数据警告: {sync_err}")

            # 发送启动指令
            start_url = f"{self.service_url}/api/remotion/start/{project_id}?port={port}"
            resp = requests.post(start_url, timeout=4.0)

            if resp.status_code == 200:
                target_url = f"http://localhost:{port}"
                webbrowser.open(target_url)
                return True, f"已在浏览器打开 Remotion 预览页面: {target_url}"
        except Exception as e:
            print(f"[RemotionBridge] 远程拉起异常: {e}")

        # 2. 如果服务未就绪，直接在浏览器中打开目标端口或给出清晰提示
        target_url = f"http://localhost:{port}"
        webbrowser.open(target_url)
        return True, f"正在打开本地预览地址: {target_url} (请确保后台 Remotion 运行时已启动)"
