"""向后兼容：请改用 videodown.core.platforms.tiktok。"""

from videodown.core.platforms.tiktok import TikTokPlatform, extract_video_id

_platform = TikTokPlatform()
parse_tiktok = _platform.parse
download_tiktok = lambda format_id, dest: _platform.download_temp("", format_id, dest)

__all__ = ["parse_tiktok", "download_tiktok", "extract_video_id", "TikTokPlatform"]
