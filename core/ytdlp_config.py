"""
yt-dlp 全局配置：Deno 运行时、Cookie、各平台参数。
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from videodown.core.url_normalize import is_tiktok_url, is_twitter_url, is_xiaohongshu_url

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_CONFIG_DIR = Path(os.environ.get("VIDEODOWN_CONFIG_DIR", str(_PROJECT_ROOT / "config")))
_YT_COOKIE = _CONFIG_DIR / "youtube_cookies.txt"
_XHS_COOKIE = _CONFIG_DIR / "xiaohongshu_cookies.txt"
_OPTIONAL_XHS_PROBE = _CONFIG_DIR / "xhs_probe_url.txt"


def cookie_has_key(cookie_file: Path, key: str) -> bool:
    """检查 Netscape Cookie 文件是否包含指定键。"""
    if not cookie_file.exists():
        return False
    try:
        text = cookie_file.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return f"\t{key}\t" in text


def xhs_cookie_ready() -> bool:
    return _XHS_COOKIE.exists() and cookie_has_key(_XHS_COOKIE, "web_session")


def youtube_cookie_ready() -> bool:
    return _YT_COOKIE.exists() and cookie_has_key(_YT_COOKIE, "LOGIN_INFO")


def optional_xhs_probe_url() -> str:
    """可选：管理员在 config/xhs_probe_url.txt 放入最新小红书视频分享链接。"""
    try:
        return _OPTIONAL_XHS_PROBE.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def _deno_path() -> str | None:
    for candidate in (
        Path("/home/admin/.deno/bin/deno"),
        Path.home() / ".deno" / "bin" / "deno",
        Path("/usr/bin/deno"),
        Path("/usr/local/bin/deno"),
    ):
        if candidate.exists():
            return str(candidate)
    return None


def _apply_platform_opts(url: str, opts: dict[str, Any], *, use_youtube_cookie: bool = True) -> None:
    if is_xiaohongshu_url(url):
        if _XHS_COOKIE.exists():
            opts["cookiefile"] = str(_XHS_COOKIE)
        return
    if is_twitter_url(url):
        # 访客模式：syndication 无需登录；传 Cookie 会强制走 graphql 并易失败
        opts["extractor_args"] = {"twitter": {"api": ["syndication"]}}
        return
    if use_youtube_cookie and _YT_COOKIE.exists():
        opts["cookiefile"] = str(_YT_COOKIE)


def base_opts(url: str = "", *, use_youtube_cookie: bool = True, **extra: Any) -> dict[str, Any]:
    """构建 yt-dlp 通用选项。"""
    opts: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
    }
    deno = _deno_path()
    if deno:
        opts["js_runtimes"] = {"deno": {"path": deno}}
        opts["remote_components"] = ["ejs:npm", "ejs:github"]
    if url:
        _apply_platform_opts(url, opts, use_youtube_cookie=use_youtube_cookie)
    opts.update(extra)
    return opts


def friendly_error(raw: str, url: str = "") -> str:
    """将 yt-dlp 英文错误转为用户可读的说明。"""
    lower = raw.lower()
    xhs = is_xiaohongshu_url(url) or "xiaohongshu" in lower

    if xhs and ("404" in lower or "unsupported url" in lower):
        return "小红书分享链接已过期，请从小红书 App 重新复制最新口令后再试。"

    if xhs and (
        "no video formats" in lower
        or "unable to extract initial state" in lower
        or raw.strip() in ("", "AssertionError")
    ):
        if xhs_cookie_ready():
            return (
                "小红书解析失败：该笔记可能是图文，或分享口令已过期。"
                "请重新复制完整分享文案；若仍失败请更新服务器 Cookie。"
            )
        return (
            "小红书需要登录 Cookie 才能解析（访客无需自行登录，由服务器统一配置）。"
            f"请管理员上传 Cookie 到 {_XHS_COOKIE}。"
        )

    if "sign in to confirm" in lower or "not a bot" in lower:
        if youtube_cookie_ready():
            return (
                "YouTube 解析失败：Cookie 可能已过期，或该视频需登录观看。"
                "请管理员更新 youtube_cookies.txt 后重试。"
            )
        return (
            "YouTube 无法解析：服务器 IP 被判定为机器人。"
            f"需管理员上传 Cookie 到 {_YT_COOKIE}。"
        )
    if "bilibili" in lower and "412" in lower:
        return "B站暂时无法从此服务器解析（网络限制 412），请稍后重试或使用抖音链接。"
    if ("twitter" in lower or is_twitter_url(url)) and "no video could be found" in lower:
        return "该推文没有视频（可能是纯图文帖），请粘贴带视频的 X/推特 分享链接。"
    if is_tiktok_url(url) or "tiktok" in lower:
        if "ip address is blocked" in lower:
            return "TikTok 官方接口限制了服务器 IP，请使用完整 /video/ 链接重试。"
        if "无法识别" in raw or "短链" in raw:
            return raw
    if "javascript runtime" in lower or "ejs" in lower:
        return "YouTube 需要 Deno 运行时，请联系管理员在服务器安装 Deno。"
    if "no video formats" in lower:
        return "未能提取到视频格式：可能是图文笔记、链接过期，或需要登录 Cookie。"
    return raw
