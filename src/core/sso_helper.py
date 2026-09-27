# -*- coding: utf-8 -*-
"""
TBE Client 单点登录 (SSO) 与官网一键直达模块
通过注入当前用户的登录凭证 (sso_token)，在系统浏览器中免密拉起官网对应学习页面。
"""

import urllib.parse
import webbrowser
from typing import Optional
from ..config import config


def get_server_url() -> str:
    """获取当前配置的官方服务端 URL，去除末尾斜杠"""
    return config.get("server_url", "https://theboringenglish.com").rstrip("/")


def build_sso_url(target_path_or_url: str, token: Optional[str] = None) -> str:
    """
    构建携带 SSO 登录态的完整目标 URL
    
    :param target_path_or_url: 目标路径 (如 '/scene'、'/videos?v=123') 或完整 URL
    :param token: 可选传入 token，若未传则从全局配置中读取
    :return: 包含 sso_token 的完整 URL
    """
    server_url = get_server_url()
    active_token = token or config.get("token", "").strip()

    # 处理绝对路径与相对路径
    if target_path_or_url.startswith("http://") or target_path_or_url.startswith("https://"):
        full_url = target_path_or_url
    else:
        clean_path = target_path_or_url if target_path_or_url.startswith("/") else f"/{target_path_or_url}"
        full_url = f"{server_url}{clean_path}"

    # 若未登录，直接返回原链接
    if not active_token:
        return full_url

    # 严格安全白名单：仅对受信任的官方域名注入 sso_token，严防将用户凭据泄露给第三方外链
    parsed = urllib.parse.urlparse(full_url)
    server_parsed = urllib.parse.urlparse(server_url)
    trusted_hosts = {
        server_parsed.netloc.lower(),
        "theboringenglish.com",
        "www.theboringenglish.com",
        "localhost:6501",
        "127.0.0.1:6501",
        "localhost:3000",
        "127.0.0.1:3000"
    }
    if parsed.netloc.lower() not in trusted_hosts:
        print(f"[SSO 安全拦截] 目标域名 ({parsed.netloc}) 非受信任官方站点，拒绝附加凭证。")
        return full_url

    # 解析 URL 并优先申请短期一次性 SSO 兑换票据 (Ticket)
    from .auth_api import AuthAPI
    ticket = AuthAPI.create_sso_ticket(active_token)

    query_dict = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)
    new_parts = list(parsed)

    if ticket:
        # 1. 正常链路：使用短期一次性 Ticket，60 秒有效、消费即焚，彻底避免长效 Token 泄露
        query_dict["sso_ticket"] = [ticket]
        new_parts[4] = urllib.parse.urlencode(query_dict, doseq=True)
        return urllib.parse.urlunparse(new_parts)
    else:
        # 2. 降级兜底：若网络异常未能向后端申请到 ticket，使用 URL Hash (#) 传递
        # HTTP 协议规定 Hash 片段绝不上报给服务器，杜绝服务端日志和 Referer 泄露
        new_parts[4] = urllib.parse.urlencode(query_dict, doseq=True)
        existing_fragment = parsed.fragment
        frag_dict = urllib.parse.parse_qs(existing_fragment, keep_blank_values=True) if existing_fragment else {}
        frag_dict["sso_token"] = [active_token]
        new_parts[5] = urllib.parse.urlencode(frag_dict, doseq=True)
        return urllib.parse.urlunparse(new_parts)


def open_web_with_sso(target_path_or_url: str = "/", token: Optional[str] = None) -> bool:
    """
    使用系统默认浏览器打开携带 SSO 凭证的官网页面
    
    :param target_path_or_url: 目标路径或页面
    :param token: 可选 Token
    :return: 是否成功调起浏览器
    """
    try:
        final_url = build_sso_url(target_path_or_url, token)
        print(f"[SSO] 正在拉起系统浏览器直达: {target_path_or_url}")
        return webbrowser.open(final_url)
    except Exception as e:
        print(f"[SSO] 拉起浏览器失败: {e}")
        return False
