"""
视频链接规范化：小红书短链、口令文案等。
"""

from __future__ import annotations

import logging
import re
from urllib.parse import parse_qs, urlencode, urlparse

from videodown.core.http.mobile import follow_redirects

logger = logging.getLogger(__name__)

_XHS_HOSTS = ("xhslink.com", "xiaohongshu.com", "xhs.cn")


def is_xiaohongshu_url(url: str) -> bool:
    lower = url.lower()
    return any(host in lower for host in _XHS_HOSTS)


def is_youtube_url(url: str) -> bool:
    lower = url.lower()
    return "youtube.com" in lower or "youtu.be" in lower


def is_twitter_url(url: str) -> bool:
    """x.com / twitter.com 推文链接。"""
    lower = url.lower()
    if "twitter.com" in lower or "x.com" in lower:
        return True
    parsed = urlparse(lower)
    host = parsed.netloc.removeprefix("www.")
    return host in ("x.com", "twitter.com", "mobile.twitter.com", "mobile.x.com")


def is_kuaishou_url(url: str) -> bool:
    """快手分享链接。"""
    lower = url.lower()
    return any(
        marker in lower
        for marker in (
            "kuaishou.com",
            "v.kuaishou.com",
            "chenzhongtech.com",
            "kwaicdn.com",
        )
    )


def is_tiktok_url(url: str) -> bool:
    """TikTok 分享链接。"""
    lower = url.lower()
    return any(
        marker in lower
        for marker in (
            "tiktok.com",
            "vm.tiktok.com",
            "vt.tiktok.com",
        )
    )


def normalize_video_url(url: str) -> str:
    """将短链/口令链接转为各平台可识别的完整 URL。"""
    if is_xiaohongshu_url(url):
        return _normalize_xhs(url)
    return url


def _normalize_xhs(url: str) -> str:
    try:
        final = follow_redirects(url)
    except Exception as exc:  # noqa: BLE001
        logger.warning("小红书短链跳转失败: %s", exc)
        return url

    if "xsec_token=" in final and "xiaohongshu.com" in final:
        return final

    parsed = urlparse(final)
    qs = parse_qs(parsed.query)
    note_id = (qs.get("noteId") or [None])[0]
    if not note_id:
        m = re.search(r"/(?:explore|discovery/item)/([0-9a-f]+)", parsed.path, re.I)
        note_id = m.group(1) if m else None
    token = (qs.get("xsec_token") or [""])[0]
    if note_id and token:
        query = urlencode({"xsec_token": token, "xsec_source": "app_share"})
        if "/discovery/" in final or (qs.get("type") or [""])[0] == "video":
            return f"https://www.xiaohongshu.com/discovery/item/{note_id}?{query}"
        return f"https://www.xiaohongshu.com/explore/{note_id}?{query}"
    return final
