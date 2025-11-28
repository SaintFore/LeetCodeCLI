"""
用户认证模块
负责LeetCode Cookie的管理和认证
"""

import os
import json
from pathlib import Path
from typing import Optional
import click


class AuthManager:
    """认证管理器 - 管理用户凭证"""

    def __init__(self, data_dir: str = None):
        # 使用 XDG 标准目录
        if data_dir is None:
            xdg_config_home = os.environ.get('XDG_CONFIG_HOME',
                                            os.path.expanduser('~/.config'))
            self.data_dir = Path(xdg_config_home) / "leetcode-fsrs-cli"
        else:
            self.data_dir = Path(data_dir)

        self.auth_file = self.data_dir / "auth.json"
        self._ensure_data_dir()

    def _ensure_data_dir(self):
        """确保数据目录存在"""
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def save_cookie(self, cookie: str, user_id: Optional[str] = None) -> bool:
        """
        保存Cookie

        Args:
            cookie: LeetCode Cookie字符串
            user_id: 用户ID（可选）

        Returns:
            bool: 是否成功保存
        """
        try:
            auth_data = {
                "cookie": cookie,
                "user_id": user_id or "unknown",
                "saved_at": str(Path.cwd())
            }

            # 设置文件权限为600（仅所有者可读写）
            with open(self.auth_file, 'w', encoding='utf-8') as f:
                json.dump(auth_data, f, ensure_ascii=False, indent=2)

            # 设置文件权限
            os.chmod(self.auth_file, 0o600)
            return True

        except Exception as e:
            click.echo(f"❌ 保存Cookie失败: {e}")
            return False

    def load_cookie(self) -> Optional[str]:
        """
        加载保存的Cookie

        Returns:
            Optional[str]: Cookie字符串，如果不存在返回None
        """
        if not os.path.exists(self.auth_file):
            return None

        try:
            with open(self.auth_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("cookie")

        except Exception as e:
            click.echo(f"❌ 加载Cookie失败: {e}")
            return None

    def get_auth_info(self) -> dict:
        """
        获取认证信息

        Returns:
            dict: 包含认证状态和用户信息的字典
        """
        if not os.path.exists(self.auth_file):
            return {"authenticated": False}

        try:
            with open(self.auth_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return {
                    "authenticated": True,
                    "user_id": data.get("user_id"),
                    "cookie": f"{data.get('cookie', '')[:20]}..." if data.get('cookie') else None
                }

        except Exception as e:
            click.echo(f"❌ 读取认证信息失败: {e}")
            return {"authenticated": False}

    def clear_auth(self) -> bool:
        """
        清除保存的认证信息

        Returns:
            bool: 是否成功清除
        """
        try:
            if os.path.exists(self.auth_file):
                os.remove(self.auth_file)
            return True

        except Exception as e:
            click.echo(f"❌ 清除认证信息失败: {e}")
            return False

    def verify_cookie(self, cookie: str) -> bool:
        """
        验证Cookie有效性
        使用 LeetCodeAPIClient 检查是否能获取用户信息

        Args:
            cookie: 要验证的Cookie字符串

        Returns:
            bool: Cookie是否有效
        """
        try:
            from .leetcode_api import LeetCodeAPIClient
            client = LeetCodeAPIClient(cookie=cookie)
            return client.is_authenticated()
        except Exception as e:
            click.echo(f"⚠️ 验证过程出错: {e}")
            return False
