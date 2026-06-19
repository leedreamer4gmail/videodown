"""
跨平台默认路径与 yt-dlp 可用性检测。
"""

from __future__ import annotations

import platform
import shutil
import sys
from pathlib import Path


def default_download_dir() -> Path:
    """返回各平台默认下载目录。"""
    system = platform.system().lower()
    home = Path.home()
    if system == "windows":
        return home / "Downloads" / "videodown"
    if system == "darwin":
        return home / "Downloads" / "videodown"
    return home / "Downloads" / "videodown"


def resolve_ytdlp() -> str:
    """确认 yt-dlp 可导入，否则抛出 RuntimeError。"""
    if shutil.which("yt-dlp"):
        return "yt-dlp"
    try:
        import yt_dlp  # noqa: F401
    except ImportError as exc:
        raise RuntimeError(
            "未找到 yt-dlp，请先运行: pip install -r requirements.txt"
        ) from exc
    return sys.executable
