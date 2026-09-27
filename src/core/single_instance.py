# -*- coding: utf-8 -*-
"""
单实例运行管理器 (Single Instance Manager)
基于 QLocalServer / QLocalSocket 确保全系统仅运行一个 TBE-Client 进程。
若重复启动：
1. 新实例向已运行实例发送 WAKEUP 信号；
2. 已运行实例主窗口从最小化/托盘恢复并置顶前台；
3. 新实例退出。
"""

import sys
from PySide6.QtCore import QObject, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket


class SingleInstanceManager(QObject):
    message_received = Signal(str)

    SERVER_NAME = "TheBoringEnglish_Client_SingleInstance_Lock"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.server = None

    def is_another_instance_running(self) -> bool:
        """
        检查是否有其他客户端实例在运行。
        若有，向已有实例发送唤醒指令并返回 True；若无，创建监听服务并返回 False。
        """
        socket = QLocalSocket()
        socket.connectToServer(self.SERVER_NAME)
        # 尝试连接已有实例
        if socket.waitForConnected(800):
            try:
                socket.write(b"WAKEUP\n")
                socket.waitForBytesWritten(800)
                socket.flush()
                socket.waitForReadyRead(600)
                socket.disconnectFromServer()
            except Exception:
                pass
            return True

        # 连接失败，可能是首次启动，也可能是之前实例异常退出残留的套接字
        QLocalServer.removeServer(self.SERVER_NAME)

        self.server = QLocalServer(self)
        self.server.newConnection.connect(self._on_new_connection)
        if not self.server.listen(self.SERVER_NAME):
            # 尝试再次清理并重试
            QLocalServer.removeServer(self.SERVER_NAME)
            self.server.listen(self.SERVER_NAME)

        return False

    def _on_new_connection(self):
        if not self.server:
            return
        client_connection = self.server.nextPendingConnection()
        if not client_connection:
            return

        def handle_ready_read():
            try:
                data = client_connection.readAll().data().decode("utf-8", errors="ignore").strip()
                if data:
                    self.message_received.emit(data)
                client_connection.write(b"ACK\n")
                client_connection.flush()
            except Exception:
                pass
            finally:
                client_connection.disconnectFromServer()

        client_connection.readyRead.connect(handle_ready_read)
        if client_connection.bytesAvailable() > 0:
            handle_ready_read()

    def cleanup(self):
        """退出时释放资源"""
        if self.server:
            self.server.close()
            QLocalServer.removeServer(self.SERVER_NAME)
            self.server = None


def activate_window(window):
    """跨平台将窗口从隐藏/最小化状态唤醒至系统最前台"""
    if not window:
        return
    try:
        if window.isHidden() or not window.isVisible():
            window.show()
        if window.isMinimized():
            window.showNormal()
        window.raise_()
        window.activateWindow()

        # Windows 原生前台激活增强
        if sys.platform == "win32":
            try:
                import ctypes
                hwnd = int(window.winId())
                # SW_RESTORE = 9
                ctypes.windll.user32.ShowWindow(hwnd, 9)
                ctypes.windll.user32.SetForegroundWindow(hwnd)
            except Exception:
                pass
    except Exception as e:
        print(f"[SingleInstance] Activate window error: {e}")
