"""
VideoDown Web API 与静态页面服务。

下载采用流式传输：视频经服务器转发，直接保存到用户浏览器本机，不在服务器落盘。
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Any
from urllib.parse import quote, urlencode

from fastapi import FastAPI, Form, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse, RedirectResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from videodown.core.downloader import download_video_temp, extract_urls, parse_video
from videodown.core.platform_probe import probe_platforms
from videodown.core.transcribe import transcribe_video
from videodown.web.geo import should_auto_redirect_en, suggest_locale
from videodown.web.seo import LLMS_TXT, ROBOTS_TXT, sitemap_xml
from videodown.web.site_config import SITE_BASE

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app = FastAPI(title="VideoDown", version="1.2.0")


class ParseRequest(BaseModel):
    text: str = Field(min_length=1)


class TranscribeRequest(BaseModel):
    url: str = Field(min_length=8)
    format_id: str | None = None


def _safe_filename(name: str, ext: str = "mp4") -> str:
    cleaned = re.sub(r"[^\w\u4e00-\u9fff.\- ()\[\]]+", "_", name).strip("._")
    base = cleaned or "video"
    if not base.lower().endswith(f".{ext}"):
        base = f"{base}.{ext}"
    return base


def _ascii_filename(name: str, ext: str = "mp4") -> str:
    """HTTP 头 filename= 仅允许 latin-1，中文标题用 ASCII 回退名。"""
    stem = Path(name).stem if "." in name else name
    ascii_stem = re.sub(r"[^A-Za-z0-9._\- ()\[\]]+", "_", stem).strip("._") or "video"
    return f"{ascii_stem}.{ext}"


def _content_disposition(filename: str, ext: str) -> str:
    ascii_name = _ascii_filename(filename, ext)
    encoded = quote(filename)
    return f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{encoded}"


def _media_type(ext: str) -> str:
    mapping = {
        "mp4": "video/mp4",
        "webm": "video/webm",
        "mkv": "video/x-matroska",
        "m4a": "audio/mp4",
        "mp3": "audio/mpeg",
    }
    return mapping.get(ext.lower(), "application/octet-stream")


def _redirect_en_if_needed(request: Request) -> RedirectResponse | None:
    """欧美 IP 首访无语言偏好时跳转英文版。"""
    path = request.url.path.rstrip("/") or "/"
    if request.method != "GET" or path not in ("", "/", "/index.html"):
        return None
    if not should_auto_redirect_en(request):
        return None
    base = str(request.url).split("?")[0]
    qs = urlencode({"lang": "en"})
    return RedirectResponse(url=f"{base}?{qs}", status_code=302)


@app.middleware("http")
async def locale_geo_redirect(request: Request, call_next: Any) -> Any:
    redirect = _redirect_en_if_needed(request)
    if redirect is not None:
        return redirect
    return await call_next(request)


@app.get("/api/bootstrap")
def api_bootstrap(request: Request) -> dict[str, Any]:
    """前端初始化：推荐语言与站点根 URL。"""
    return {
        "suggested_locale": suggest_locale(request),
        "site_base": SITE_BASE,
        "auto_redirect_en": should_auto_redirect_en(request),
    }


@app.get("/robots.txt", include_in_schema=False)
def robots_txt() -> PlainTextResponse:
    return PlainTextResponse(ROBOTS_TXT, media_type="text/plain; charset=utf-8")


@app.get("/sitemap.xml", include_in_schema=False)
def sitemap() -> Response:
    return Response(
        content=sitemap_xml(),
        media_type="application/xml; charset=utf-8",
    )


@app.get("/llms.txt", include_in_schema=False)
def llms_txt() -> PlainTextResponse:
    """AIO：供 LLM / AI 爬虫理解的站点摘要。"""
    return PlainTextResponse(LLMS_TXT, media_type="text/plain; charset=utf-8")


@app.post("/api/parse")
def api_parse(body: ParseRequest) -> dict[str, Any]:
    urls = extract_urls(body.text)
    if not urls:
        raise HTTPException(status_code=400, detail="未检测到有效链接")
    result = parse_video(urls[0])
    if result.error:
        raise HTTPException(status_code=400, detail=result.error)
    return {
        "url": result.url,
        "title": result.title,
        "duration": result.duration,
        "extractor": result.extractor,
        "formats": [
            {
                "format_id": f.format_id,
                "label": f.label,
                "height": f.height,
                "ext": f.ext,
                "filesize": f.filesize,
            }
            for f in result.formats
        ],
    }


@app.post("/api/transcribe")
def api_transcribe(body: TranscribeRequest) -> dict[str, str]:
    """视频语音转文字（自动字幕或 Whisper）。"""
    try:
        text = transcribe_video(body.url, body.format_id)
    except Exception as exc:  # noqa: BLE001
        logger.warning("语音识别失败: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    if not text.strip():
        raise HTTPException(status_code=404, detail="未识别到语音内容")
    return {"transcript": text}


@app.get("/api/platforms")
def api_platforms() -> dict[str, Any]:
    """实时探测各平台解析能力（每次请求重新实测）。"""
    return probe_platforms()


def _build_stream_response(
    url: str,
    title: str,
    ext: str,
    format_id: str | None,
) -> StreamingResponse:
    filename = _safe_filename(title, ext)
    tmp: Path | None = None
    try:
        tmp = download_video_temp(url, format_id)
        size = tmp.stat().st_size
    except Exception as exc:  # noqa: BLE001
        logger.warning("下载准备失败: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    path = tmp

    def _generate() -> Any:
        try:
            with path.open("rb") as handle:
                while chunk := handle.read(64 * 1024):
                    yield chunk
        finally:
            path.unlink(missing_ok=True)

    headers = {
        "Content-Disposition": _content_disposition(filename, ext),
        "Content-Length": str(size),
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
        "Accept-Ranges": "bytes",
    }
    return StreamingResponse(
        _generate(),
        media_type=_media_type(ext),
        headers=headers,
    )


@app.get("/api/stream")
def api_stream_get(
    url: str = Query(min_length=8),
    format_id: str | None = Query(default=None),
    title: str = Query(default="video"),
    ext: str = Query(default="mp4"),
) -> StreamingResponse:
    """流式下载（GET，适合短链接）。"""
    return _build_stream_response(url, title, ext, format_id)


@app.post("/api/stream")
def api_stream_post(
    url: str = Form(..., min_length=8),
    title: str = Form(default="video"),
    ext: str = Form(default="mp4"),
    format_id: str | None = Form(default=None),
) -> StreamingResponse:
    """流式下载（POST 表单，适合手机与超长小红书链接）。"""
    return _build_stream_response(url, title, ext, format_id or None)


app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
