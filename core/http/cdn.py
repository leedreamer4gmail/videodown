"""CDN 直链下载。"""

from __future__ import annotations

import urllib.request
from pathlib import Path

from videodown.core.http.mobile import mobile_headers, mobile_opener

_MIN_BYTES = 1024


def download_url_to_file(
    video_url: str,
    dest: Path,
    *,
    referer: str = "",
    timeout: int = 180,
    opener: urllib.request.OpenerDirector | None = None,
) -> Path:
    out = Path(dest)
    client = opener or mobile_opener()
    req = urllib.request.Request(video_url, headers=mobile_headers(referer=referer))
    with client.open(req, timeout=timeout) as resp:
        out.write_bytes(resp.read())
    if out.stat().st_size < _MIN_BYTES:
        raise RuntimeError("下载文件过小，可能链接已过期")
    return out
