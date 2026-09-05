# -*- coding: utf-8 -*-
"""
统一 TTS 本地发音引擎 (Edge-TTS + Kokoro 本地离线神经网络双模驱动)
支持高保真英语、双语发音试听、音速微调、批量导出 MP3/WAV。
"""

import os
import io
import asyncio
import tempfile
import urllib.request
from typing import Optional, Tuple, List, Dict, Any

# 音色预设定义
SUPPORTED_VOICES: List[Dict[str, Any]] = [
    # ── Edge-TTS 高音质云端音色 ──
    {"id": "en-US-JennyNeural", "name": "美音·Jenny (女声·生动自然)", "type": "edge", "lang": "en-US", "gender": "Female"},
    {"id": "en-US-GuyNeural", "name": "美音·Guy (男声·沉稳自信)", "type": "edge", "lang": "en-US", "gender": "Male"},
    {"id": "en-US-AriaNeural", "name": "美音·Aria (女声·富有感染力)", "type": "edge", "lang": "en-US", "gender": "Female"},
    {"id": "en-US-ChristopherNeural", "name": "美音·Christopher (男声·电台质感)", "type": "edge", "lang": "en-US", "gender": "Male"},
    {"id": "en-GB-SoniaNeural", "name": "英音·Sonia (女声·标准RP播音)", "type": "edge", "lang": "en-GB", "gender": "Female"},
    {"id": "en-GB-RyanNeural", "name": "英音·Ryan (男声·优雅绅士)", "type": "edge", "lang": "en-GB", "gender": "Male"},
    {"id": "zh-CN-XiaoxiaoNeural", "name": "中英双语·晓晓 (女声·自然亲切)", "type": "edge", "lang": "zh-CN", "gender": "Female"},
    {"id": "zh-CN-YunxiNeural", "name": "中文·云希 (男声·阳光活力)", "type": "edge", "lang": "zh-CN", "gender": "Male"},

    # ── Kokoro ONNX 本地离线神经发音 ──
    {"id": "kokoro:af_bella", "name": "离线美音·Bella (女声·明亮清澈)", "type": "kokoro", "lang": "en-US", "gender": "Female"},
    {"id": "kokoro:af_sarah", "name": "离线美音·Sarah (女声·温柔亲切)", "type": "kokoro", "lang": "en-US", "gender": "Female"},
    {"id": "kokoro:af_nicole", "name": "离线美音·Nicole (女声·自然低语)", "type": "kokoro", "lang": "en-US", "gender": "Female"},
    {"id": "kokoro:am_michael", "name": "离线美音·Michael (男声·标准美式口音)", "type": "kokoro", "lang": "en-US", "gender": "Male"},
    {"id": "kokoro:am_adam", "name": "离线美音·Adam (男声·浑厚有磁性)", "type": "kokoro", "lang": "en-US", "gender": "Male"},
    {"id": "kokoro:bf_emma", "name": "离线英音·Emma (女声·英伦标准发音)", "type": "kokoro", "lang": "en-GB", "gender": "Female"},
    {"id": "kokoro:bm_george", "name": "离线英音·George (男声·BBC纪实风格)", "type": "kokoro", "lang": "en-GB", "gender": "Male"},
]


class LocalTTSManager:
    """本地统一发音调度引擎"""

    def __init__(self, models_dir: Optional[str] = None):
        if not models_dir:
            from ..config import config
            models_dir = config.get("models_dir")
        self.models_dir = models_dir
        self.kokoro_dir = os.path.join(self.models_dir, "kokoro")
        self.kokoro_instance = None
        self._kokoro_lock = asyncio.Lock()

    def get_supported_voices(self) -> List[Dict[str, Any]]:
        return SUPPORTED_VOICES

    def is_kokoro_model_ready(self) -> Tuple[bool, str]:
        """检测离线 Kokoro ONNX 模型是否存在"""
        model_path = os.path.join(self.kokoro_dir, "kokoro-v1.0.fp16-gpu.onnx")
        voices_path = os.path.join(self.kokoro_dir, "voices-v1.0.bin")
        legacy_voices = os.path.join(self.kokoro_dir, "voices.bin")

        has_model = os.path.exists(model_path) and os.path.getsize(model_path) > 1000000
        has_voices = (os.path.exists(voices_path) and os.path.getsize(voices_path) > 1000) or \
                     (os.path.exists(legacy_voices) and os.path.getsize(legacy_voices) > 1000)

        if has_model and has_voices:
            return True, "离线模型已就绪"
        elif has_model:
            return False, "缺少音色特征库 voices-v1.0.bin"
        elif has_voices:
            return False, "缺少模型权重 kokoro-v1.0.fp16-gpu.onnx"
        else:
            return False, "尚未下载离线模型 (可随时在设置中一键下载)"

    async def _init_kokoro_if_needed(self) -> bool:
        """按需初始化 Kokoro"""
        if self.kokoro_instance:
            return True

        async with self._kokoro_lock:
            if self.kokoro_instance:
                return True

            try:
                from kokoro_onnx import Kokoro
            except ImportError:
                print("[TTS] kokoro-onnx 尚未安装，将自动降级至 Edge-TTS")
                return False

            ready, msg = self.is_kokoro_model_ready()
            if not ready:
                print(f"[TTS] Kokoro 未就绪: {msg}")
                return False

            model_path = os.path.join(self.kokoro_dir, "kokoro-v1.0.fp16-gpu.onnx")
            voices_path = os.path.join(self.kokoro_dir, "voices-v1.0.bin")
            if not os.path.exists(voices_path):
                voices_path = os.path.join(self.kokoro_dir, "voices.bin")

            loop = asyncio.get_running_loop()
            try:
                self.kokoro_instance = await loop.run_in_executor(
                    None, lambda: Kokoro(model_path, voices_path)
                )
                print("[TTS] Kokoro 本地离线引擎载入成功！")
                return True
            except Exception as e:
                print(f"[TTS] Kokoro 初始化异常: {e}")
                return False

    async def synthesize(
        self,
        text: str,
        voice_id: str = "en-US-JennyNeural",
        speed: float = 1.0,
        pitch: str = "+0Hz"
    ) -> Tuple[Optional[bytes], Optional[str]]:
        """
        统一合成方法
        返回: (audio_bytes, error_message)
        """
        text = text.strip()
        if not text:
            return None, "文本内容为空"

        voice_id_clean = voice_id.strip()
        is_kokoro = voice_id_clean.startswith("kokoro:")

        # 优先执行 Kokoro
        if is_kokoro:
            kokoro_ok = await self._init_kokoro_if_needed()
            if kokoro_ok and self.kokoro_instance:
                try:
                    clean_voice = voice_id_clean.replace("kokoro:", "").strip()
                    loop = asyncio.get_running_loop()

                    def _run_kokoro():
                        import soundfile as sf
                        samples, sample_rate = self.kokoro_instance.create(
                            text, voice=clean_voice, speed=speed, lang="en-us"
                        )
                        buffer = io.BytesIO()
                        sf.write(buffer, samples, sample_rate, format="WAV")
                        return buffer.getvalue()

                    audio_bytes = await loop.run_in_executor(None, _run_kokoro)
                    return audio_bytes, None
                except Exception as e:
                    print(f"[TTS] Kokoro 合成出错: {e}，正在降级使用 Edge-TTS 兜底...")
            else:
                print("[TTS] Kokoro 离线模型不可用，自动平滑降级至 Edge-TTS...")

        # Edge-TTS 生成 (或作为 Kokoro 的优雅降级)
        try:
            import edge_tts

            edge_voice = voice_id_clean
            if is_kokoro or not any(v["id"] == edge_voice for v in SUPPORTED_VOICES if v["type"] == "edge"):
                edge_voice = "en-US-JennyNeural"

            rate_str = f"+{int((speed - 1.0) * 100)}%" if speed >= 1.0 else f"-{int((1.0 - speed) * 100)}%"
            communicate = edge_tts.Communicate(text, edge_voice, rate=rate_str, pitch=pitch)

            audio_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]

            if audio_data:
                return audio_data, None
            else:
                return None, "Edge-TTS 未返回有效音频数据"
        except Exception as e:
            return None, f"语音合成失败: {str(e)}"

    def save_audio(self, audio_bytes: bytes, target_path: str) -> bool:
        """保存音频到本地指定路径"""
        try:
            os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
            with open(target_path, "wb") as f:
                f.write(audio_bytes)
            return True
        except Exception as e:
            print(f"[TTS] 保存音频文件失败: {e}")
            return False
