"""各平台解析适配器。"""

from videodown.core.platforms.registry import all_adapters, download_video_temp, parse_video, probe_specs, resolve_adapter

__all__ = [
    "all_adapters",
    "download_video_temp",
    "parse_video",
    "probe_specs",
    "resolve_adapter",
]
