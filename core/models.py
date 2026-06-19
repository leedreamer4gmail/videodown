"""解析与下载共用的数据结构。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VideoFormat:
    """可选清晰度条目。"""

    format_id: str
    label: str
    height: int
    ext: str
    filesize: int | None = None


@dataclass(frozen=True)
class ParseResult:
    """解析结果。"""

    url: str
    title: str
    duration: int
    formats: tuple[VideoFormat, ...]
    extractor: str = ""
    error: str = ""


@dataclass(frozen=True)
class DownloadResult:
    """单次下载结果。"""

    url: str
    success: bool
    title: str = ""
    filepath: str = ""
    error: str = ""


def empty_parse(url: str, error: str, *, extractor: str = "") -> ParseResult:
    return ParseResult(url=url, title="", duration=0, formats=(), error=error, extractor=extractor)
