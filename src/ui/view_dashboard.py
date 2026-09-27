# -*- coding: utf-8 -*-
"""
TBE Client 学习看板视图 (DashboardView)
高质感双栏架构与本地优先 (Local-First) 极速秒开设计：
- 本地优先：启动 0 毫秒即从本地配置与持久化缓存中加载呈现个人登录态、打卡天数、维度进度与精选内容，零白屏等待；
- 异步双通道刷新：用户信息与学习计划极速优先获取，视听新闻流后台并发更新并自动落盘缓存；
- 原生异步网络图片池：基于 Qt 原生非阻塞 QNetworkAccessManager，零操作系统线程消耗，彻底根绝闪退与线程竞争；
- SSO 免密直达：点击任务、YouTube 视频或环球新闻，携带官方登录凭证直达网页端沉浸学习。
"""

import os
import json
import hashlib
import urllib.parse
import threading
import requests
from typing import Dict, Any, List, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QScrollArea, QProgressBar, QStackedWidget, QSizePolicy, QGridLayout
)
from PySide6.QtCore import Qt, Signal, QThread, QObject, QSize, QTimer, QUrl
from PySide6.QtGui import QPixmap, QCursor, QPainter, QPainterPath, QColor, QFont
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply

from ..config import config, get_asset_path
from ..core.auth_api import AuthAPI
from ..core.sso_helper import open_web_with_sso
from ..core.i18n import t


# ── 本地持久化缓存目录 ──
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".tbe_client_cache")
IMAGE_CACHE_DIR = os.path.join(CACHE_DIR, "images")
DASHBOARD_CACHE_FILE = os.path.join(CACHE_DIR, "dashboard_data.json")

os.makedirs(IMAGE_CACHE_DIR, exist_ok=True)


class DashboardCache:
    """看板数据本地持久化管理器"""

    @classmethod
    def load(cls) -> dict:
        if os.path.exists(DASHBOARD_CACHE_FILE):
            try:
                with open(DASHBOARD_CACHE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    @classmethod
    def save(cls, data: dict):
        try:
            with open(DASHBOARD_CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[DashboardCache] 缓存保存失败: {e}")


class NetworkImageLoader(QObject):
    """
    基于 Qt 原生异步非阻塞事件循环的图片加载池
    零系统线程占用，自带磁盘缓存，100% 避免 QThread 析构崩溃
    """
    _instance = None

    @classmethod
    def instance(cls):
        if cls._instance is None:
            cls._instance = NetworkImageLoader()
        return cls._instance

    def __init__(self):
        super().__init__()
        self.nam = QNetworkAccessManager(self)

    def load_image(self, url: str, callback):
        if not url or not url.startswith("http"):
            return

        # 检查本地磁盘缓存
        url_hash = hashlib.md5(url.encode("utf-8")).hexdigest()
        ext = ".jpg" if "jpg" in url.lower() else ".png"
        cache_path = os.path.join(IMAGE_CACHE_DIR, f"{url_hash}{ext}")

        if os.path.exists(cache_path) and os.path.getsize(cache_path) > 0:
            pix = QPixmap(cache_path)
            if not pix.isNull():
                callback(pix)
                return

        # 发起异步非阻塞网络请求
        req = QNetworkRequest(QUrl(url))
        req.setHeader(QNetworkRequest.UserAgentHeader, "TBE-Desktop-Client/1.0")
        reply = self.nam.get(req)

        def _on_reply_finished():
            try:
                if reply.error() == QNetworkReply.NoError:
                    raw_data = reply.readAll().data()
                    pix = QPixmap()
                    if pix.loadFromData(raw_data):
                        try:
                            with open(cache_path, "wb") as f:
                                f.write(raw_data)
                        except Exception:
                            pass
                        callback(pix)
            except Exception:
                pass
            finally:
                reply.deleteLater()

        reply.finished.connect(_on_reply_finished)


class DashboardDataWorker(QObject):
    """
    双通道后台数据刷新任务：
    - 通道 1: 优先获取个人信息、学习计划与打卡天数 (快速返回，更新右栏)
    - 通道 2: 获取 YouTube 推荐与 RSS 环球新闻 (更新左栏并写入持久化缓存)
    基于 QObject 信号 + Python daemon 守护线程，彻底杜绝 QThread 提前析构崩溃与 C++ 对象已删除异常
    """
    user_plan_signal = Signal(dict)
    feeds_signal = Signal(dict)
    finished_signal = Signal()

    def __init__(self, force_refresh: bool = False, parent=None):
        super().__init__(parent)
        self.force_refresh = force_refresh

    def run(self):
        try:
            server_url = config.get("server_url", "https://theboringenglish.com").rstrip("/")
            token = config.get("token", "").strip()
            headers = {"User-Agent": "TBE-Desktop-Client/1.0"}
            if token:
                headers["Authorization"] = f"Bearer {token}"

            # ── 阶段 1: 优先同步个人用户资料、学习计划与打卡统计 (0.5s 极速响应) ──
            user_data = {
                "user": None,
                "plan": {},
                "progress": {},
                "stats": {}
            }

            if token:
                try:
                    me_resp = requests.get(f"{server_url}/api/v1/auth/me", timeout=3.5, headers=headers)
                    if me_resp.status_code == 200:
                        u = me_resp.json().get("user")
                        if u:
                            user_data["user"] = {
                                "id": u.get("id", 0),
                                "username": u.get("username", ""),
                                "avatar": u.get("avatar_url", ""),
                                "is_vip": bool(u.get("is_vip", False) or u.get("is_max", False)),
                                "is_super_admin": bool(u.get("is_super_admin", False)),
                                "plan_id": u.get("plan_id")
                            }
                            config.set("user_info", user_data["user"])
                except Exception as e:
                    print(f"[DashboardWorker] 获取用户资料延迟: {e}")

                try:
                    plan_resp = requests.get(f"{server_url}/api/v1/learning-plan/progress", timeout=3.5, headers=headers)
                    if plan_resp.status_code == 200:
                        p_data = plan_resp.json()
                        user_data["plan"] = p_data.get("plan", {})
                        user_data["progress"] = p_data.get("progress", {})
                except Exception as e:
                    print(f"[DashboardWorker] 获取学习计划异常: {e}")

                try:
                    stats_resp = requests.get(f"{server_url}/api/v1/history/stats", timeout=3.5, headers=headers)
                    if stats_resp.status_code == 200:
                        user_data["stats"] = stats_resp.json()
                except Exception as e:
                    print(f"[DashboardWorker] 获取学习统计异常: {e}")

                # 立即发送个人数据信号，使右侧界面秒级刷新！
                self.user_plan_signal.emit(user_data)

            # ── 阶段 2: 获取视听推荐与环球新闻 ──
            feeds_data = {
                "channels": [],
                "news": []
            }

            # 2.1 YouTube 频道与视频精选
            try:
                resp = requests.get(f"{server_url}/api/v1/voicetube/channels", timeout=4.0, headers=headers)
                if resp.status_code == 200:
                    d = resp.json()
                    if d.get("success") and d.get("channels"):
                        feeds_data["channels"] = d["channels"]
            except Exception:
                pass

            if not feeds_data["channels"]:
                try:
                    resp = requests.get(f"{server_url}/voicetube_channels.json", timeout=3.0, headers=headers)
                    if resp.status_code == 200:
                        feeds_data["channels"] = resp.json().get("channels", [])
                except Exception:
                    pass

            # 2.2 环球英文新闻 RSS
            default_sources = [
                {"name": "BBC World", "url": "https://feeds.bbci.co.uk/news/world/rss.xml"},
                {"name": "The Guardian", "url": "https://www.theguardian.com/world/rss"},
                {"name": "Wired Tech", "url": "https://www.wired.com/feed/rss"},
                {"name": "TED Blog", "url": "https://blog.ted.com/feed/"}
            ]
            news_items = []
            for src in default_sources:
                try:
                    resp = requests.post(
                        f"{server_url}/api/v1/article/rss/list",
                        json={"url": src["url"], "target_lang": "zh-CN"},
                        timeout=3.5,
                        headers=headers
                    )
                    if resp.status_code == 200:
                        items = resp.json().get("items", [])
                        for it in items[:3]:
                            it["source_name"] = src["name"]
                            news_items.append(it)
                except Exception:
                    continue

            feeds_data["news"] = news_items

            self.feeds_signal.emit(feeds_data)

            # 持久化整合保存
            all_cache = DashboardCache.load()
            if user_data.get("user"):
                all_cache["user"] = user_data["user"]
            if user_data.get("plan"):
                all_cache["plan"] = user_data["plan"]
            if user_data.get("progress"):
                all_cache["progress"] = user_data["progress"]
            if user_data.get("stats"):
                all_cache["stats"] = user_data["stats"]
            if feeds_data.get("channels"):
                all_cache["channels"] = feeds_data["channels"]
            if feeds_data.get("news"):
                all_cache["news"] = feeds_data["news"]
            DashboardCache.save(all_cache)
        except Exception as e:
            print(f"[DashboardWorker] 刷新异常: {e}")
        finally:
            self.finished_signal.emit()


class VideoCardWidget(QFrame):
    """单个精选 YouTube 视频卡片"""

    def __init__(self, video: dict, parent=None):
        super().__init__(parent)
        self.video = video
        self.setProperty("class", "card")
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(88)
        self._init_ui()

    def _init_ui(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 8, 12, 8)
        lay.setSpacing(12)

        self.lbl_thumb = QLabel()
        self.lbl_thumb.setFixedSize(106, 60)
        self.lbl_thumb.setStyleSheet(
            "background-color: rgba(255, 255, 255, 0.05); border-radius: 6px; color: #64748B;"
        )
        self.lbl_thumb.setAlignment(Qt.AlignCenter)
        self.lbl_thumb.setText("🎬")
        lay.addWidget(self.lbl_thumb)

        info_lay = QVBoxLayout()
        info_lay.setContentsMargins(0, 2, 0, 2)
        info_lay.setSpacing(4)

        title_text = self.video.get("title", "YouTube 英语视频")
        self.lbl_title = QLabel(title_text)
        self.lbl_title.setStyleSheet("font-size: 13px; font-weight: 600; line-height: 1.3;")
        self.lbl_title.setWordWrap(False)
        info_lay.addWidget(self.lbl_title)

        meta_row = QHBoxLayout()
        meta_row.setSpacing(8)

        ch_name = self.video.get("channel_title") or self.video.get("channelName") or "YouTube"
        self.lbl_ch = QLabel(f"📺 {ch_name}")
        self.lbl_ch.setStyleSheet("font-size: 11.5px; color: #94A3B8;")
        meta_row.addWidget(self.lbl_ch)

        duration = self.video.get("duration")
        if duration:
            self.lbl_dur = QLabel(f"⏱️ {duration}")
            self.lbl_dur.setStyleSheet("font-size: 11px; color: #64748B;")
            meta_row.addWidget(self.lbl_dur)

        meta_row.addStretch()

        lbl_jump = QLabel(t("dash_click_to_study", "精读 ↗"))
        lbl_jump.setStyleSheet("font-size: 11px; font-weight: 600; color: #EA580C;")
        meta_row.addWidget(lbl_jump)

        info_lay.addLayout(meta_row)
        lay.addLayout(info_lay)

        # 基于 QNetworkAccessManager 异步加载图片，不消耗系统线程
        thumb_url = self.video.get("thumbnail") or f"https://i.ytimg.com/vi/{self.video.get('youtube_id')}/mqdefault.jpg"
        if thumb_url:
            NetworkImageLoader.instance().load_image(thumb_url, self._set_thumbnail)

    def _set_thumbnail(self, pix: QPixmap):
        try:
            if not pix.isNull():
                scaled_pix = pix.scaled(106, 60, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                rounded = QPixmap(106, 60)
                rounded.fill(Qt.transparent)
                painter = QPainter(rounded)
                painter.setRenderHint(QPainter.Antialiasing)
                path_draw = QPainterPath()
                path_draw.addRoundedRect(0, 0, 106, 60, 6, 6)
                painter.setClipPath(path_draw)
                painter.drawPixmap(0, 0, scaled_pix)
                painter.end()
                self.lbl_thumb.setPixmap(rounded)
                self.lbl_thumb.setText("")
        except (RuntimeError, Exception):
            pass

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            vid = self.video.get("youtube_id") or self.video.get("id")
            if vid:
                open_web_with_sso(f"/video-study/{vid}")
        super().mousePressEvent(event)


class NewsCardWidget(QFrame):
    """单个环球英文新闻卡片"""

    def __init__(self, item: dict, parent=None):
        super().__init__(parent)
        self.item = item
        self.setProperty("class", "card")
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(94)
        self._init_ui()

    def _init_ui(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(12)

        self.lbl_thumb = QLabel()
        self.lbl_thumb.setFixedSize(80, 66)
        self.lbl_thumb.setStyleSheet(
            "background-color: rgba(255, 255, 255, 0.05); border-radius: 6px; color: #64748B;"
        )
        self.lbl_thumb.setAlignment(Qt.AlignCenter)
        self.lbl_thumb.setText("📰")
        lay.addWidget(self.lbl_thumb)

        info_lay = QVBoxLayout()
        info_lay.setContentsMargins(0, 0, 0, 0)
        info_lay.setSpacing(4)

        title = self.item.get("title", "News Article")
        self.lbl_title = QLabel(title)
        self.lbl_title.setStyleSheet("font-size: 13px; font-weight: 600; line-height: 1.3;")
        self.lbl_title.setWordWrap(True)
        info_lay.addWidget(self.lbl_title)

        meta_lay = QHBoxLayout()
        meta_lay.setSpacing(8)

        source = self.item.get("source_name") or "News"
        self.lbl_src = QLabel(source)
        self.lbl_src.setStyleSheet(
            "font-size: 11px; font-weight: 600; background: rgba(56, 189, 248, 0.12); color: #0284C7; border-radius: 4px; padding: 2px 6px;"
        )
        meta_lay.addWidget(self.lbl_src)

        pub_date = self.item.get("pubDate") or ""
        if pub_date:
            short_date = pub_date[:16] if len(pub_date) > 16 else pub_date
            self.lbl_date = QLabel(short_date)
            self.lbl_date.setStyleSheet("font-size: 11px; color: #64748B;")
            meta_lay.addWidget(self.lbl_date)

        meta_lay.addStretch()

        lbl_import = QLabel(t("dash_import_study", "精读 ↗"))
        lbl_import.setStyleSheet("font-size: 11px; font-weight: 600; color: #EA580C;")
        meta_lay.addWidget(lbl_import)

        info_lay.addLayout(meta_lay)
        lay.addLayout(info_lay)

        img_url = self.item.get("image") or self.item.get("enclosure", {}).get("url")
        if img_url:
            NetworkImageLoader.instance().load_image(img_url, self._set_thumbnail)

    def _set_thumbnail(self, pix: QPixmap):
        try:
            if not pix.isNull():
                scaled_pix = pix.scaled(80, 66, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                rounded = QPixmap(80, 66)
                rounded.fill(Qt.transparent)
                painter = QPainter(rounded)
                painter.setRenderHint(QPainter.Antialiasing)
                path_draw = QPainterPath()
                path_draw.addRoundedRect(0, 0, 80, 66, 6, 6)
                painter.setClipPath(path_draw)
                painter.drawPixmap(0, 0, scaled_pix)
                painter.end()
                self.lbl_thumb.setPixmap(rounded)
                self.lbl_thumb.setText("")
        except (RuntimeError, Exception):
            pass

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            link = self.item.get("link")
            if link:
                encoded = urllib.parse.quote(link)
                open_web_with_sso(f"/articles?quick_import={encoded}")
        super().mousePressEvent(event)


class PlanDimensionRow(QFrame):
    """单个每日学习计划指标条目"""

    def __init__(self, dim_id: str, icon: str, name: str, route: str, current: int, target: int, parent=None):
        super().__init__(parent)
        self.dim_id = dim_id
        self.route = route
        self.current = current
        self.target = target

        self.setProperty("class", "card")
        self.setFixedHeight(54)
        self._init_ui(icon, name)

    def _init_ui(self, icon: str, name: str):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(12, 6, 12, 6)
        lay.setSpacing(10)

        lbl_icon = QLabel(icon)
        lbl_icon.setStyleSheet("font-size: 16px;")
        lay.addWidget(lbl_icon)

        mid_lay = QVBoxLayout()
        mid_lay.setContentsMargins(0, 2, 0, 2)
        mid_lay.setSpacing(3)

        title_row = QHBoxLayout()
        title_row.setSpacing(6)
        lbl_name = QLabel(name)
        lbl_name.setStyleSheet("font-size: 12.5px; font-weight: 600;")
        title_row.addWidget(lbl_name)
        title_row.addStretch()

        is_finished = self.current >= self.target and self.target > 0
        progress_str = f"{self.current} / {self.target}" if self.target > 0 else f"{self.current}"
        lbl_count = QLabel("✓ 已完成" if is_finished else progress_str)
        lbl_count.setStyleSheet(
            "font-size: 11.5px; font-weight: 700; color: #10B981;" if is_finished else "font-size: 11.5px; color: #94A3B8;"
        )
        title_row.addWidget(lbl_count)
        mid_lay.addLayout(title_row)

        self.pbar = QProgressBar()
        self.pbar.setFixedHeight(5)
        self.pbar.setTextVisible(False)
        pct = min(100, int((self.current / self.target) * 100)) if self.target > 0 else 0
        self.pbar.setValue(pct)
        mid_lay.addWidget(self.pbar)

        lay.addLayout(mid_lay)

        btn_go = QPushButton(t("btn_start_study", "开始"))
        btn_go.setFixedSize(54, 26)
        btn_go.setProperty("class", "btnPrimary" if not is_finished else "btnSecondary")
        btn_go.setCursor(Qt.PointingHandCursor)
        btn_go.setStyleSheet("font-size: 11.5px; padding: 2px 6px; border-radius: 6px;")
        btn_go.clicked.connect(self._on_go_clicked)
        lay.addWidget(btn_go)

    def _on_go_clicked(self):
        open_web_with_sso(self.route)


class DashboardView(QWidget):
    """
    全新现代化大屏双栏看板视图
    - 左侧: 视频/新闻推荐与精选视听
    - 右侧: 个人资料、打卡天数与每日计划指标
    """

    navigate_signal = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.all_channels = []
        self.all_news = []
        self.current_cat = "all"
        self._is_refreshing = False
        self._worker: Optional[DashboardDataWorker] = None

        self._init_ui()
        # 1. 本地优先：0 毫秒即刻加载呈现本地已有账号与缓存数据
        self._apply_local_cached_data()
        # 2. 异步后台网络刷新
        self.refresh_data(force=False)

    def _init_ui(self):
        root_lay = QHBoxLayout(self)
        root_lay.setContentsMargins(18, 16, 18, 16)
        root_lay.setSpacing(16)

        # ── 左侧：视听推荐与环球新闻 (宽栏，约 60%) ──
        left_box = QFrame()
        left_lay = QVBoxLayout(left_box)
        left_lay.setContentsMargins(0, 0, 0, 0)
        left_lay.setSpacing(12)

        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)

        self.feed_pill_box = QFrame()
        self.feed_pill_box.setObjectName("subPillContainer")
        fp_lay = QHBoxLayout(self.feed_pill_box)
        fp_lay.setContentsMargins(2, 2, 2, 2)
        fp_lay.setSpacing(2)

        self.btn_tab_yt = QPushButton(t("dash_tab_youtube", "精选"))
        self.btn_tab_yt.setProperty("class", "subTabPill")
        self.btn_tab_yt.setCheckable(True)
        self.btn_tab_yt.setChecked(True)
        self.btn_tab_yt.setCursor(Qt.PointingHandCursor)
        self.btn_tab_yt.clicked.connect(lambda: self._switch_feed_tab("yt"))
        fp_lay.addWidget(self.btn_tab_yt)

        self.btn_tab_news = QPushButton(t("dash_tab_news", "新闻"))
        self.btn_tab_news.setProperty("class", "subTabPill")
        self.btn_tab_news.setCheckable(True)
        self.btn_tab_news.setCursor(Qt.PointingHandCursor)
        self.btn_tab_news.clicked.connect(lambda: self._switch_feed_tab("news"))
        fp_lay.addWidget(self.btn_tab_news)

        top_bar.addWidget(self.feed_pill_box)
        top_bar.addStretch()

        self.btn_shuffle = QPushButton(t("dash_btn_shuffle", "刷新"))
        self.btn_shuffle.setProperty("class", "toolPillBtn")
        self.btn_shuffle.setCursor(Qt.PointingHandCursor)
        self.btn_shuffle.clicked.connect(self._shuffle_current_feed)
        top_bar.addWidget(self.btn_shuffle)

        left_lay.addLayout(top_bar)

        # 分类筛选芯片栏
        self.cat_chips_frame = QFrame()
        chips_lay = QHBoxLayout(self.cat_chips_frame)
        chips_lay.setContentsMargins(0, 0, 0, 0)
        chips_lay.setSpacing(6)

        categories = [
            ("all", t("cat_all", "全部")),
            ("Speeches", t("cat_speeches", "TED 演说")),
            ("Podcasts", t("cat_podcasts", "播客 Talks")),
            ("News", t("cat_news", "全球新闻")),
            ("Movies", t("cat_movies", "影视原声")),
            ("Music", t("cat_music", "音乐歌曲")),
            ("Kids", t("cat_kids", "儿童卡通")),
        ]
        self.cat_buttons = {}
        for cat_id, cat_label in categories:
            b = QPushButton(cat_label)
            b.setProperty("class", "toolPillBtn")
            b.setCheckable(True)
            b.setCursor(Qt.PointingHandCursor)
            if cat_id == "all":
                b.setChecked(True)
            b.clicked.connect(lambda chk, cid=cat_id: self._on_cat_selected(cid))
            chips_lay.addWidget(b)
            self.cat_buttons[cat_id] = b

        chips_lay.addStretch()
        left_lay.addWidget(self.cat_chips_frame)

        self.feed_stack = QStackedWidget()

        # YouTube 列表容器
        self.scroll_yt = QScrollArea()
        self.scroll_yt.setWidgetResizable(True)
        self.scroll_yt.setFrameShape(QFrame.NoFrame)
        self.yt_container = QWidget()
        self.yt_list_lay = QVBoxLayout(self.yt_container)
        self.yt_list_lay.setContentsMargins(0, 2, 4, 2)
        self.yt_list_lay.setSpacing(8)
        self.scroll_yt.setWidget(self.yt_container)
        self.feed_stack.addWidget(self.scroll_yt)

        # 新闻列表容器
        self.scroll_news = QScrollArea()
        self.scroll_news.setWidgetResizable(True)
        self.scroll_news.setFrameShape(QFrame.NoFrame)
        self.news_container = QWidget()
        self.news_list_lay = QVBoxLayout(self.news_container)
        self.news_list_lay.setContentsMargins(0, 2, 4, 2)
        self.news_list_lay.setSpacing(8)
        self.scroll_news.setWidget(self.news_container)
        self.feed_stack.addWidget(self.scroll_news)

        left_lay.addWidget(self.feed_stack)
        root_lay.addWidget(left_box, 60)

        # ── 右侧：个人打卡与学习计划 (窄栏，约 40%) ──
        right_box = QFrame()
        right_lay = QVBoxLayout(right_box)
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_lay.setSpacing(12)

        # 1. 顶部用户状态卡片
        self.user_card = QFrame()
        self.user_card.setProperty("class", "card")
        uc_lay = QVBoxLayout(self.user_card)
        uc_lay.setContentsMargins(16, 14, 16, 14)
        uc_lay.setSpacing(10)

        u_top = QHBoxLayout()
        u_top.setSpacing(10)

        self.lbl_avatar = QLabel("👤")
        self.lbl_avatar.setFixedSize(38, 38)
        self.lbl_avatar.setStyleSheet(
            "background: rgba(255, 255, 255, 0.08); border-radius: 19px; font-size: 18px;"
        )
        self.lbl_avatar.setAlignment(Qt.AlignCenter)
        u_top.addWidget(self.lbl_avatar)

        u_meta = QVBoxLayout()
        u_meta.setSpacing(2)
        self.lbl_username = QLabel(t("dash_guest_user", "未登录访客"))
        self.lbl_username.setStyleSheet("font-size: 14px; font-weight: 700;")
        u_meta.addWidget(self.lbl_username)

        self.lbl_vip_badge = QLabel(t("dash_guest_tip", "关联账号同步学习轨迹"))
        self.lbl_vip_badge.setStyleSheet("font-size: 11.5px; color: #94A3B8;")
        u_meta.addWidget(self.lbl_vip_badge)
        u_top.addLayout(u_meta)
        u_top.addStretch()

        self.btn_login_link = QPushButton(t("dash_btn_login", "登录"))
        self.btn_login_link.setProperty("class", "btnPrimary")
        self.btn_login_link.setCursor(Qt.PointingHandCursor)
        self.btn_login_link.clicked.connect(self._open_login_or_profile)
        u_top.addWidget(self.btn_login_link)
        uc_lay.addLayout(u_top)

        # 连续打卡统计条
        self.streak_frame = QFrame()
        self.streak_frame.setStyleSheet(
            "background: rgba(249, 115, 22, 0.08); border-radius: 8px; padding: 6px 12px;"
        )
        sf_lay = QHBoxLayout(self.streak_frame)
        sf_lay.setContentsMargins(6, 4, 6, 4)
        sf_lay.setSpacing(8)

        self.lbl_streak = QLabel("🔥 连续学习: 0 天")
        self.lbl_streak.setStyleSheet("font-size: 12.5px; font-weight: 700; color: #EA580C;")
        sf_lay.addWidget(self.lbl_streak)
        sf_lay.addStretch()

        self.btn_refresh = QPushButton("🔄")
        self.btn_refresh.setToolTip(t("dash_refresh_tooltip", "刷新数据"))
        self.btn_refresh.setProperty("class", "toolCircleBtn")
        self.btn_refresh.setCursor(Qt.PointingHandCursor)
        self.btn_refresh.clicked.connect(lambda: self.refresh_data(force=True))
        sf_lay.addWidget(self.btn_refresh)

        uc_lay.addWidget(self.streak_frame)
        right_lay.addWidget(self.user_card)

        # 2. 今日学习计划维度卡片容器
        self.scroll_plan = QScrollArea()
        self.scroll_plan.setWidgetResizable(True)
        self.scroll_plan.setFrameShape(QFrame.NoFrame)
        self.plan_container = QWidget()
        self.plan_list_lay = QVBoxLayout(self.plan_container)
        self.plan_list_lay.setContentsMargins(0, 0, 0, 0)
        self.plan_list_lay.setSpacing(8)
        self.scroll_plan.setWidget(self.plan_container)
        right_lay.addWidget(self.scroll_plan)

        # 3. 底部官网直达卡片
        bottom_card = QFrame()
        bottom_card.setProperty("class", "card")
        bc_lay = QHBoxLayout(bottom_card)
        bc_lay.setContentsMargins(14, 10, 14, 10)
        bc_lay.setSpacing(10)

        lbl_tbe_icon = QLabel("⚡")
        lbl_tbe_icon.setStyleSheet("font-size: 16px;")
        bc_lay.addWidget(lbl_tbe_icon)

        lbl_tbe_desc = QLabel("TheBoringEnglish 官方平台")
        lbl_tbe_desc.setStyleSheet("font-size: 12px; font-weight: 600;")
        bc_lay.addWidget(lbl_tbe_desc)
        bc_lay.addStretch()

        btn_open_portal = QPushButton(t("dash_open_portal", "官网"))
        btn_open_portal.setProperty("class", "btnSecondary")
        btn_open_portal.setCursor(Qt.PointingHandCursor)
        btn_open_portal.setStyleSheet("font-size: 11.5px; padding: 4px 10px; border-radius: 6px;")
        btn_open_portal.clicked.connect(lambda: open_web_with_sso("/"))
        bc_lay.addWidget(btn_open_portal)

        right_lay.addWidget(bottom_card)
        root_lay.addWidget(right_box, 40)

    # ── 本地优先加载与即时呈现 ──
    def _apply_local_cached_data(self):
        """0毫秒立即从本地配置文件与持久化缓存恢复界面，绝不出现假未登录状态"""
        cached = DashboardCache.load()
        token = config.get("token", "").strip()
        local_user = config.get("user_info") or cached.get("user")

        self._update_user_ui(local_user, token)

        cached_stats = cached.get("stats", {})
        cached_plan = cached.get("plan", {})
        self._update_plan_ui(cached_plan, cached.get("progress", {}), cached_stats)

        # 恢复视听与新闻
        self.all_channels = cached.get("videos", [])
        self.all_news = cached.get("news", [])
        if self.all_channels:
            self._render_videos()
        if self.all_news:
            self._render_news()

    def _update_user_ui(self, user_info: Optional[dict], token: str):
        if token and user_info and user_info.get("username"):
            username = user_info.get("username", "Learner")
            self.lbl_username.setText(username)
            is_vip = user_info.get("is_vip", False)
            self.lbl_vip_badge.setText("💎 Pro 会员" if is_vip else "🌱 学习达人")
            self.lbl_vip_badge.setStyleSheet(
                "font-size: 11.5px; font-weight: 600; color: #F59E0B;" if is_vip else "font-size: 11.5px; color: #10B981;"
            )
            self.btn_login_link.setText(t("dash_btn_my_center", "主页"))

            avatar_url = user_info.get("avatar")
            if avatar_url:
                NetworkImageLoader.instance().load_image(avatar_url, self._set_avatar)
        else:
            self.lbl_username.setText(t("dash_guest_user", "未登录访客"))
            self.lbl_vip_badge.setText(t("dash_guest_tip", "关联账号同步学习轨迹"))
            self.lbl_vip_badge.setStyleSheet("font-size: 11.5px; color: #94A3B8;")
            self.btn_login_link.setText(t("dash_btn_login", "登录"))

    def _update_plan_ui(self, plan: dict, progress: dict, stats: dict):
        total_days = stats.get("total_days", 0)
        self.lbl_streak.setText(f"🔥 累计学习: {total_days} 天" if total_days > 0 else "🔥 开启今日打卡挑战！")

        while self.plan_list_lay.count():
            item = self.plan_list_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        dimensions = [
            ("scene",    "💬", t("nav_scene", "情景对话"), "/scene",       progress.get("scene", 0),    plan.get("scene", 1)),
            ("article",  "📖", t("nav_article", "双语精读"), "/articles",    progress.get("article", 0),  plan.get("article", 1)),
            ("podcast",  "🎧", t("nav_podcast", "原声播客"), "/podcast",     progress.get("podcast", 0),  plan.get("podcast", 1)),
            ("vocab",    "🔤", t("nav_vocab", "词汇打卡"), "/vocab-study", progress.get("vocab", 0),    plan.get("vocab", 20)),
            ("grammar",  "✏️", t("nav_grammar", "核心语法"), "/grammar/tutor", progress.get("grammar", 0), plan.get("grammar", 1)),
            ("speaking", "🎤", t("nav_speaking", "口语对话"), "/speaking",    progress.get("speaking", 0), plan.get("speaking", 1)),
        ]

        for dim_id, icon, name, route, cur, target in dimensions:
            row = PlanDimensionRow(dim_id, icon, name, route, cur, target, self)
            self.plan_list_lay.addWidget(row)

        self.plan_list_lay.addStretch()

    # ── 交互事件 ──
    def _switch_feed_tab(self, tab: str):
        if tab == "yt":
            self.btn_tab_yt.setChecked(True)
            self.btn_tab_news.setChecked(False)
            self.cat_chips_frame.show()
            self.feed_stack.setCurrentIndex(0)
        else:
            self.btn_tab_yt.setChecked(False)
            self.btn_tab_news.setChecked(True)
            self.cat_chips_frame.hide()
            self.feed_stack.setCurrentIndex(1)

    def _on_cat_selected(self, cat_id: str):
        self.current_cat = cat_id
        for cid, b in self.cat_buttons.items():
            b.setChecked(cid == cat_id)
        self._render_videos()

    def _shuffle_current_feed(self):
        import random
        if self.feed_stack.currentIndex() == 0:
            random.shuffle(self.all_channels)
            self._render_videos()
        else:
            random.shuffle(self.all_news)
            self._render_news()

    def _open_login_or_profile(self):
        token = config.get("token")
        if not token:
            self.navigate_signal.emit("settings")
        else:
            open_web_with_sso("/settings")

    # ── 异步网络数据拉取 ──
    def refresh_data(self, force: bool = False):
        self._apply_local_cached_data()

        # 检查是否已有 worker 正在运行，若有则忽略本次重复触发
        if self._is_refreshing:
            return

        self._is_refreshing = True
        try:
            self.btn_refresh.setEnabled(False)
        except (RuntimeError, Exception):
            pass

        self._worker = DashboardDataWorker(force_refresh=force, parent=self)
        self._worker.user_plan_signal.connect(self._on_user_plan_loaded)
        self._worker.feeds_signal.connect(self._on_feeds_loaded)
        self._worker.finished_signal.connect(self._on_refresh_finished)

        # 启动 Python 原生守护线程，生命周期全权交由 Python 管理，彻底杜绝 QThread 提前析构与闪退
        worker_thread = threading.Thread(
            target=self._worker.run,
            name="DashboardDataWorkerThread",
            daemon=True
        )
        worker_thread.start()

    def _on_refresh_finished(self):
        self._is_refreshing = False
        try:
            self.btn_refresh.setEnabled(True)
        except (RuntimeError, Exception):
            pass

    def _on_user_plan_loaded(self, user_data: dict):
        try:
            token = config.get("token", "").strip()
            user_info = user_data.get("user") or config.get("user_info")
            self._update_user_ui(user_info, token)

            plan = user_data.get("plan", {})
            progress = user_data.get("progress", {})
            stats = user_data.get("stats", {})
            self._update_plan_ui(plan, progress, stats)
        except (RuntimeError, Exception):
            pass

    def _on_feeds_loaded(self, feeds_data: dict):
        try:
            channels = feeds_data.get("channels", [])
            news = feeds_data.get("news", [])

            if channels:
                self.all_channels = channels
                self._render_videos()

            if news:
                self.all_news = news
                self._render_news()
        except (RuntimeError, Exception):
            pass

    def _render_videos(self):
        while self.yt_list_lay.count():
            item = self.yt_list_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        matched_videos = []
        for ch in self.all_channels:
            ch_name = (ch.get("display_name") or ch.get("name") or "").lower()
            if self.current_cat != "all":
                target_key = self.current_cat.lower()
                if target_key not in ch_name:
                    continue
            for v in ch.get("videos", []):
                v["channelName"] = ch.get("display_name") or ch.get("name")
                matched_videos.append(v)

        import random
        shuffled = list(matched_videos)
        random.shuffle(shuffled)
        display_videos = shuffled[:12]

        if not display_videos:
            lbl_empty = QLabel(t("dash_no_videos", "暂无推荐视频，请稍后刷新"))
            lbl_empty.setStyleSheet("color: #64748B; font-size: 13px; padding: 20px;")
            lbl_empty.setAlignment(Qt.AlignCenter)
            self.yt_list_lay.addWidget(lbl_empty)
        else:
            for v in display_videos:
                card = VideoCardWidget(v, self)
                self.yt_list_lay.addWidget(card)

        self.yt_list_lay.addStretch()

    def _render_news(self):
        while self.news_list_lay.count():
            item = self.news_list_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not self.all_news:
            lbl_empty = QLabel(t("dash_no_news", "暂无环球新闻资讯，请稍后刷新"))
            lbl_empty.setStyleSheet("color: #64748B; font-size: 13px; padding: 20px;")
            lbl_empty.setAlignment(Qt.AlignCenter)
            self.news_list_lay.addWidget(lbl_empty)
        else:
            for item in self.all_news[:12]:
                card = NewsCardWidget(item, self)
                self.news_list_lay.addWidget(card)

        self.news_list_lay.addStretch()

    def _set_avatar(self, pix: QPixmap):
        try:
            if not pix.isNull():
                scaled_pix = pix.scaled(38, 38, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
                rounded = QPixmap(38, 38)
                rounded.fill(Qt.transparent)
                painter = QPainter(rounded)
                painter.setRenderHint(QPainter.Antialiasing)
                path_draw = QPainterPath()
                path_draw.addEllipse(0, 0, 38, 38)
                painter.setClipPath(path_draw)
                painter.drawPixmap(0, 0, scaled_pix)
                painter.end()
                self.lbl_avatar.setPixmap(rounded)
                self.lbl_avatar.setText("")
        except (RuntimeError, Exception):
            pass

    def closeEvent(self, event):
        self._is_refreshing = False
        super().closeEvent(event)
