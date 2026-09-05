# -*- coding: utf-8 -*-
"""
TBE 学习足迹与历史数据交互 API
负责从云端获取用户的学习记录，并转换为本地可用的多媒体与视频制作素材。
"""

import requests
from typing import List, Dict, Any, Optional, Tuple
from ..config import config


# 本地离线/演示用精选学习足迹（确保新用户无需登录也能秒级体验）
DEMO_FOOTPRINTS: List[Dict[str, Any]] = [
    {
        "id": "demo-article-01",
        "type": "article",
        "title": "How Deep Work Boosts Your Brain (深度工作如何重塑大脑)",
        "source": "YouTube 精选原声",
        "date": "2026-09-05",
        "sentence_count": 6,
        "duration": "1m 45s",
        "preview_cover": "",
        "segments": [
            {
                "en": "Deep work is the ability to focus without distraction on a cognitively demanding task.",
                "cn": "深度工作是指在无干扰的状态下，专注进行高认知要求的任务的能力。",
                "words_sync": [
                    {"w": "Deep", "t": [0.0, 0.4]},
                    {"w": "work", "t": [0.4, 0.8]},
                    {"w": "is", "t": [0.8, 1.0]},
                    {"w": "the", "t": [1.0, 1.2]},
                    {"w": "ability", "t": [1.2, 1.7]},
                    {"w": "to", "t": [1.7, 1.9]},
                    {"w": "focus", "t": [1.9, 2.4]},
                    {"w": "without", "t": [2.4, 2.8]},
                    {"w": "distraction", "t": [2.8, 3.6]}
                ],
                "keywords": [
                    {"word": "cognitively", "def": "在认知层面上", "phonetic": "/ˈkɒɡnətɪvli/"},
                    {"word": "distraction", "def": "分散注意力的事物", "phonetic": "/dɪˈstrækʃn/"}
                ]
            },
            {
                "en": "It's a skill that allows you to quickly master complicated information and produce better results in less time.",
                "cn": "这项技能能让你在更短的时间内快速掌握复杂信息，并产出更高质量的成果。",
                "words_sync": [
                    {"w": "It's", "t": [0.0, 0.3]},
                    {"w": "a", "t": [0.3, 0.4]},
                    {"w": "skill", "t": [0.4, 0.8]},
                    {"w": "that", "t": [0.8, 1.0]},
                    {"w": "allows", "t": [1.0, 1.4]},
                    {"w": "you", "t": [1.4, 1.6]},
                    {"w": "to", "t": [1.6, 1.8]},
                    {"w": "master", "t": [1.8, 2.3]}
                ],
                "keywords": [
                    {"word": "complicated", "def": "复杂的，难懂的", "phonetic": "/ˈkɒmplɪkeɪtɪd/"}
                ]
            }
        ]
    },
    {
        "id": "demo-dialogue-02",
        "type": "dialogue",
        "title": "Coffee Shop Order & Casual Talk (咖啡店点单与即兴交流)",
        "source": "AI 口语跟读",
        "date": "2026-09-04",
        "sentence_count": 4,
        "duration": "58s",
        "preview_cover": "",
        "segments": [
            {
                "en": "Could I get a large oat milk latte with an extra shot of espresso, please?",
                "cn": "麻烦给我来一杯大杯燕麦拿铁，再多加一份浓缩咖啡，谢谢！",
                "words_sync": [
                    {"w": "Could", "t": [0.0, 0.2]},
                    {"w": "I", "t": [0.2, 0.4]},
                    {"w": "get", "t": [0.4, 0.6]},
                    {"w": "a", "t": [0.6, 0.7]},
                    {"w": "large", "t": [0.7, 1.1]},
                    {"w": "oat", "t": [1.1, 1.4]},
                    {"w": "milk", "t": [1.4, 1.7]},
                    {"w": "latte", "t": [1.7, 2.2]}
                ],
                "keywords": [
                    {"word": "espresso", "def": "意式浓缩咖啡", "phonetic": "/eˈspresəʊ/"}
                ]
            },
            {
                "en": "Sure thing! Would you like that hot or iced today?",
                "cn": "没问题！请问今天是要做热的还是加冰呢？",
                "words_sync": [
                    {"w": "Sure", "t": [0.0, 0.3]},
                    {"w": "thing", "t": [0.3, 0.6]},
                    {"w": "Would", "t": [0.6, 0.8]},
                    {"w": "you", "t": [0.8, 1.0]},
                    {"w": "like", "t": [1.0, 1.2]},
                    {"w": "that", "t": [1.2, 1.4]},
                    {"w": "iced", "t": [1.4, 1.9]}
                ],
                "keywords": [
                    {"word": "iced", "def": "冰镇的", "phonetic": "/aɪst/"}
                ]
            }
        ]
    },
    {
        "id": "demo-vocab-03",
        "type": "vocabulary",
        "title": "Top Tech Colloquialisms (硅谷科技圈高频俚语精讲)",
        "source": "生词本沉浸复习",
        "date": "2026-09-03",
        "sentence_count": 3,
        "duration": "45s",
        "preview_cover": "",
        "segments": [
            {
                "en": "Let's touch base next Monday after everyone reviews the architecture RFC.",
                "cn": "等大家审阅完架构设计文档后，我们下周一再碰一下对齐进展。",
                "words_sync": [
                    {"w": "Let's", "t": [0.0, 0.3]},
                    {"w": "touch", "t": [0.3, 0.6]},
                    {"w": "base", "t": [0.6, 1.0]}
                ],
                "keywords": [
                    {"word": "touch base", "def": "联系，商谈，碰头", "phonetic": "[phrase]"}
                ]
            }
        ]
    }
]


class FootprintAPI:
    """学习足迹 API 客户端"""

    def __init__(self):
        self.server_url = config.get("server_url", "https://theboringenglish.com").rstrip("/")
        self.token = config.get("token", "")

    def refresh_auth(self):
        self.server_url = config.get("server_url", "https://theboringenglish.com").rstrip("/")
        self.token = config.get("token", "")

    def _headers(self) -> Dict[str, str]:
        headers = {"User-Agent": "TBE-Desktop-Client/1.0"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def fetch_user_footprints(self, limit: int = 20) -> Tuple[List[Dict[str, Any]], bool, str]:
        """
        拉取学习足迹列表
        返回: (footprints_list, is_cloud_data, message)
        """
        self.refresh_auth()

        # 未登录状态直接返回精美的演示示例
        if not self.token:
            return DEMO_FOOTPRINTS, False, "当前处于离线/游客体验模式，已载入精选足迹示例"

        try:
            url = f"{self.server_url}/api/v1/history?limit={limit}"
            resp = requests.get(url, headers=self._headers(), timeout=5.0)

            if resp.status_code == 200:
                data = resp.json()
                items = data.get("items") or data.get("history") or []
                if items:
                    normalized = []
                    for it in items:
                        normalized.append({
                            "id": it.get("id", ""),
                            "type": it.get("type", "article"),
                            "title": it.get("title") or it.get("topic") or "未命名学习足迹",
                            "source": it.get("source", "TheBoringEnglish"),
                            "date": (it.get("created_at") or "")[:10],
                            "sentence_count": len(it.get("segments", [])),
                            "duration": it.get("duration", "1m+"),
                            "segments": it.get("segments", [])
                        })
                    return normalized, True, f"成功同步 {len(normalized)} 条云端学习足迹"
                return DEMO_FOOTPRINTS, False, "云端暂无足迹记录，已载入精选足迹示例"
            elif resp.status_code == 401:
                return DEMO_FOOTPRINTS, False, "登录凭据已失效，请重新登录"
            else:
                return DEMO_FOOTPRINTS, False, f"同步异常 (HTTP {resp.status_code})，已显示本地示例"
        except Exception as e:
            return DEMO_FOOTPRINTS, False, f"网络连接失败: {e}，已切换为本地示例数据"
