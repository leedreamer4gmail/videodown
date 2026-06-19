"""清晰度展示文案。"""

from __future__ import annotations


def human_size(num: int | None) -> str:
    if not num:
        return ""
    size = float(num)
    for unit in ("B", "KB", "MB", "GB"):
        if size < 1024 or unit == "GB":
            return f"{size:.1f}{unit}" if unit != "B" else f"{int(size)}B"
        size /= 1024
    return f"{num}B"


def codec_label(vcodec: str) -> str:
    lower = vcodec.lower()
    if "h264" in lower or "avc" in lower:
        return "H.264"
    if "h265" in lower or "hevc" in lower or "bytevc" in lower:
        return "H.265"
    if "vp9" in lower:
        return "VP9"
    if "av01" in lower:
        return "AV1"
    return "视频"


def note_label(note: str) -> str:
    if not note:
        return ""
    if "watermark" in note.lower() or "水印" in note:
        return "水印"
    if "direct" in note.lower():
        return "直链"
    if "playback" in note.lower():
        return "播放"
    return ""
