# -*- coding: utf-8 -*-
"""
本地 Remotion 视频出片历史管理器 (VideoHistoryManager)
管理从网页端或本地触发生成过的 Remotion 视频历史工程记录。
历史记录保存在本地 ~/.tbe_client/video_history.json 中。
"""

import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

HISTORY_FILE = os.path.join(os.path.expanduser("~"), ".tbe_client", "video_history.json")


class VideoHistoryManager:
    """本地出片历史记录管理器"""

    @classmethod
    def load_history(cls) -> List[Dict[str, Any]]:
        if not os.path.exists(HISTORY_FILE):
            # 首次默认提供基础示例档案，方便新用户直观查看
            default_history = [
                {
                    "id": "rec-demo-01",
                    "title": "How Deep Work Boosts Your Brain (深度工作如何重塑大脑)",
                    "template_name": "动态视频背景模板 (video1)",
                    "project_id": "remotion_video1",
                    "port": 3001,
                    "generated_at": "2026-09-05 14:30",
                    "sentence_count": 6,
                    "duration": "1m 45s",
                    "status": "ready",
                    "preview_url": "http://localhost:3001",
                    "source": "theboringenglish.com 网页端足迹"
                },
                {
                    "id": "rec-demo-02",
                    "title": "Coffee Shop Order & Casual Talk (咖啡店点单与即兴交流)",
                    "template_name": "纯文字动画模板 (text1)",
                    "project_id": "remotion_text1",
                    "port": 3000,
                    "generated_at": "2026-09-04 19:15",
                    "sentence_count": 4,
                    "duration": "58s",
                    "status": "ready",
                    "preview_url": "http://localhost:3000",
                    "source": "theboringenglish.com 网页端跟读"
                }
            ]
            cls.save_history(default_history)
            return default_history

        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception as e:
            print(f"[VideoHistoryManager] 读取出片历史失败: {e}")
        return []

    @classmethod
    def save_history(cls, history: List[Dict[str, Any]]) -> bool:
        try:
            os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"[VideoHistoryManager] 保存出片历史失败: {e}")
            return False

    @classmethod
    def add_record(cls, title: str, project_id: str, port: int = 3000, template_name: str = "", sentence_count: int = 0, duration: str = "", source: str = "theboringenglish.com 网页端") -> Dict[str, Any]:
        history = cls.load_history()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M")

        # 检查是否已有同名或相同 project_id 的记录，更新置顶
        new_record = {
            "id": f"rec-{int(datetime.now().timestamp())}",
            "title": title or "未命名足迹视频",
            "template_name": template_name or project_id,
            "project_id": project_id,
            "port": port,
            "generated_at": now_str,
            "sentence_count": sentence_count,
            "duration": duration or "1m+",
            "status": "ready",
            "preview_url": f"http://localhost:{port}",
            "source": source
        }

        # 移除已有相同标题记录，确保不重复
        history = [h for h in history if h.get("title") != title]
        history.insert(0, new_record)
        cls.save_history(history)
        return new_record

    @classmethod
    def delete_record(cls, record_id: str) -> bool:
        history = cls.load_history()
        history = [h for h in history if h.get("id") != record_id]
        return cls.save_history(history)

    @classmethod
    def clear_all(cls) -> bool:
        return cls.save_history([])
