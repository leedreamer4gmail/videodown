"""从 yt-dlp info_dict 汇总清晰度列表。"""

from __future__ import annotations

from typing import Any

from videodown.core.formats.labels import codec_label, human_size, note_label
from videodown.core.models import VideoFormat


def stream_format_id(fmt: dict[str, Any]) -> str:
    fid = str(fmt.get("format_id") or "")
    if not fid:
        return "bestvideo+bestaudio/best"
    if fmt.get("acodec", "none") != "none":
        return fid
    return f"{fid}+bestaudio"


def _youtube_score(fmt: dict[str, Any]) -> tuple[int, int, float]:
    has_audio = 1 if fmt.get("acodec", "none") != "none" else 0
    prefer_mp4 = 1 if str(fmt.get("ext") or "") == "mp4" else 0
    return (has_audio, prefer_mp4, float(fmt.get("tbr") or 0))


def _av_score(fmt: dict[str, Any]) -> tuple[int, int, int, float]:
    has_audio = 1 if fmt.get("acodec", "none") != "none" else 0
    prefer_mp4 = 1 if str(fmt.get("ext") or "") == "mp4" else 0
    prefer_https = 1 if str(fmt.get("protocol") or "") == "https" else 0
    return (has_audio, prefer_mp4, prefer_https, float(fmt.get("tbr") or 0))


def _is_extractor(info: dict[str, Any], keyword: str) -> bool:
    name = str(info.get("extractor") or info.get("extractor_key") or "").lower()
    return keyword in name


def _collect_by_height(
    info: dict[str, Any],
    *,
    audio_tag: str,
    best_label: str,
) -> list[VideoFormat]:
    raw = info.get("formats") or []
    best_by_height: dict[int, dict[str, Any]] = {}
    score_fn = _youtube_score if _is_extractor(info, "youtube") else _av_score

    for fmt in raw:
        if str(fmt.get("format_note") or "").lower() == "storyboard":
            continue
        if str(fmt.get("ext") or "") == "mhtml":
            continue
        if fmt.get("vcodec", "none") == "none":
            continue
        height = int(fmt.get("height") or 0)
        if height <= 0:
            continue
        prev = best_by_height.get(height)
        if prev is None or score_fn(fmt) > score_fn(prev):
            best_by_height[height] = fmt

    items: list[VideoFormat] = []
    for height in sorted(best_by_height, reverse=True):
        fmt = best_by_height[height]
        ext = str(fmt.get("ext") or "mp4")
        codec = codec_label(str(fmt.get("vcodec") or ""))
        size = fmt.get("filesize") or fmt.get("filesize_approx")
        size_int = int(size) if size else None
        has_audio = fmt.get("acodec", "none") != "none"
        parts = [f"{height}p", codec, ext.upper()]
        if not has_audio:
            parts.append(audio_tag)
        if size_int:
            parts.append(human_size(size_int))
        items.append(
            VideoFormat(
                format_id=stream_format_id(fmt),
                label=" · ".join(parts),
                height=height,
                ext="mp4" if has_audio and ext == "mp4" else ext,
                filesize=size_int,
            )
        )

    if items:
        items.insert(
            0,
            VideoFormat(
                format_id="bestvideo+bestaudio/best",
                label=best_label,
                height=items[0].height,
                ext="mp4",
                filesize=items[0].filesize,
            ),
        )
    return items


def collect_ytdlp_formats(info: dict[str, Any]) -> list[VideoFormat]:
    if _is_extractor(info, "youtube"):
        items = _collect_by_height(info, audio_tag="合并音轨", best_label="最佳画质 · 自动")
        if items:
            return items
    if _is_extractor(info, "twitter"):
        items = _collect_by_height(info, audio_tag="含音轨", best_label="最佳画质 · 含音轨")
        if items:
            return items

    raw = info.get("formats") or []
    buckets: dict[tuple[int, str, str], VideoFormat] = {}

    for fmt in raw:
        if fmt.get("vcodec", "none") == "none":
            continue
        height = int(fmt.get("height") or 0)
        ext = str(fmt.get("ext") or "mp4")
        codec = codec_label(str(fmt.get("vcodec") or ""))
        tag = note_label(str(fmt.get("format_note") or ""))
        size = fmt.get("filesize") or fmt.get("filesize_approx")
        size_int = int(size) if size else None
        parts = [f"{height}p" if height else "默认", codec, ext.upper()]
        if tag:
            parts.append(tag)
        if size_int:
            parts.append(human_size(size_int))
        if fmt.get("acodec", "none") == "none":
            parts.append("含音轨")
        candidate = VideoFormat(
            format_id=stream_format_id(fmt),
            label=" · ".join(parts),
            height=height,
            ext=ext,
            filesize=size_int,
        )
        if not candidate.format_id:
            continue
        key = (height, codec, tag)
        prev = buckets.get(key)
        if prev is None or (size_int or 0) > (prev.filesize or 0):
            buckets[key] = candidate

    items = sorted(buckets.values(), key=lambda x: (x.height, x.filesize or 0), reverse=True)
    if items:
        return items

    fid = str(info.get("format_id") or "best")
    ext = str(info.get("ext") or "mp4")
    height = int(info.get("height") or 0)
    res = f"{height}p" if height else "默认"
    return [VideoFormat(format_id=fid, label=f"{res} · {ext.upper()}", height=height, ext=ext)]
