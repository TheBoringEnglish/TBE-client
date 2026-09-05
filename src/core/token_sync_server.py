# -*- coding: utf-8 -*-
"""
本地浏览器同步与交互服务 (TokenSyncServer)
监听本地 6502 端口：
1. /auth: 接收浏览器官网登录后的 Token 回调，免密同步绑定；
2. /launch-preview: 接收来自 theboringenglish.com 网页端点击「一键 Remotion 预览」或「生成视频」的请求，自动唤起本地 Remotion Studio 并归档至历史记录。
"""

import json
import time
import secrets
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
from PySide6.QtCore import QThread, Signal
from .remotion_bridge import RemotionBridge
from .video_history import VideoHistoryManager

# POST 请求体最大大小 (10 MB)
MAX_POST_BYTES = 10 * 1024 * 1024


class TokenSyncHandler(BaseHTTPRequestHandler):
    """处理来自浏览器的 Token 与网页端足迹拉起请求"""

    token_callback = None
    preview_callback = None
    # nonce 安全验证：只有带匹配 nonce 的请求才能被接受 (默认 60 秒有效期)
    _expected_nonce: str = ""
    _nonce_timestamp: float = 0

    def _send_cors_headers(self):
        origin = self.headers.get("Origin", "")
        allowed_origins = [
            "https://theboringenglish.com",
            "http://localhost:6501",
            "http://127.0.0.1:6501",
            "http://localhost:3000"
        ]
        allow_origin = origin if origin in allowed_origins else allowed_origins[0]
        self.send_header("Access-Control-Allow-Origin", allow_origin)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Private-Network", "true")

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        # 1. 登录 Token 同步
        if parsed.path == "/auth":
            query_params = urllib.parse.parse_qs(parsed.query)
            tokens = query_params.get("token")
            nonce_params = query_params.get("nonce")

            if tokens and tokens[0]:
                raw_token = tokens[0].strip()

                # nonce 安全验证：如果应用设置了 nonce，且未超过 60 秒有效期，必须匹配
                if TokenSyncHandler._expected_nonce:
                    if time.time() - TokenSyncHandler._nonce_timestamp > 60:
                        # 超过 60 秒过期，重置 nonce
                        TokenSyncHandler._expected_nonce = ""
                    else:
                        provided_nonce = nonce_params[0] if nonce_params else ""
                        if not secrets.compare_digest(provided_nonce, TokenSyncHandler._expected_nonce):
                            self.send_response(403)
                            self._send_cors_headers()
                            self.send_header("Content-Type", "application/json; charset=utf-8")
                            self.end_headers()
                            res = json.dumps({"status": "error", "message": "Invalid or expired nonce"}).encode("utf-8")
                            self.wfile.write(res)
                            return
                        # nonce 匹配后立即失效（一次性使用）
                        TokenSyncHandler._expected_nonce = ""

                if TokenSyncHandler.token_callback:
                    TokenSyncHandler.token_callback(raw_token)

                self.send_response(200)
                self._send_cors_headers()
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                res = json.dumps({"status": "ok", "message": "Token received by local desktop client"}).encode("utf-8")
                self.wfile.write(res)
                return

            # 缺少 token 参数
            self.send_response(400)
            self._send_cors_headers()
            self.end_headers()
            return

        # 2. 网页端足迹出片拉起服务 (GET 简易触发)
        elif parsed.path == "/launch-preview":
            query_params = urllib.parse.parse_qs(parsed.query)
            title = (query_params.get("title") or ["TBE 学习足迹"])[0]
            project_id = (query_params.get("project_id") or ["remotion_text1"])[0]
            port = int((query_params.get("port") or [3000])[0])

            # 自动归档并启动
            VideoHistoryManager.add_record(
                title=title,
                project_id=project_id,
                port=port,
                source="theboringenglish.com 网页端足迹"
            )

            bridge = RemotionBridge()
            bridge.launch_preview(project_id=project_id, port=port)

            if TokenSyncHandler.preview_callback:
                TokenSyncHandler.preview_callback(title)

            self.send_response(200)
            self._send_cors_headers()
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            res = json.dumps({"status": "ok", "message": f"Remotion preview launched for {title}"}).encode("utf-8")
            self.wfile.write(res)
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)

        # 3. 网页端 POST 完整足迹 payload 数据并拉起
        if parsed.path == "/launch-preview":
            content_length = int(self.headers.get("Content-Length", 0))

            # 安全限制：请求体不得超过 10MB
            if content_length > MAX_POST_BYTES:
                self.send_response(413)
                self._send_cors_headers()
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                res = json.dumps({"status": "error", "message": "Request body too large (max 10MB)"}).encode("utf-8")
                self.wfile.write(res)
                return

            post_body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
            try:
                data = json.loads(post_body)
            except Exception:
                data = {}

            title = data.get("title") or "TBE 学习足迹"
            project_id = data.get("project_id") or "remotion_text1"
            port = int(data.get("port") or 3000)
            segments = data.get("segments") or []

            # 归档出片历史
            VideoHistoryManager.add_record(
                title=title,
                project_id=project_id,
                port=port,
                sentence_count=len(segments),
                source="theboringenglish.com 网页端足迹"
            )

            # 拉起预览
            bridge = RemotionBridge()
            bridge.launch_preview(
                project_id=project_id,
                port=port,
                payload_data={"title": title, "segments": segments}
            )

            if TokenSyncHandler.preview_callback:
                TokenSyncHandler.preview_callback(title)

            self.send_response(200)
            self._send_cors_headers()
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            res = json.dumps({"status": "ok", "message": "Preview launched successfully"}).encode("utf-8")
            self.wfile.write(res)
            return

        self.send_response(404)
        self.end_headers()

    def log_message(self, format, *args):
        pass


class TokenSyncServerThread(QThread):
    """后台监听服务线程"""

    token_received_signal = Signal(str)
    preview_launched_signal = Signal(str)

    def __init__(self, port: int = 6502, parent=None):
        super().__init__(parent)
        self.port = port
        self.server: HTTPServer = None

    def run(self):
        TokenSyncHandler.token_callback = lambda tok: self.token_received_signal.emit(tok)
        TokenSyncHandler.preview_callback = lambda t: self.preview_launched_signal.emit(t)
        try:
            self.server = HTTPServer(("127.0.0.1", self.port), TokenSyncHandler)
            self.server.serve_forever()
        except Exception:
            pass

    def set_nonce(self, nonce: str):
        """设置一次性 nonce，下次 /auth 请求必须携带该值才被接受 (默认 60 秒有效期)"""
        TokenSyncHandler._expected_nonce = nonce
        TokenSyncHandler._nonce_timestamp = time.time() if nonce else 0

    def stop(self):
        if self.server:
            try:
                self.server.shutdown()
                self.server.server_close()
            except Exception:
                pass
