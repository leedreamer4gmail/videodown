"""向后兼容：请改用 videodown.core.platforms.kuaishou。"""

from videodown.core.platforms.kuaishou import KuaishouPlatform, extract_photo_id

_platform = KuaishouPlatform()
parse_kuaishou = _platform.parse
download_kuaishou_direct = lambda url, dest: _platform.download_temp("", url, dest)

__all__ = ["parse_kuaishou", "download_kuaishou_direct", "extract_photo_id", "KuaishouPlatform"]
