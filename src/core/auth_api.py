# -*- coding: utf-8 -*-
"""
TheBoringEnglish 官方账号服务与一键关联 API
支持账号密码登录、Token 验证、用户信息与 VIP 状态拉取
"""

import requests
from typing import Dict, Any, Optional, Tuple
from ..config import config


class AuthAPI:
    """TheBoringEnglish 账户关联客户端"""

    @classmethod
    def get_server_url(cls) -> str:
        return config.get("server_url", "https://theboringenglish.com").rstrip("/")

    @classmethod
    def login_with_credentials(cls, username_or_email: str, password: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        通过用户名/邮箱与密码关联登录
        返回: (success, message, user_info)
        """
        server_url = cls.get_server_url()
        url = f"{server_url}/api/v1/auth/login"
        payload = {
            "username": username_or_email.strip(),
            "password": password.strip()
        }

        try:
            resp = requests.post(url, json=payload, timeout=8.0, headers={"User-Agent": "TBE-Desktop-Client/1.0"})
            data = resp.json() if resp.content else {}

            if resp.status_code == 200 and data.get("success"):
                token = data.get("token", "")
                raw_user = data.get("user", {})
                
                # 更新本地配置
                config.set("token", token)
                user_info = {
                    "id": raw_user.get("id", 0),
                    "username": raw_user.get("username", ""),
                    "is_vip": bool(raw_user.get("is_vip", False)),
                    "is_super_admin": bool(raw_user.get("is_super_admin", False))
                }
                
                # 进一步拉取详细 VIP 与头像信息
                cls.fetch_profile(token)
                return True, "账户关联成功！", user_info

            elif resp.status_code == 423:
                return False, data.get("detail", "账户或 IP 暂时锁定，请稍后再试"), None
            elif resp.status_code == 401:
                return False, "用户名或密码错误", None
            else:
                detail = data.get("detail") or data.get("message") or f"登录失败 (HTTP {resp.status_code})"
                return False, detail, None

        except requests.exceptions.ConnectionError:
            return False, f"无法连接到服务端 ({server_url})，请检查网络或服务状态", None
        except Exception as e:
            return False, f"登录网络异常: {str(e)}", None

    @classmethod
    def link_with_token(cls, token: str) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        直接通过已有 JWT Token 验证并关联账户
        """
        token = token.strip()
        if not token:
            return False, "Token 不能为空", None

        ok, msg, user_info = cls.fetch_profile(token)
        if ok and user_info:
            config.set("token", token)
            return True, "Token 校验成功，已绑定账户！", user_info
        return False, msg, None

    @classmethod
    def fetch_profile(cls, token: Optional[str] = None) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        获取当前 Token 对应的用户 profile 与 VIP 状态
        """
        token = token or config.get("token", "")
        if not token:
            return False, "未登录", None

        server_url = cls.get_server_url()
        url = f"{server_url}/api/v1/auth/me"
        headers = {
            "User-Agent": "TBE-Desktop-Client/1.0",
            "Authorization": f"Bearer {token}"
        }

        try:
            resp = requests.get(url, headers=headers, timeout=6.0)
            if resp.status_code == 200:
                data = resp.json()
                u = data.get("user", {})
                user_info = {
                    "id": u.get("id", 0),
                    "username": u.get("username", ""),
                    "avatar": u.get("avatar_url", ""),
                    "is_vip": bool(u.get("is_vip", False) or u.get("is_max", False)),
                    "is_super_admin": bool(u.get("is_super_admin", False)),
                    "plan_id": u.get("plan_id")
                }
                config.set("user_info", user_info)
                return True, "获取成功", user_info
            elif resp.status_code == 401:
                config.clear_auth()
                return False, "登录凭证已过期，请重新登录", None
            else:
                return False, f"服务响应异常: HTTP {resp.status_code}", None
        except Exception as e:
            return False, f"网络异常: {str(e)}", None

    @classmethod
    def logout(cls):
        """解除关联 / 退出登录"""
        config.clear_auth()
