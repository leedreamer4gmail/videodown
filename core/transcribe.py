"""视频语音转文字：平台自动字幕优先，否则 Whisper 识别音轨。"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

import yt_dlp

from videodown.core.copy import clean_copy, speech_captions_from_info
from videodown.core.downloader import download_video_temp
from videodown.core.url_normalize import normalize_video_url
from videodown.core.ytdlp_config import base_opts

logger = logging.getLogger(__name__)

_MAX_ASR_SEC = int(os.environ.get("VIDEODOWN_ASR_MAX_SEC", "600"))
_WHISPER_MODEL: Any = None


def transcribe_video(url: str, format_id: str | None = None) -> str:
    """将视频语音转为纯文本。"""
    norm = normalize_video_url(url)
    text = _try_platform_speech_captions(norm)
    if text:
        return text
    work = Path(tempfile.mkdtemp(prefix="vd_asr_"))
    audio = work / "audio.mp3"
    try:
        if not _extract_audio(norm, format_id, work, audio):
            return ""
        return _whisper_transcribe(audio)
    finally:
        shutil.rmtree(work, ignore_errors=True)


def _try_platform_speech_captions(url: str) -> str:
    """各平台自动语音字幕（非作者简介）。"""
    opts = base_opts(url=url, skip_download=True)
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=False)
        if info:
            return speech_captions_from_info(info)
    except Exception as exc:  # noqa: BLE001
        logger.info("平台语音字幕不可用 %s: %s", url, exc)
    return ""


def _extract_audio(url: str, format_id: str | None, work: Path, audio: Path) -> bool:
    if _ytdlp_audio(url, audio):
        return audio.exists() and audio.stat().st_size > 512
    video = work / "video.mp4"
    try:
        src = download_video_temp(url, format_id)
        shutil.move(str(src), str(video))
        _ffmpeg_audio(video, audio)
        return audio.exists() and audio.stat().st_size > 512
    except Exception as exc:  # noqa: BLE001
        logger.warning("音轨提取失败 %s: %s", url, exc)
        return False


def _ytdlp_audio(url: str, dest: Path) -> bool:
    work = dest.parent
    template = str(work / "track.%(ext)s")
    opts = base_opts(url=url, skip_download=False)
    opts.update(
        {
            "format": "bestaudio/best",
            "outtmpl": template,
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "64",
                }
            ],
        }
    )
    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            ydl.download([url])
    except Exception as exc:  # noqa: BLE001
        logger.info("yt-dlp 音频提取失败: %s", exc)
        return False
    for candidate in work.glob("track.*"):
        if candidate.suffix.lower() == ".mp3":
            shutil.move(str(candidate), str(dest))
            return True
    return False


def _ffmpeg_audio(video: Path, audio: Path) -> None:
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(video),
        "-vn",
        "-t",
        str(_MAX_ASR_SEC),
        "-acodec",
        "libmp3lame",
        "-q:a",
        "4",
        str(audio),
    ]
    proc = subprocess.run(cmd, capture_output=True, check=False)
    if proc.returncode != 0:
        err = (proc.stderr or b"").decode(errors="replace").strip()
        raise RuntimeError(err or "ffmpeg 提取音轨失败")


def _whisper_transcribe(audio: Path) -> str:
    global _WHISPER_MODEL
    try:
        from faster_whisper import WhisperModel
    except ImportError as exc:
        raise RuntimeError("服务器未安装语音识别组件 faster-whisper") from exc
    if _WHISPER_MODEL is None:
        model_name = os.environ.get("VIDEODOWN_WHISPER_MODEL", "base")
        _WHISPER_MODEL = WhisperModel(model_name, device="cpu", compute_type="int8")
    segments, _ = _WHISPER_MODEL.transcribe(
        str(audio),
        vad_filter=True,
        beam_size=1,
    )
    parts = [seg.text.strip() for seg in segments if seg.text.strip()]
    text = clean_copy(" ".join(parts))
    if not text:
        raise RuntimeError("未识别到语音内容")
    return text
