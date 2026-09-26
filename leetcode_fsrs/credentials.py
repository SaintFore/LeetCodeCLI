"""Device-local LeetCode session storage."""

from __future__ import annotations

import os


SERVICE = "leetcode-fsrs"
ACCOUNT = "leetcode.com-session"


class CredentialStore:
    def load(self) -> str | None:
        environment = os.environ.get("LEETCODE_SESSION")
        if environment:
            return _cookie(environment)
        try:
            import keyring

            value = keyring.get_password(SERVICE, ACCOUNT)
        except Exception:
            return None
        return _cookie(value) if value else None

    def save(self, value: str) -> None:
        try:
            import keyring

            keyring.set_password(SERVICE, ACCOUNT, _cookie(value))
        except Exception as error:
            raise RuntimeError(
                "No usable system keyring. Set LEETCODE_SESSION in the environment instead."
            ) from error

    def clear(self) -> None:
        try:
            import keyring

            keyring.delete_password(SERVICE, ACCOUNT)
        except Exception:
            pass


def _cookie(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("LeetCode session cannot be empty")
    if ";" in value or value.startswith("LEETCODE_SESSION="):
        return value
    return f"LEETCODE_SESSION={value}"
