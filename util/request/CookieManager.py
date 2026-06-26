"""
CookieManager 精简版 — 仅支持从 cookies 列表或 cookies.json 文件读取。
去除了原项目对 KVDatabase（TinyDB）的依赖，直接用标准 JSON 解析。
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class Account:
    """B站账号信息"""
    uid: str
    name: str
    face: str
    cookies: list[dict]
    level: int = 0
    is_vip: bool = False
    coins: float = 0.0


class CookieManager:
    """
    管理 cookies，支持两种来源：
    1. 直接传入 cookies 列表（List[dict]）
    2. 从 cookies.json 文件路径读取

    cookies.json 支持以下两种格式：
    - TinyDB 格式: {"_default": {"1": {"key": "cookie", "value": [...]}}}
    - 简单格式: [{"name": "SESSDATA", "value": "xxx"}, ...]
    """

    def __init__(self, config_file_path: str | None = None, cookies: list | None = None):
        self._cookies: list | None = cookies
        self._config_file_path = config_file_path
        # 如果既有文件又有直接传入的 cookies，直接传入的优先
        if self._cookies is None and config_file_path:
            self._cookies = self._load_from_file(config_file_path)

    @staticmethod
    def _load_from_file(path: str) -> list | None:
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw: Any = json.load(f)
        except Exception:
            return None

        # TinyDB 格式: {"_default": {"1": {"key": "cookie", "value": [...]}}}
        if isinstance(raw, dict):
            default_group = raw.get("_default")
            if isinstance(default_group, dict):
                for item in default_group.values():
                    if isinstance(item, dict) and item.get("key") == "cookie":
                        return item.get("value")
            # 直接是 {"key": "cookie", "value": [...]}
            if raw.get("key") == "cookie":
                return raw.get("value")

        # 简单格式: [{"name": "...", "value": "..."}]
        if isinstance(raw, list):
            return raw

        return None

    def get_cookies(self, force: bool = False) -> list | None:
        if force:
            return self._cookies
        if not self._cookies:
            raise RuntimeError("当前未登录，请在 cookies.json 中配置 Cookie 或直接传入 cookies 参数")
        return self._cookies

    def have_cookies(self) -> bool:
        return bool(self._cookies)
