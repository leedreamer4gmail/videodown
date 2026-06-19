"""
各平台解析能力实时探测。
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from typing import Any, Literal

from videodown.core.platforms.base import ProbeSpec
from videodown.core.platforms.registry import parse_video, probe_specs
from videodown.core.ytdlp_config import optional_xhs_probe_url, xhs_cookie_ready, youtube_cookie_ready

logger = logging.getLogger(__name__)

PlatformStatus = Literal["ok", "cookie_required", "unstable", "varies", "error", "checking"]
_PROBE_TIMEOUT_SEC = 20.0


def _status_from_error(name: str, error: str, requires_cookie: bool) -> PlatformStatus:
    lower = error.lower()
    if name == "小红书" and xhs_cookie_ready() and ("过期" in error or "404" in lower):
        return "ok"
    if requires_cookie and name == "YouTube" and not youtube_cookie_ready():
        return "cookie_required"
    if "cookie" in lower or "登录" in error or "sign in" in lower:
        if name == "YouTube" and youtube_cookie_ready():
            return "unstable"
        return "cookie_required"
    if "412" in error or "超时" in error or "timeout" in lower:
        return "unstable"
    if name == "快手" and "unsupported" in lower:
        return "error"
    if requires_cookie:
        return "unstable"
    return "error"


def _note_from_result(target: ProbeSpec, title: str, fmt_count: int, error: str) -> str:
    if title and fmt_count > 0:
        short = title if len(title) <= 18 else f"{title[:17]}…"
        suffix = " · 访客可用" if target.name == "YouTube" and youtube_cookie_ready() else ""
        return f"实测通过 · {fmt_count} 种清晰度 · 《{short}》{suffix}"
    if error:
        return error if len(error) <= 48 else f"{error[:47]}…"
    return "探测失败"


def _probe_xiaohongshu() -> dict[str, Any]:
    started = datetime.now(timezone.utc)
    if not xhs_cookie_ready():
        return {
            "name": "小红书",
            "status": "cookie_required",
            "note": "未配置 Cookie 或缺少 web_session，访客无法解析",
            "latency_ms": 0,
        }
    probe_url = optional_xhs_probe_url()
    if not probe_url:
        latency_ms = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
        return {
            "name": "小红书",
            "status": "ok",
            "note": "Cookie 已配置 · 访客粘贴最新分享链接即可使用",
            "latency_ms": latency_ms,
        }
    result = parse_video(probe_url)
    latency_ms = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
    spec = ProbeSpec("小红书", probe_url, 1, True)
    if not result.error and result.formats:
        return {
            "name": "小红书",
            "status": "ok",
            "note": _note_from_result(spec, result.title, len(result.formats), ""),
            "latency_ms": latency_ms,
        }
    if result.error and ("过期" in result.error or "404" in result.error):
        return {
            "name": "小红书",
            "status": "ok",
            "note": "Cookie 已配置 · 访客可用（探针链接已过期，请粘贴新分享链接）",
            "latency_ms": latency_ms,
        }
    return {
        "name": "小红书",
        "status": _status_from_error("小红书", result.error, True),
        "note": _note_from_result(spec, result.title, len(result.formats), result.error),
        "latency_ms": latency_ms,
    }


def _probe_one(target: ProbeSpec) -> dict[str, Any]:
    started = datetime.now(timezone.utc)
    try:
        result = parse_video(target.url)
        latency_ms = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
        if result.error:
            status = _status_from_error(target.name, result.error, target.requires_cookie)
            note = _note_from_result(target, "", 0, result.error)
            if target.name == "YouTube" and youtube_cookie_ready() and status == "cookie_required":
                status = "unstable"
                note = "公开视频可解析；部分视频需有效 Cookie · 访客可用"
            return {"name": target.name, "status": status, "note": note, "latency_ms": latency_ms}
        return {
            "name": target.name,
            "status": "ok",
            "note": _note_from_result(target, result.title, len(result.formats), ""),
            "latency_ms": latency_ms,
        }
    except Exception as exc:  # noqa: BLE001
        latency_ms = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
        msg = str(exc).strip() or exc.__class__.__name__
        logger.warning("平台探测异常 %s: %s", target.name, msg)
        return {
            "name": target.name,
            "status": _status_from_error(target.name, msg, target.requires_cookie),
            "note": _note_from_result(target, "", 0, msg),
            "latency_ms": latency_ms,
        }


def probe_platforms() -> dict[str, Any]:
    targets = probe_specs()
    platforms: list[dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=len(targets) + 1) as pool:
        futures = {pool.submit(_probe_one, t): t for t in targets}
        futures[pool.submit(_probe_xiaohongshu)] = None
        for future in as_completed(futures, timeout=_PROBE_TIMEOUT_SEC + 5):
            try:
                platforms.append(future.result(timeout=_PROBE_TIMEOUT_SEC))
            except Exception as exc:  # noqa: BLE001
                target = futures[future]
                name = target.name if target else "小红书"
                platforms.append(
                    {
                        "name": name,
                        "status": "unstable",
                        "note": f"探测超时或异常：{exc.__class__.__name__}",
                        "latency_ms": int(_PROBE_TIMEOUT_SEC * 1000),
                    }
                )
    order = {s.name: s.order for s in targets}
    order["小红书"] = 1
    platforms.sort(key=lambda p: order.get(p["name"], 99))
    platforms.append(
        {
            "name": "其它平台",
            "status": "varies",
            "note": "yt-dlp 理论支持上千网站，视目标站反爬策略而定",
            "latency_ms": 0,
        }
    )
    return {
        "checked_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "visitor_mode": True,
        "visitor_note": "访客无需登录：抖音可直接用；小红书/YouTube 使用服务器统一 Cookie",
        "youtube_cookie_configured": youtube_cookie_ready(),
        "xiaohongshu_cookie_configured": xhs_cookie_ready(),
        "platforms": platforms,
    }
