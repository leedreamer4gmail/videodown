"""yt-dlp 通用平台：抖音 / YouTube / B站 / 小红书 / X 等。"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import yt_dlp

from videodown.core.formats.ytdlp_collect import collect_ytdlp_formats
from videodown.core.models import ParseResult, empty_parse
from videodown.core.platforms.base import PlatformAdapter, ProbeSpec
from videodown.core.url_normalize import (
    is_twitter_url,
    is_xiaohongshu_url,
    is_youtube_url,
    normalize_video_url,
)
from videodown.core.ytdlp_config import _XHS_COOKIE, _YT_COOKIE, _deno_path, base_opts, friendly_error

logger = logging.getLogger(__name__)

_PROBE_URLS: tuple[tuple[str, str, int, bool], ...] = (
    ("抖音", "https://v.douyin.com/ndbUluzN0OA/", 0, False),
    ("YouTube", "https://www.youtube.com/watch?v=dQw4w9WgXcQ", 2, False),
    ("B站", "https://www.bilibili.com/video/BV1GJ411x7h7", 3, False),
    ("X", "https://x.com/i/status/2022969777736597586", 5, False),
)


def _is_bot_error(msg: str) -> bool:
    lower = msg.lower()
    return "sign in to confirm" in lower or "not a bot" in lower


def _ytdlp_executable() -> str:
    candidate = Path(sys.executable).parent / "yt-dlp"
    return str(candidate) if candidate.exists() else "yt-dlp"


def build_stream_cmd(url: str, format_id: str | None, output: str) -> tuple[list[str], dict[str, str]]:
    norm_url = normalize_video_url(url)
    cmd = [
        _ytdlp_executable(),
        "-f",
        format_id or "bestvideo+bestaudio/best",
        "-o",
        output,
        "--no-warnings",
        "--quiet",
        "--no-progress",
    ]
    if output != "-":
        cmd += ["--merge-output-format", "mp4", "--no-part"]
    deno = _deno_path()
    if deno and is_youtube_url(norm_url):
        cmd += ["--js-runtimes", f"deno:{deno}", "--remote-components", "ejs:npm", "ejs:github"]
    if is_youtube_url(norm_url) and _YT_COOKIE.exists():
        cmd += ["--cookies", str(_YT_COOKIE)]
    elif is_xiaohongshu_url(norm_url):
        if _XHS_COOKIE.exists():
            cmd += ["--cookies", str(_XHS_COOKIE)]
        cmd += ["--impersonate", "chrome"]
    elif is_twitter_url(norm_url):
        cmd += ["--extractor-args", "twitter:api=syndication"]
    cmd.append(norm_url)
    env = os.environ.copy()
    if deno:
        env["PATH"] = f"{Path(deno).parent}:{env.get('PATH', '')}"
    return cmd, env


class YtdlpPlatform(PlatformAdapter):
    """默认后端：凡未被专用适配器接管的链接均走 yt-dlp。"""

    slug = "ytdlp"

    def matches(self, url: str) -> bool:
        return True

    def parse(self, url: str) -> ParseResult:
        norm = normalize_video_url(url)
        if is_youtube_url(norm) and _YT_COOKIE.exists():
            with_cookie = self._parse_once(norm, use_youtube_cookie=True)
            if not with_cookie.error:
                return with_cookie
            if _is_bot_error(with_cookie.error):
                without = self._parse_once(norm, use_youtube_cookie=False)
                if not without.error:
                    return without
            return with_cookie
        return self._parse_once(norm, use_youtube_cookie=True)

    def download_temp(self, url: str, format_id: str | None, dest: Path) -> Path:
        tmpdir = Path(tempfile.mkdtemp(prefix="vd_"))
        outtmpl = str(tmpdir / "video.%(ext)s")
        cmd, env = build_stream_cmd(url, format_id, outtmpl)
        try:
            proc = subprocess.run(cmd, env=env, capture_output=True, check=False)
            candidates = [p for p in tmpdir.iterdir() if p.is_file() and p.stat().st_size > 1024]
            if proc.returncode != 0 or not candidates:
                err = (proc.stderr or b"").decode(errors="replace").strip()
                shutil.rmtree(tmpdir, ignore_errors=True)
                raise RuntimeError(
                    friendly_error(err or f"yt-dlp 退出码 {proc.returncode}", normalize_video_url(url))
                )
            video = max(candidates, key=lambda p: p.stat().st_size)
            shutil.move(str(video), str(dest))
            shutil.rmtree(tmpdir, ignore_errors=True)
            return dest
        except Exception:
            shutil.rmtree(tmpdir, ignore_errors=True)
            raise

    def _parse_once(self, norm_url: str, *, use_youtube_cookie: bool) -> ParseResult:
        opts = base_opts(url=norm_url, skip_download=True, use_youtube_cookie=use_youtube_cookie)
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(norm_url, download=False)
            if info is None:
                return empty_parse(norm_url, "无法解析该链接")
            formats = tuple(collect_ytdlp_formats(info))
            if not formats:
                return empty_parse(norm_url, friendly_error("no video formats found", norm_url))
            return ParseResult(
                url=norm_url,
                title=str(info.get("title") or "未知标题"),
                duration=int(info.get("duration") or 0),
                formats=formats,
                extractor=str(info.get("extractor") or info.get("extractor_key") or ""),
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("yt-dlp 解析失败 %s: %s", norm_url, exc)
            msg = str(exc).strip() or exc.__class__.__name__
            return empty_parse(norm_url, friendly_error(msg, norm_url))


class YtdlpProbePlatform(YtdlpPlatform):
    """带探测配置的 yt-dlp 子平台（仅用于 probe_spec）。"""

    def __init__(self, name: str, url: str, order: int, requires_cookie: bool = False) -> None:
        self._name = name
        self._url = url
        self._order = order
        self._requires_cookie = requires_cookie

    def matches(self, url: str) -> bool:
        return False

    def parse(self, url: str) -> ParseResult:
        return empty_parse(url, "probe-only adapter")

    def probe_spec(self) -> ProbeSpec:
        return ProbeSpec(self._name, self._url, self._order, self._requires_cookie)


def ytdlp_probe_adapters() -> list[YtdlpProbePlatform]:
    return [YtdlpProbePlatform(n, u, o, rc) for n, u, o, rc in _PROBE_URLS]
