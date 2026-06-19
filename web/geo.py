"""
访客地区识别：用于默认语言推荐与欧美自动跳转。
"""

from __future__ import annotations

from fastapi import Request

# 北美、西欧、大洋洲等主要英语/欧美市场
_WESTERN_COUNTRIES: frozenset[str] = frozenset(
    {
        "US",
        "CA",
        "GB",
        "UK",
        "AU",
        "NZ",
        "DE",
        "FR",
        "IT",
        "ES",
        "NL",
        "BE",
        "SE",
        "NO",
        "DK",
        "FI",
        "IE",
        "AT",
        "CH",
        "PT",
        "PL",
        "CZ",
        "LU",
        "IS",
    }
)

# 华人地区优先中文
_CHINESE_PREFERRED: frozenset[str] = frozenset({"TW", "HK", "MO", "CN", "SG"})


def country_code(request: Request) -> str | None:
    """从 CDN / 反向代理头读取 ISO 国家码。"""
    for key in (
        "CF-IPCountry",
        "X-Vercel-IP-Country",
        "CloudFront-Viewer-Country",
        "X-Country-Code",
    ):
        raw = request.headers.get(key, "").strip().upper()
        if raw and raw not in ("XX", "T1", "UNKNOWN"):
            return raw
    return None


def suggest_locale(request: Request) -> str:
    """
    推荐界面语言：zh | en。
    欧美 IP → en；华人地区 → zh；其余看 Accept-Language。
    """
    cc = country_code(request)
    if cc in _CHINESE_PREFERRED:
        return "zh"
    if cc and cc in _WESTERN_COUNTRIES and cc not in _CHINESE_PREFERRED:
        return "en"
    accept = request.headers.get("Accept-Language", "").lower()
    if accept.startswith("zh"):
        return "zh"
    if any(accept.startswith(p) for p in ("en", "de", "fr", "es", "it", "pt", "nl")):
        return "en"
    return "zh"


def should_auto_redirect_en(request: Request) -> bool:
    """首次访问且无语言偏好时，欧美访客跳转英文版。"""
    if request.cookies.get("vd_lang"):
        return False
    if request.query_params.get("lang"):
        return False
    cc = country_code(request)
    if cc in _CHINESE_PREFERRED:
        return False
    if cc and cc in _WESTERN_COUNTRIES:
        return True
    # 无国家码时根据浏览器语言
    accept = request.headers.get("Accept-Language", "").lower()
    return accept.startswith("en") and not accept.startswith("zh")
