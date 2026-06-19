"""TikTok 平台适配器。"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from videodown.core.formats.labels import human_size
from videodown.core.http.curl_client import DEFAULT_IMPERSONATE, new_session
from videodown.core.models import ParseResult, VideoFormat, empty_parse
from videodown.core.platforms.base import PlatformAdapter, ProbeSpec
from videodown.core.url_normalize import is_tiktok_url

logger = logging.getLogger(__name__)

_VIDEO_ID_RE = re.compile(r"/video/(\d{8,})")
_FORMAT_PREFIX = "tt:"


class TikTokPlatform(PlatformAdapter):
    slug = "tiktok"

    def matches(self, url: str) -> bool:
        return is_tiktok_url(url)

    def probe_spec(self) -> ProbeSpec:
        return ProbeSpec(
            "TikTok",
            "https://www.tiktok.com/@pokemonlife22/video/7059698374567611694",
            6,
        )

    def owns_format_id(self, format_id: str | None) -> bool:
        return bool(format_id and format_id.startswith(_FORMAT_PREFIX))

    def parse(self, url: str) -> ParseResult:
        try:
            video_id = extract_video_id(url)
            item, _ = _fetch_item_struct(video_id)
            video = item["video"]
            formats = tuple(_build_formats(video_id, video))
            if not formats:
                raise ValueError("未提取到可下载格式")
            return ParseResult(
                url=_canonical_url(video_id),
                title=_build_title(item),
                duration=int(video.get("duration") or item.get("duration") or 0),
                formats=formats,
                extractor=self.slug,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("TikTok 解析失败 %s: %s", url, exc)
            return empty_parse(url, str(exc), extractor=self.slug)

    def download_temp(self, url: str, format_id: str | None, dest: Path) -> Path:
        if not format_id or not self.owns_format_id(format_id):
            raise ValueError("TikTok 下载需要 tt: 格式 ID")
        video_id, kind = _parse_format_token(format_id)
        item, sess = _fetch_item_struct(video_id)
        play_url = _pick_play_url(item["video"], kind)
        resp = sess.get(
            play_url,
            impersonate=DEFAULT_IMPERSONATE,
            timeout=180,
            headers={"Referer": "https://www.tiktok.com/"},
        )
        if resp.status_code != 200 or len(resp.content) < 2048:
            raise RuntimeError("TikTok 视频下载失败，请重新解析后再试")
        if b"<HTML" in resp.content[:32].upper():
            raise RuntimeError("TikTok CDN 拒绝下载，请重新解析链接")
        dest.write_bytes(resp.content)
        return dest


def extract_video_id(url: str) -> str:
    m = _VIDEO_ID_RE.search(url)
    if m:
        return m.group(1)
    try:
        sess = new_session()
        resp = sess.get(url, impersonate=DEFAULT_IMPERSONATE, timeout=25, allow_redirects=True)
        for text in (str(resp.url), resp.text):
            m2 = _VIDEO_ID_RE.search(text)
            if m2:
                return m2.group(1)
    except Exception as exc:  # noqa: BLE001
        logger.warning("TikTok 短链解析失败 %s: %s", url, exc)
    raise ValueError("无法识别 TikTok 视频 ID。请粘贴带 /video/数字 的完整链接（vm.tiktok.com 短链可能失效）")


def _canonical_url(video_id: str) -> str:
    return f"https://www.tiktok.com/video/{video_id}"


def _format_token(video_id: str, kind: str) -> str:
    return f"{_FORMAT_PREFIX}{video_id}:{kind}"


def _parse_format_token(format_id: str) -> tuple[str, str]:
    body = format_id[len(_FORMAT_PREFIX) :]
    video_id, _, kind = body.partition(":")
    if not video_id or not kind:
        raise ValueError("无效的 TikTok format_id")
    return video_id, kind


def _fetch_item_struct(video_id: str) -> tuple[dict[str, Any], Any]:
    sess = new_session()
    url = f"https://m.tiktok.com/v/{video_id}.html"
    resp = sess.get(url, impersonate=DEFAULT_IMPERSONATE, timeout=25, allow_redirects=True)
    m = re.search(
        r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">(.*?)</script>',
        resp.text,
    )
    if not m:
        raise ValueError("TikTok 页面无视频数据（链接无效或地区限制）")
    detail = json.loads(m.group(1)).get("__DEFAULT_SCOPE__", {}).get("webapp.video-detail") or {}
    code = detail.get("statusCode")
    if code is not None and int(code) != 0:
        raise ValueError(f"TikTok 无法访问该视频（{detail.get('statusMsg') or 'unknown'}）")
    item = (detail.get("itemInfo") or {}).get("itemStruct") or {}
    if not item.get("video"):
        raise ValueError("该链接不是可下载的 TikTok 视频")
    return item, sess


def _sorted_bitrates(video: dict[str, Any]) -> list[dict[str, Any]]:
    infos = list(video.get("bitrateInfo") or [])
    infos.sort(
        key=lambda b: (int((b.get("PlayAddr") or {}).get("Height") or 0), int(b.get("Bitrate") or 0)),
        reverse=True,
    )
    return infos


def _pick_play_url(video: dict[str, Any], kind: str) -> str:
    if kind == "dl":
        url = str(video.get("downloadAddr") or "")
        if url:
            return url
    if kind == "play":
        return str(video.get("playAddr") or "")
    if kind.startswith("b"):
        idx = int(kind[1:] or "0")
        infos = _sorted_bitrates(video)
        if idx < 0 or idx >= len(infos):
            raise ValueError("清晰度选项已失效，请重新解析")
        urls = (infos[idx].get("PlayAddr") or {}).get("UrlList") or []
        if urls:
            return str(urls[0])
    raise ValueError("未找到对应清晰度的播放地址")


def _build_formats(video_id: str, video: dict[str, Any]) -> list[VideoFormat]:
    items: list[VideoFormat] = []
    if video.get("downloadAddr"):
        items.append(
            VideoFormat(
                format_id=_format_token(video_id, "dl"),
                label="推荐 · 无水印 · MP4",
                height=int(video.get("height") or 0),
                ext="mp4",
            )
        )
    for idx, info in enumerate(_sorted_bitrates(video)):
        play = info.get("PlayAddr") or {}
        height = int(play.get("Height") or 0)
        gear = str(info.get("GearName") or f"档位{idx}")
        bitrate = int(info.get("Bitrate") or 0)
        size = int(play.get("DataSize") or 0) if play.get("DataSize") else None
        label = f"{height}p · {gear} · MP4" if height else f"{gear} · MP4"
        if bitrate:
            label += f" · {bitrate // 1000}kbps"
        if size:
            label += f" · {human_size(size)}"
        items.append(
            VideoFormat(format_id=_format_token(video_id, f"b{idx}"), label=label, height=height, ext="mp4", filesize=size)
        )
    if not items and video.get("playAddr"):
        items.append(
            VideoFormat(
                format_id=_format_token(video_id, "play"),
                label="默认 · MP4",
                height=int(video.get("height") or 0),
                ext="mp4",
            )
        )
    return items


def _build_title(item: dict[str, Any]) -> str:
    author = (item.get("author") or {}).get("nickname") or ""
    desc = str(item.get("desc") or "").strip()
    if desc and desc != "...":
        return f"{author} · {desc}" if author else desc
    return f"{author} · TikTok" if author else "TikTok 视频"
