# -*- coding: utf-8 -*-
"""
TBE Client 安全配置与凭证管理器
配置持久化保存在用户系统主目录 (~/.tbe_client_config.json)，绝不保存在项目仓库中，防止密钥泄露。
"""

import os
import json
from pathlib import Path
from typing import Any, Dict, Optional

# 默认配置文件路径在用户主目录
CONFIG_FILE_PATH = os.path.join(os.path.expanduser("~"), ".tbe_client_config.json")
DEFAULT_MODELS_DIR = os.path.join(os.path.expanduser("~"), ".tbe_client", "models")
DEFAULT_AUDIO_OUTPUT_DIR = os.path.join(os.path.expanduser("~"), "Music", "TBE_Audio")

DEFAULT_CONFIG: Dict[str, Any] = {
    # 服务端连接配置
    "server_url": "https://theboringenglish.com",
    "token": "",
    "user_info": {
        "username": "",
        "nickname": "",
        "avatar": "",
        "points": 0,
        "is_admin": False
    },

    # Remotion 视频服务配置
    "remotion_url": "http://localhost:6402",

    # 本地模型配置
    "models_dir": DEFAULT_MODELS_DIR,
    "audio_output_dir": DEFAULT_AUDIO_OUTPUT_DIR,

    # TTS 偏好设置
    "tts_voice": "en-US-JennyNeural",
    "tts_speed": 1.0,
    "tts_pitch": "+0Hz",

    # 算力挂机设置
    "compute_enabled": False,
    "compute_threads": 2,
    "auto_start_compute": False,
    "minimize_to_tray": True,

    # 界面偏好
    "theme": "dark",  # "dark" or "light"
    "window_width": 1180,
    "window_height": 780,
}


class AppConfig:
    """应用配置单例管理器"""

    _instance: Optional["AppConfig"] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AppConfig, cls).__new__(cls)
            cls._instance._data = {}
            cls._instance.load()
        return cls._instance

    def load(self) -> Dict[str, Any]:
        """加载配置（优先文件，其次环境变量覆盖）"""
        self._data = DEFAULT_CONFIG.copy()

        if os.path.exists(CONFIG_FILE_PATH):
            try:
                with open(CONFIG_FILE_PATH, "r", encoding="utf-8") as f:
                    saved_data = json.load(f)
                    if isinstance(saved_data, dict):
                        self._deep_update(self._data, saved_data)
            except Exception as e:
                print(f"[Config] 警告: 读取配置文件失败: {e}，使用默认配置")

        # 环境变量动态覆盖（如 CI 或容器环境）
        if os.getenv("TBE_SERVER_URL"):
            self._data["server_url"] = os.getenv("TBE_SERVER_URL").rstrip("/")
        if os.getenv("TBE_TOKEN"):
            self._data["token"] = os.getenv("TBE_TOKEN")
        if os.getenv("REMOTION_SERVICE_URL"):
            self._data["remotion_url"] = os.getenv("REMOTION_SERVICE_URL").rstrip("/")
        if os.getenv("CLIENT_MODELS_DIR"):
            self._data["models_dir"] = os.getenv("CLIENT_MODELS_DIR")

        # 确保基础输出目录存在
        os.makedirs(self._data["models_dir"], exist_ok=True)
        os.makedirs(self._data["audio_output_dir"], exist_ok=True)

        return self._data

    def save(self) -> bool:
        """安全保存配置到用户目录"""
        try:
            config_dir = os.path.dirname(CONFIG_FILE_PATH)
            os.makedirs(config_dir, exist_ok=True)
            with open(CONFIG_FILE_PATH, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"[Config] 错误: 保存配置失败: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any, auto_save: bool = True):
        self._data[key] = value
        if auto_save:
            self.save()

    def _deep_update(self, target: dict, source: dict):
        for k, v in source.items():
            if isinstance(v, dict) and k in target and isinstance(target[k], dict):
                self._deep_update(target[k], v)
            else:
                target[k] = v

    @property
    def is_logged_in(self) -> bool:
        return bool(self._data.get("token"))

    def clear_auth(self):
        self._data["token"] = ""
        self._data["user_info"] = DEFAULT_CONFIG["user_info"].copy()
        self.save()


# 全局单例
config = AppConfig()
