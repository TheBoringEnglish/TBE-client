# -*- coding: utf-8 -*-
"""
TBE Client 全局国际化多语言支持引擎 (i18n)
支持动态切换简体中文 (zh_CN) 与英文 (en_US)
"""

from typing import Dict
from ..config import config

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "zh_CN": {
        # 通用
        "app_title": "TheBoringEnglish 桌面客户端",
        "app_subtitle": "本地高质量发音引擎 · 学习足迹出片 · 生态互联",
        "save": "保存",
        "cancel": "取消",
        "confirm": "确认",
        "loading": "加载中...",
        "browse": "浏览...",
        "ready": "就绪",
        "online": "在线",
        "offline": "离线",
        "success": "成功",
        "failed": "失败",
        "yes": "是",
        "no": "否",
        
        # 侧边栏导航
        "nav_dashboard": "🏠  概览与推荐",
        "nav_engine": "⚡  本地发音引擎",
        "nav_footprints": "👣  足迹与出片",
        "nav_settings": "⚙️  设置与管理",
        "client_brand": "TBE Client",
        "client_sub": "桌面生态客户端",
        "public_release": "v1.0.0 正式版",

        # 仪表盘
        "dash_welcome": "欢迎使用 TheBoringEnglish 本地客户端",
        "dash_sub": "本地 AI 神经发音 · 学习足迹一键视频预览 · 极速沉浸式学英语",
        "status_cloud_ok": "云端已关联",
        "status_cloud_guest": "游客/离线模式",
        "card_engine_title": "本地发音引擎",
        "card_engine_val": "就绪",
        "card_engine_sub": "Edge-TTS + 离线 Kokoro",
        "card_remotion_title": "Remotion 视频",
        "card_remotion_val": "检测中...",
        "card_remotion_sub": "端口 6402 视频预览服务",
        "card_engine_run_title": "发音服务状态",
        "card_footprints_title": "学习足迹",
        "card_footprints_sub": "本地示例就绪，可一键出片",
        
        # 生态推广卡片
        "promo_web_title": "🌐 TheBoringEnglish 沉浸式英语学习平台",
        "promo_web_desc": "让英语学习自然发生。AI 智能精读、原生 YouTube 影视台词意群对齐、生词本智能记忆算法，打造听说读写完整学习闭环。",
        "btn_open_web": "🚀 访问 TheBoringEnglish 官网",
        "promo_yt_title": "🎬 TBE-YouTube 双语字幕 Pro (浏览器扩展)",
        "promo_yt_desc": "在 YouTube 观看视频时提供母语级精准双语字幕，鼠标悬停即查生词、智能暂停跟读，一键将视频字幕导出到 TBE 网页端深度精读。",
        "btn_open_yt": "📥 了解并获取 YouTube 扩展",
        
        # 系统环境与健康体检
        "diag_title": "🔍 本地运行环境诊断与组件自检",
        "diag_refresh": "重检",
        "doctor_title": "🩺 系统环境与网络健康体检",
        "doctor_btn": "体检",
        "doctor_recheck": "重检",

        # 本地发音引擎页面
        "engine_title": "⚡ 本地发音引擎 (Local Speech Engine)",
        "engine_sub": "将本地算力化身高速发音节点，为浏览器与云端精读提供毫秒级高保真原声发音",
        "engine_start": "启动",
        "engine_stop": "暂停",
        "engine_running": "发音引擎运行中",
        "engine_stopped": "已停止",
        "stat_today_completed": "今日发音句子",
        "stat_uptime": "本次在线时长",
        "stat_threads": "并发计算线程",
        "console_title": "📋 发音任务调度实时流水日志",
        "autoscroll": "自动滚屏",
        "clear_log": "清空",
        "tray_hint": "💡 提示：开启后客户端可在系统托盘后台静默运行，无需保持窗口开启。",

        # 足迹与出片历史
        "nav_footprints": "🎬  足迹出片历史",
        "fp_title": "🎬 足迹出片记录与管理 (Video History)",
        "fp_sub": "由 theboringenglish.com 网页端精读/跟读足迹调起生成，本地自动归档出片历史，随时回看与重新预览",
        "fp_sync": "刷新",
        "fp_open_web_footprints": "制作",
        "fp_list_title": "已生成视频工程历史档案:",
        "fp_empty_title": "暂无足迹视频生成记录",
        "fp_empty_desc": "在 theboringenglish.com 网页端学习足迹中点击「一键 Remotion 预览」或生成视频，客户端将自动在此归档展示。",
        "fp_btn_reopen": "预览",
        "fp_btn_open_folder": "打开",
        "fp_btn_delete": "删除",
        "fp_total_count": "共 {count} 条历史生成视频",
        "fp_status_ready": "工程就绪",

        # 设置中心与二级导航
        "set_title": "⚙️ 系统偏好与账户设置 (Settings)",
        "set_sub": "管理 theboringenglish.com 关联账户、软件语言与高级系统选项",
        "set_save_all": "保存",
        "tab_general": "通用设置",
        "tab_account": "账号关联",
        "tab_advanced": "高级选项",
        "tab_about": "关于客户端",
        "sec_account": "👤 theboringenglish.com 账户关联",
        "acc_not_linked": "未关联官方账号 (游客体验)",
        "acc_linked": "已关联账号",
        "acc_user_label": "用户名 / 邮箱:",
        "acc_pass_label": "密码:",
        "acc_token_label": "或者手动粘贴 Token:",
        "btn_browser_link": "同步",
        "browser_link_hint": "💡 提示：点击将在默认浏览器打开 theboringenglish.com 登录页，登录成功后会自动免密同步至本客户端。",
        "btn_login_link": "关联",
        "btn_logout_link": "解绑",
        "acc_vip_badge": "VIP 会员权益已激活",
        "acc_normal_badge": "标准免费用户",

        "sec_general": "🌐 界面与常用偏好",
        "set_lang": "软件界面语言:",
        "set_theme": "界面主题风格:",
        "theme_dark": "深邃暗黑 (Dark Modern)",
        "theme_light": "极简透亮 (Light Minimal)",
        "set_tray": "关闭窗口时最小化至系统托盘，保持后台静默运行",
        "sec_advanced": "🔧 高级选项 (高级用户，通常保持默认即可)",
        "adv_toggle_show": "展开高级设置 ▼",
        "adv_toggle_hide": "折叠高级设置 ▲",
        "adv_server_url": "TBE 服务端接口:",
        "adv_remotion_url": "Remotion 服务接口:",
        "adv_model_dir": "离线模型存放目录:",
        "adv_audio_dir": "音频导出默认目录:",
        "adv_btn_kokoro": "📥 下载/校验 Kokoro 离线模型",

        # 关于
        "about_brand": "TheBoringEnglish Client",
        "about_version_desc": "v1.0.0 · AI 沉浸式母语级英语学习桌面生态",
        "about_author_title": "制作团队",
        "about_author_val": "TheBoringEnglish",
        "about_wechat_title": "官方平台",
        "about_wechat_val": "官网直达",
        "about_tg_title": "扩展支持",
        "about_tg_val": "YouTube Pro",
        "about_repo_title": "开源生态",
        "about_repo_val": "访问仓库",
        "about_btn_check_update": "更新",
        "about_copyright": "Copyright © 2025-2026 TheBoringEnglish. All rights reserved.",

        # 托盘菜单
        "tray_show": "🖥️  显示主界面",
        "tray_engine": "⚡  本地发音引擎",
        "tray_footprints": "👣  足迹与出片",
        "tray_settings": "⚙️  系统偏好设置",
        "tray_quit": "🚪  退出程序",

        # 首次安装向导
        "wiz_title": "欢迎使用 TheBoringEnglish 桌面端",
        "wiz_welcome": "快速初始化向导",
        "wiz_desc": "只需简单两步，设置您的首选语言与数据存储路径，即可开启原生母语级英语学习体验。",
        "wiz_lang_sel": "1. 选择界面语言 (Select Language):",
        "wiz_path_sel": "2. 选择模型与数据存储目录:",
        "wiz_start_btn": "完成",

        # 新版看板与任务
        "dash_tab_youtube": "精选",
        "dash_tab_news": "新闻",
        "dash_btn_shuffle": "刷新",
        "dash_click_to_study": "精读",
        "dash_import_study": "精读",
        "btn_start_study": "开始",
        "dash_guest_user": "未登录访客",
        "dash_guest_tip": "关联账号同步学习轨迹",
        "dash_btn_login": "登录",
        "dash_btn_my_center": "主页",
        "dash_refresh_tooltip": "刷新数据",
        "dash_open_portal": "官网",
        "dash_no_videos": "暂无推荐视频，请稍后刷新",
        "dash_no_news": "暂无环球新闻资讯，请稍后刷新",
        "cat_all": "全部",
        "cat_speeches": "TED 演说",
        "cat_podcasts": "播客 Talks",
        "cat_news": "全球新闻",
        "cat_movies": "影视原声",
        "cat_music": "音乐歌曲",
        "cat_kids": "儿童卡通",
        "nav_scene": "情景对话",
        "nav_article": "双语精读",
        "nav_podcast": "原声播客",
        "nav_vocab": "词汇打卡",
        "nav_grammar": "核心语法",
        "nav_speaking": "口语对话",
    },
    "en_US": {
        # Common
        "app_title": "TheBoringEnglish Desktop Client",
        "app_subtitle": "Local Speech Engine · Footprint Remotion · Eco Sync",
        "save": "Save",
        "cancel": "Cancel",
        "confirm": "Confirm",
        "loading": "Loading...",
        "browse": "Browse...",
        "ready": "Ready",
        "online": "Online",
        "offline": "Offline",
        "success": "Success",
        "failed": "Failed",
        "yes": "Yes",
        "no": "No",

        # Sidebar
        "nav_dashboard": "🏠  Dashboard",
        "nav_engine": "⚡  Local Speech Engine",
        "nav_footprints": "👣  Footprints & Video",
        "nav_settings": "⚙️  Settings",
        "client_brand": "TBE Client",
        "client_sub": "Desktop Workspace",
        "public_release": "v1.0.0 Public Release",

        # Dashboard
        "dash_welcome": "Welcome to TheBoringEnglish Client",
        "dash_sub": "Local AI Neural Speech · Footprint Video Preview · Immersive English Learning",
        "status_cloud_ok": "Cloud Linked",
        "status_cloud_guest": "Guest / Offline Mode",
        "card_engine_title": "Speech Engine",
        "card_engine_val": "Ready",
        "card_engine_sub": "Edge-TTS + Offline Kokoro",
        "card_remotion_title": "Remotion Video",
        "card_remotion_val": "Checking...",
        "card_remotion_sub": "Port 6402 Video Service",
        "card_engine_run_title": "Engine Status",
        "card_footprints_title": "Footprints",
        "card_footprints_sub": "Demo records ready for video render",

        # Eco Promo Cards
        "promo_web_title": "🌐 TheBoringEnglish Learning Platform",
        "promo_web_desc": "Make English acquisition natural. AI-powered intensive reading, genuine YouTube sentence alignment, and spaced-repetition vocabulary book.",
        "btn_open_web": "🚀 Open theboringenglish.com",
        "promo_yt_title": "🎬 TBE-YouTube Dual Subtitles Pro",
        "promo_yt_desc": "Native bilingual subtitles for YouTube. Hover over any word to inspect phonetic definitions, auto-pause sync, and one-click export to TBE Web.",
        "btn_open_yt": "📥 Discover YouTube Extension",

        # Diagnostics & Health Doctor
        "diag_title": "🔍 System Diagnostics & Components Check",
        "diag_refresh": "🔄 Re-check",
        "doctor_title": "🩺 System & Network Health Doctor",
        "doctor_btn": "🩺 System Doctor",
        "doctor_recheck": "🔄 Re-check",

        # Local Speech Engine
        "engine_title": "⚡ Local Speech Engine",
        "engine_sub": "Run local speech synthesis node for ultra-low latency native speech in browser and web studies",
        "engine_start": "▶ Start Speech Engine",
        "engine_stop": "⏸ Pause Speech Engine",
        "engine_running": "Engine Active",
        "engine_stopped": "Stopped",
        "stat_today_completed": "Sentences Synthesized",
        "stat_uptime": "Active Uptime",
        "stat_threads": "Worker Threads",
        "console_title": "📋 Realtime Speech Dispatch Logs",
        "autoscroll": "Auto Scroll",
        "clear_log": "Clear Logs",
        "tray_hint": "💡 Hint: When enabled, the client runs silently in the system tray without keeping the window open.",

        # Footprints & Generated Video History
        "nav_footprints": "🎬  Video History",
        "fp_title": "🎬 Footprint Video History & Management",
        "fp_sub": "Triggered and generated from theboringenglish.com web study footprints, automatically archived locally for re-watching and preview",
        "fp_sync": "🔄 Refresh History",
        "fp_open_web_footprints": "🌐 Open Web Study Footprints",
        "fp_list_title": "Generated Remotion Video Archives:",
        "fp_empty_title": "No Generated Video Records Yet",
        "fp_empty_desc": "Click 'One-Click Remotion Preview' on theboringenglish.com study history to trigger video generation. Projects will be automatically archived here.",
        "fp_btn_reopen": "🚀 Reopen Browser Preview",
        "fp_btn_open_folder": "📁 Open Project Folder",
        "fp_btn_delete": "🗑️ Remove Record",
        "fp_total_count": "Total {count} generated video projects",
        "fp_status_ready": "Ready",

        # Settings & Sub-tabs
        "set_title": "⚙️ Preferences & Account (Settings)",
        "set_sub": "Manage theboringenglish.com account linking, language, and advanced settings",
        "set_save_all": "💾 Save Settings",
        "tab_general": "General",
        "tab_account": "Account",
        "tab_advanced": "Advanced",
        "tab_about": "About",
        "sec_account": "👤 theboringenglish.com Account Link",
        "acc_not_linked": "Account Not Linked (Guest Mode)",
        "acc_linked": "Account Linked",
        "acc_user_label": "Username / Email:",
        "acc_pass_label": "Password:",
        "acc_token_label": "Or Paste Auth Token Directly:",
        "btn_browser_link": "🌐 Open Browser to Link Account",
        "browser_link_hint": "💡 Tip: Opens theboringenglish.com login in your browser and automatically syncs back to this client upon login.",
        "btn_login_link": "🔗 Link Account",
        "btn_logout_link": "Unlink Account",
        "acc_vip_badge": "VIP Member Active",
        "acc_normal_badge": "Standard Free User",

        "sec_general": "🌐 Interface & Preferences",
        "set_lang": "Application Language:",
        "set_theme": "Theme Style:",
        "theme_dark": "Dark Modern",
        "theme_light": "Light Minimal",
        "set_tray": "Minimize to system tray on window close, keep background running",
        "sec_advanced": "🔧 Advanced Settings (Normally keep defaults)",
        "adv_toggle_show": "Show Advanced Settings ▼",
        "adv_toggle_hide": "Hide Advanced Settings ▲",
        "adv_server_url": "TBE Backend URL:",
        "adv_remotion_url": "Remotion Service URL:",
        "adv_model_dir": "Offline Models Directory:",
        "adv_audio_dir": "Audio Output Directory:",
        "adv_btn_kokoro": "📥 Download / Verify Kokoro Model",

        # About
        "about_brand": "TheBoringEnglish Client",
        "about_version_desc": "v1.0.0 · AI Immersive English Learning Desktop Ecosystem",
        "about_author_title": "Creator",
        "about_author_val": "TheBoringEnglish",
        "about_wechat_title": "Official Web",
        "about_wechat_val": "theboringenglish.com",
        "about_tg_title": "Extension",
        "about_tg_val": "YouTube Pro",
        "about_repo_title": "Repository",
        "about_repo_val": "View Code",
        "about_btn_check_update": "🔄 Check for Updates",
        "about_copyright": "Copyright © 2025-2026 TheBoringEnglish. All rights reserved.",

        # Tray
        "tray_show": "🖥️  Open Main Window",
        "tray_engine": "⚡  Local Speech Engine",
        "tray_footprints": "👣  Footprints & Video",
        "tray_settings": "⚙️  Preferences",
        "tray_quit": "🚪  Quit Application",

        # Setup Wizard
        "wiz_title": "Welcome to TheBoringEnglish Client",
        "wiz_welcome": "Quick Setup Wizard",
        "wiz_desc": "Just two simple steps to configure your preferred language and data storage directory.",
        "wiz_lang_sel": "1. Select Interface Language:",
        "wiz_path_sel": "2. Choose Models & Data Directory:",
        "wiz_start_btn": "🚀 Finish & Launch Client",

        # New Dashboard & Tasks
        "dash_tab_youtube": "📺 YouTube Picks",
        "dash_tab_news": "📰 World News",
        "dash_btn_shuffle": "🎲 Shuffle",
        "dash_click_to_study": "Study Now ↗",
        "dash_import_study": "Quick Import ↗",
        "btn_start_study": "Start",
        "dash_guest_user": "Guest User",
        "dash_guest_tip": "Sign in to sync daily learning goals",
        "dash_btn_login": "Sign In",
        "dash_btn_my_center": "Profile ↗",
        "dash_refresh_tooltip": "Refresh Data",
        "dash_open_portal": "Open Web ↗",
        "dash_no_videos": "No videos found, please refresh",
        "dash_no_news": "No news found, please refresh",
        "cat_all": "All",
        "cat_speeches": "Speeches",
        "cat_podcasts": "Podcasts",
        "cat_news": "News",
        "cat_movies": "Movies",
        "cat_music": "Music",
        "cat_kids": "Kids",
        "nav_scene": "Daily Scenes",
        "nav_article": "Articles",
        "nav_podcast": "Podcasts",
        "nav_vocab": "Vocabulary",
        "nav_grammar": "Grammar Tutor",
        "nav_speaking": "Speaking QA",
    }
}


class I18nManager:
    """国际化翻译管理器"""

    @classmethod
    def current_lang(cls) -> str:
        lang = config.get("language", "zh_CN")
        return lang if lang in TRANSLATIONS else "zh_CN"

    @classmethod
    def set_lang(cls, lang: str):
        if lang in TRANSLATIONS:
            config.set("language", lang)

    @classmethod
    def t(cls, key: str, default_or_arg: str = None, **kwargs) -> str:
        lang = cls.current_lang()
        fallback = default_or_arg if isinstance(default_or_arg, str) else key
        text = TRANSLATIONS.get(lang, {}).get(key) or TRANSLATIONS["zh_CN"].get(key, fallback)
        if kwargs:
            try:
                return text.format(**kwargs)
            except Exception:
                return text
        return text


# 全局翻译助手函数
t = I18nManager.t
set_language = I18nManager.set_lang

