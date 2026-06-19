"""移动端 UA、Cookie 跳转抓取。"""

from __future__ import annotations

import http.cookiejar
import urllib.request

MOBILE_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
)


def mobile_headers(*, referer: str = "") -> dict[str, str]:
    headers = {
        "User-Agent": MOBILE_UA,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9",
    }
    if referer:
        headers["Referer"] = referer
    return headers


def mobile_opener() -> urllib.request.OpenerDirector:
    jar = http.cookiejar.CookieJar()
    return urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(jar),
        urllib.request.HTTPRedirectHandler(),
    )


def fetch_with_cookies(url: str, *, timeout: int = 25) -> tuple[str, str]:
    """返回 (最终 URL, HTML 文本)。"""
    opener = mobile_opener()
    req = urllib.request.Request(url, headers=mobile_headers())
    with opener.open(req, timeout=timeout) as resp:
        return resp.url, resp.read().decode("utf-8", errors="replace")


def follow_redirects(url: str, *, timeout: int = 20) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": MOBILE_UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.url
