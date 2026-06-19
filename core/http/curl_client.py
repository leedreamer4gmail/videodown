"""curl_cffi 会话（TikTok 等反爬站点）。"""

from __future__ import annotations

from typing import Any

DEFAULT_IMPERSONATE = "safari18_0"


def new_session() -> Any:
    from curl_cffi import requests as cr

    return cr.Session()


def get_text(url: str, *, session: Any | None = None, impersonate: str = DEFAULT_IMPERSONATE, timeout: int = 25) -> tuple[str, Any]:
    from curl_cffi import requests as cr

    if session is None:
        resp = cr.get(url, impersonate=impersonate, timeout=timeout, allow_redirects=True)
        return resp.text, session
    resp = session.get(url, impersonate=impersonate, timeout=timeout, allow_redirects=True)
    return resp.text, session
