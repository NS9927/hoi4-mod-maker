"""版本更新检查 — 启动时后台检查 GitHub Releases。"""
from __future__ import annotations

import json
import urllib.request
from typing import Optional

from version import VERSION

GITHUB_API_URL = "https://api.github.com/repos/AmonStreeling/hoi4-mod-maker/releases/latest"
GITHUB_RELEASES_URL = "https://github.com/AmonStreeling/hoi4-mod-maker/releases"


def check_for_update() -> Optional[dict]:
    """检查是否有新版本。返回 None 表示已是最新，否则返回 {version, body, url}。
    网络错误静默返回 None（不打扰用户）。"""
    try:
        req = urllib.request.Request(
            GITHUB_API_URL,
            headers={"User-Agent": "hoi4-map-maker", "Accept": "application/vnd.github.v3+json"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        remote_version = data.get("tag_name", "").lstrip("v")
        if not remote_version:
            return None

        if _is_newer(remote_version, VERSION):
            return {
                "version": remote_version,
                "body": data.get("body", ""),
                "url": data.get("html_url", GITHUB_RELEASES_URL),
            }
        return None
    except Exception:
        return None


def _is_newer(remote: str, local: str) -> bool:
    """比较版本号，remote > local 返回 True。
    支持格式：1.0.0 / 1.0.0-beta.1 等。"""
    def _parse(v: str) -> tuple:
        # 去掉 -beta.1 之类的后缀做主版本比较
        main = v.split("-")[0]
        parts = []
        for p in main.split("."):
            try:
                parts.append(int(p))
            except ValueError:
                parts.append(0)
        # 有 pre-release 后缀的比没有的低
        pre = v.split("-", 1)[1] if "-" in v else ""
        return tuple(parts), pre

    r_main, r_pre = _parse(remote)
    l_main, l_pre = _parse(local)

    if r_main > l_main:
        return True
    if r_main == l_main:
        # 同主版本：无 pre > 有 pre（1.0.0 > 1.0.0-beta.1）
        if not r_pre and l_pre:
            return True
        # 都有 pre：按字符串比较
        if r_pre and l_pre and r_pre > l_pre:
            return True
    return False
