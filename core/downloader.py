"""
视频下载统一入口。

职责：URL 提取、解析调度、临时文件下载、GUI 下载器。
平台实现见 videodown.core.platforms。
"""

from __future__ import annotations

import logging
import re
import subprocess
from pathlib import Path
from typing import Any, Callable

import yt_dlp

from videodown.core.models import DownloadResult, ParseResult, VideoFormat
from videodown.core.platforms.registry import download_video_temp as _download_video_temp
from videodown.core.platforms.registry import parse_video
from videodown.core.platforms.ytdlp_platform import build_stream_cmd
from videodown.core.url_normalize import is_twitter_url, normalize_video_url
from videodown.core.ytdlp_config import base_opts, friendly_error

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[dict[str, Any]], None]
LogCallback = Callable[[str], None]

_URL_PATTERN = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)

# 向后兼容：外部仍可从 downloader 导入类型
__all__ = [
    "DownloadResult",
    "ParseResult",
    "VideoDownloader",
    "VideoFormat",
    "download_video_temp",
    "extract_urls",
    "parse_video",
    "stream_video_chunks",
]


def extract_urls(text: str) -> list[str]:
    return list(dict.fromkeys(_URL_PATTERN.findall(text)))


def download_video_temp(url: str, format_id: str | None = None) -> Path:
    return _download_video_temp(url, format_id)


class VideoDownloader:
    """桌面 GUI：yt-dlp 本机落盘下载。"""

    def __init__(self, output_dir: Path) -> None:
        self._output_dir = output_dir

    def download(
        self,
        url: str,
        format_id: str | None = None,
        on_progress: ProgressCallback | None = None,
        on_log: LogCallback | None = None,
    ) -> DownloadResult:
        self._output_dir.mkdir(parents=True, exist_ok=True)
        title = ""
        filepath = ""

        def _hook(data: dict[str, Any]) -> None:
            nonlocal title, filepath
            status = data.get("status", "")
            if status == "downloading":
                title = str(data.get("info_dict", {}).get("title", title))
            elif status == "finished":
                filepath = str(data.get("filename", ""))
            if on_progress:
                on_progress(data)

        def _logger(msg: str) -> None:
            if on_log:
                on_log(msg)

        opts = base_opts(
            url=url,
            outtmpl=str(self._output_dir / "%(title)s.%(ext)s"),
            progress_hooks=[_hook],
            logger=_YtdlpLogger(_logger),
            merge_output_format="mp4",
        )
        if format_id:
            opts["format"] = format_id
        elif is_twitter_url(url):
            opts["format"] = "bestvideo+bestaudio/best"
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
            if info:
                title = str(info.get("title", title))
            return DownloadResult(url=url, success=True, title=title, filepath=filepath)
        except Exception as exc:  # noqa: BLE001
            logger.warning("下载失败 %s: %s", url, exc)
            return DownloadResult(url=url, success=False, error=friendly_error(str(exc), url))


def stream_video_chunks(url: str, format_id: str | None = None) -> Any:
    cmd, env = build_stream_cmd(url, format_id, "-")
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, env=env)
    if proc.stdout is None:
        raise RuntimeError("无法启动 yt-dlp")
    total = 0
    try:
        while chunk := proc.stdout.read(64 * 1024):
            total += len(chunk)
            yield chunk
        code = proc.wait()
        if code != 0 and total < 1024:
            raise RuntimeError(friendly_error(f"yt-dlp 退出码 {code}", normalize_video_url(url)))
    finally:
        if proc.poll() is None:
            proc.kill()


class _YtdlpLogger:
    def __init__(self, callback: LogCallback) -> None:
        self._callback = callback

    def debug(self, msg: str) -> None:
        pass

    def info(self, msg: str) -> None:
        self._callback(msg)

    def warning(self, msg: str) -> None:
        self._callback(f"⚠ {msg}")

    def error(self, msg: str) -> None:
        self._callback(f"✗ {msg}")
