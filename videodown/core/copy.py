"""从视频自动语音字幕提炼文字（非作者简介）。"""

from __future__ import annotations

import html
import re
from typing import Any
from urllib.request import Request, urlopen

_VTT_TS = re.compile(
    r"^\d{2}:\d{2}:\d{2}\.\d{3}\s+-->\s+\d{2}:\d{2}:\d{2}\.\d{3}\s*$",
    re.MULTILINE,
)
_VTT_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\n{3,}")


def clean_copy(text: str) -> str:
    if not text:
        return ""
    s = html.unescape(str(text))
    s = _VTT_TAG.sub("", s)
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    lines = [ln.strip() for ln in s.split("\n")]
    s = "\n".join(ln for ln in lines if ln)
    return _WS.sub("\n\n", s).strip()


def _vtt_to_text(raw: str) -> str:
    """VTT/SRT → 文本，保留原有标点。"""
    lines: list[str] = []
    seen: set[str] = set()
    for line in raw.splitlines():
        t = line.strip()
        if not t or t.startswith("WEBVTT") or t.startswith("NOTE"):
            continue
        if t.isdigit() or _VTT_TS.match(t) or t.startswith("STYLE") or t.startswith("::"):
            continue
        t = _VTT_TAG.sub("", t).strip()
        if not t:
            continue
        key = re.sub(r"[\s\W_]+", "", t)
        if key in seen:
            continue
        seen.add(key)
        lines.append(t)
    return clean_copy("\n".join(lines))


def _fetch_subtitle_url(url: str) -> str:
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(req, timeout=15) as resp:  # noqa: S310
        return resp.read().decode("utf-8", errors="replace")


def _entries_from_pool(pool: dict[str, Any], langs: tuple[str, ...]) -> list[dict[str, Any]]:
    ordered: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    for lang in langs:
        items = pool.get(lang)
        if not isinstance(items, list):
            continue
        for entry in items:
            if not isinstance(entry, dict):
                continue
            url = str(entry.get("url") or "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                ordered.append(entry)
    for items in pool.values():
        if not isinstance(items, list):
            continue
        for entry in items:
            if not isinstance(entry, dict):
                continue
            url = str(entry.get("url") or "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                ordered.append(entry)
    return ordered


def speech_captions_from_info(info: dict[str, Any]) -> str:
    """自动语音字幕优先，其次人工字幕（均非作者简介）。"""
    langs = ("zh-Hans", "zh", "zh-CN", "zh-TW", "en", "en-US")
    pools: list[dict[str, Any]] = []
    auto = info.get("automatic_captions")
    manual = info.get("subtitles")
    if isinstance(auto, dict):
        pools.append(auto)
    if isinstance(manual, dict):
        pools.append(manual)
    for pool in pools:
        for entry in _entries_from_pool(pool, langs):
            url = entry.get("url")
            if not url:
                continue
            try:
                text = _vtt_to_text(_fetch_subtitle_url(str(url)))
                if len(text) >= 4:
                    return text
            except Exception:  # noqa: BLE001
                continue
    return ""
