"""快手平台适配器。"""

from __future__ import annotations

import json
import logging
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from videodown.core.http.mobile import fetch_with_cookies, mobile_headers, mobile_opener
from videodown.core.models import ParseResult, VideoFormat, empty_parse
from videodown.core.platforms.base import PlatformAdapter, ProbeSpec
from videodown.core.url_normalize import is_kuaishou_url

logger = logging.getLogger(__name__)

_QUALITY_ORDER = {"hd15": 4, "hd": 3, "b": 2, "default": 1}


@dataclass(frozen=True)
class _KsVideo:
    title: str
    duration: int
    formats: tuple[VideoFormat, ...]


class KuaishouPlatform(PlatformAdapter):
    slug = "kuaishou"

    def matches(self, url: str) -> bool:
        return is_kuaishou_url(url)

    def probe_spec(self) -> ProbeSpec:
        return ProbeSpec("快手", "https://v.kuaishou.com/JxenmDQI", 4)

    def owns_format_id(self, format_id: str | None) -> bool:
        return bool(format_id and format_id.startswith("http"))

    def parse(self, url: str) -> ParseResult:
        final_url = url
        try:
            final_url, html = fetch_with_cookies(url)
            extract_photo_id(final_url)
            parsed = _parse_mobile_html(html)
        except Exception as exc:  # noqa: BLE001
            logger.warning("快手移动端解析失败 %s: %s", url, exc)
            try:
                photo_id = extract_photo_id(url)
            except ValueError:
                return empty_parse(url, f"快手解析失败：{exc}", extractor=self.slug)
            parsed = _graphql_fetch(photo_id)
            if parsed is None:
                return empty_parse(url, f"快手解析失败：{exc}", extractor=self.slug)
            final_url = url

        if not parsed.formats:
            return empty_parse(
                final_url,
                "快手作品未返回可下载视频（可能是图文或链接已失效）",
                extractor=self.slug,
            )
        return ParseResult(
            url=final_url,
            title=parsed.title,
            duration=parsed.duration,
            formats=parsed.formats,
            extractor=self.slug,
        )

    def download_temp(self, url: str, format_id: str | None, dest: Path) -> Path:
        if not format_id or not self.owns_format_id(format_id):
            raise ValueError("快手下载需要 CDN 直链 format_id")
        return download_url_to_file(format_id, dest, referer="https://www.kuaishou.com/", opener=mobile_opener())


def extract_photo_id(url: str) -> str:
    parsed = urlparse(url)
    qs = parse_qs(parsed.query)
    for key in ("photoId", "photo_id"):
        if qs.get(key):
            return str(qs[key][0])
    for pattern in (r"/short-video/([A-Za-z0-9_-]+)", r"/fw/photo/([A-Za-z0-9_-]+)", r"/photo/([A-Za-z0-9_-]+)"):
        m = re.search(pattern, parsed.path)
        if m:
            return m.group(1)
    raise ValueError("无法从链接中识别快手作品 ID")


def _quality_key(video_url: str) -> tuple[int, int]:
    tt_m = re.search(r"[?&]tt=([^&\"]+)", video_url)
    tt = (tt_m.group(1) if tt_m else "default").lower()
    score = _QUALITY_ORDER.get(tt, 1)
    if "_hd15" in video_url or "photo-video-mz" in video_url:
        score = max(score, _QUALITY_ORDER["hd15"])
    return (score, len(video_url))


def _pick_best_urls(html: str) -> list[str]:
    urls = set(re.findall(r'https://[^"\\]+\.mp4[^"\\]*', html))
    if not urls:
        return []
    ranked = sorted(urls, key=_quality_key, reverse=True)
    best = _quality_key(ranked[0])[0]
    return [u for u in ranked if _quality_key(u)[0] == best]


def _build_formats(urls: list[str]) -> list[VideoFormat]:
    items: list[VideoFormat] = []
    seen: set[str] = set()
    for idx, video_url in enumerate(urls):
        base = video_url.split("?", 1)[0]
        if base in seen:
            continue
        seen.add(base)
        score, _ = _quality_key(video_url)
        if score >= _QUALITY_ORDER["hd15"]:
            label, height = "高清 · MP4", 1080
        elif score >= _QUALITY_ORDER["b"]:
            label, height = "标清 · MP4", 720
        else:
            label, height = "默认 · MP4", 480
        if idx > 0:
            label = f"{label} · 线路{idx + 1}"
        items.append(VideoFormat(format_id=video_url, label=label, height=height, ext="mp4"))
    return items


def _parse_title(html: str) -> str:
    user_m = re.search(r'"userName":"([^"]+)"', html)
    user = user_m.group(1) if user_m else ""
    cap_m = re.search(r'"caption":"((?:\\.|[^"\\])*)"', html)
    caption = ""
    if cap_m:
        try:
            caption = json.loads(f'"{cap_m.group(1)}"')
        except json.JSONDecodeError:
            caption = cap_m.group(1)
    caption = str(caption).strip()
    if caption and caption != "...":
        return f"{user} · {caption}" if user else caption
    return f"{user} · 快手作品" if user else "快手视频"


def _parse_duration(html: str) -> int:
    m = re.search(r'"duration":(\d+)', html)
    if not m:
        return 0
    ms = int(m.group(1))
    return ms // 1000 if ms > 1000 else ms


def _parse_mobile_html(html: str) -> _KsVideo:
    urls = _pick_best_urls(html)
    if not urls:
        raise ValueError("页面中未找到可下载的视频地址")
    return _KsVideo(_parse_title(html), _parse_duration(html), tuple(_build_formats(urls)))


def _graphql_fetch(photo_id: str) -> _KsVideo | None:
    query = (
        "query visionVideoDetail($photoId: String, $type: String, $page: String, "
        "$webPageArea: String) { visionVideoDetail(photoId: $photoId, type: $type, "
        "page: $page, webPageArea: $webPageArea) { photo { caption duration photoUrl "
        "manifest { adaptationSet { representation { url backupUrl height qualityLabel } } } } } } }"
    )
    payload = json.dumps(
        {"operationName": "visionVideoDetail", "variables": {"photoId": photo_id, "page": "detail"}, "query": query}
    ).encode()
    headers = {
        **mobile_headers(),
        "Content-Type": "application/json",
        "Origin": "https://www.kuaishou.com",
        "Referer": f"https://www.kuaishou.com/short-video/{photo_id}",
        "Cookie": "kpf=PC_WEB; clientid=3; kpn=KUAISHOU_VISION",
    }
    req = urllib.request.Request("https://www.kuaishou.com/graphql", data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = json.loads(resp.read().decode())
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        logger.warning("快手 GraphQL 备用解析失败: %s", exc)
        return None

    photo = (data.get("data") or {}).get("visionVideoDetail", {}).get("photo") or {}
    urls: list[str] = []
    if photo.get("photoUrl"):
        urls.append(str(photo["photoUrl"]))
    for ad in (photo.get("manifest") or {}).get("adaptationSet") or []:
        for rep in ad.get("representation") or []:
            for key in ("url", "backupUrl"):
                u = str(rep.get(key) or "")
                if u and u not in urls:
                    urls.append(u)
    if not urls:
        return None
    duration = int(photo.get("duration") or 0)
    if duration > 1000:
        duration //= 1000
    return _KsVideo(str(photo.get("caption") or "快手视频"), duration, tuple(_build_formats(urls)))
