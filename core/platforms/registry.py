"""平台注册与统一调度。"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from videodown.core.models import ParseResult
from videodown.core.platforms.base import PlatformAdapter, ProbeSpec
from videodown.core.platforms.kuaishou import KuaishouPlatform
from videodown.core.platforms.tiktok import TikTokPlatform
from videodown.core.platforms.ytdlp_platform import YtdlpPlatform, ytdlp_probe_adapters
from videodown.core.url_normalize import normalize_video_url

# 专用适配器优先；ytdlp 兜底（matches 恒为 True，须放最后）
_YTDLP = YtdlpPlatform()
_ADAPTERS: tuple[PlatformAdapter, ...] = (
    KuaishouPlatform(),
    TikTokPlatform(),
    _YTDLP,
)


def all_adapters() -> tuple[PlatformAdapter, ...]:
    return _ADAPTERS


def resolve_adapter(url: str) -> PlatformAdapter:
    norm = normalize_video_url(url)
    for adapter in _ADAPTERS:
        if adapter.matches(norm) or adapter.matches(url):
            return adapter
    return _YTDLP


def parse_video(url: str) -> ParseResult:
    return resolve_adapter(url).parse(url)


def probe_specs() -> list[ProbeSpec]:
    specs: list[ProbeSpec] = []
    for adapter in _ADAPTERS:
        spec = adapter.probe_spec()
        if spec:
            specs.append(spec)
    for probe in ytdlp_probe_adapters():
        spec = probe.probe_spec()
        if spec:
            specs.append(spec)
    specs.sort(key=lambda s: s.order)
    return specs


def download_video_temp(url: str, format_id: str | None = None) -> Path:
    """下载到临时文件（Web 转发后即删）。"""
    fd, raw = tempfile.mkstemp(prefix="vd_", suffix=".mp4")
    os.close(fd)
    dest = Path(raw)
    try:
        for adapter in _ADAPTERS:
            if format_id and adapter.owns_format_id(format_id):
                return adapter.download_temp(url, format_id, dest)
        return resolve_adapter(url).download_temp(url, format_id, dest)
    except Exception:
        dest.unlink(missing_ok=True)
        raise
