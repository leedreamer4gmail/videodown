"""站点公开 URL 与 SEO 常量。"""

from __future__ import annotations

import os

SITE_BASE = os.environ.get("VIDEODOWN_SITE_URL", "https://leedreamer.cn/videodown").rstrip("/")
SITE_NAME = "VideoDown"
SITE_NAME_ZH = "VideoDown 视频下载"
CONTACT_EMAIL = os.environ.get("VIDEODOWN_CONTACT_EMAIL", "admin@leedreamer.cn")
