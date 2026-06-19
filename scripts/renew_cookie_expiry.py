#!/usr/bin/env python3
"""
续期 Netscape Cookie 文件中的过期时间戳。

说明：
- 仅延长文件里的 expiry 字段，防止 yt-dlp/客户端因「本地过期」丢弃 Cookie。
- 无法代替平台侧会话续期；web_session / LOGIN_INFO 被平台作废后，仍需重新上传新 Cookie。
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# 与 Chrome / yt-dlp 导出格式一致的大数过期时间（约 2600+ 年）
_FAR_FUTURE_CHROME = "19999999999999999"
# 标准 Netscape 秒级时间戳（2099 年）
_FAR_FUTURE_UNIX = "4102444800"

_DEFAULT_CONFIG = Path(
    os.environ.get("VIDEODOWN_CONFIG_DIR", "/home/project/videodown/config")
)
_COOKIE_FILES = ("xiaohongshu_cookies.txt", "youtube_cookies.txt")


def _setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def _pick_far_future(sample_expiry: str) -> str:
    exp = sample_expiry.strip()
    if exp.isdigit() and len(exp) >= 12:
        return _FAR_FUTURE_CHROME
    return _FAR_FUTURE_UNIX


def _renew_line(line: str, far_future: str) -> tuple[str, bool]:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return line, False
    parts = line.split("\t")
    if len(parts) < 5:
        return line, False
    old_exp = parts[4].strip()
    if old_exp == far_future:
        return line, False
    parts[4] = far_future
    return "\t".join(parts), True


def renew_cookie_file(path: Path) -> int:
    """续期单个 Cookie 文件，返回更新的条目数。"""
    if not path.exists():
        logging.warning("跳过不存在的文件: %s", path)
        return 0
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise RuntimeError(f"无法读取 {path}: {exc}") from exc

    far_future = _FAR_FUTURE_UNIX
    for line in text.splitlines():
        parts = line.split("\t")
        if len(parts) >= 5 and parts[4].strip().isdigit():
            far_future = _pick_far_future(parts[4])
            break

    updated = 0
    new_lines: list[str] = []
    for line in text.splitlines():
        new_line, changed = _renew_line(line, far_future)
        new_lines.append(new_line)
        if changed:
            updated += 1

    if updated == 0:
        logging.info("%s 无需更新", path.name)
        return 0

    tmp = path.with_suffix(path.suffix + ".tmp")
    try:
        tmp.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
        tmp.chmod(0o600)
        tmp.replace(path)
    except OSError as exc:
        if tmp.exists():
            tmp.unlink(missing_ok=True)
        raise RuntimeError(f"无法写入 {path}: {exc}") from exc

    logging.info("%s 已续期 %d 条 Cookie", path.name, updated)
    return updated


def renew_all(config_dir: Path) -> int:
    total = 0
    for name in _COOKIE_FILES:
        total += renew_cookie_file(config_dir / name)
    return total


def main() -> int:
    parser = argparse.ArgumentParser(description="续期 VideoDown Cookie 文件过期时间")
    parser.add_argument(
        "--config-dir",
        type=Path,
        default=_DEFAULT_CONFIG,
        help="Cookie 配置目录",
    )
    args = parser.parse_args()
    _setup_logging()
    try:
        count = renew_all(args.config_dir)
        logging.info(
            "完成 %s，共续期 %d 条",
            datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
            count,
        )
    except Exception as exc:  # noqa: BLE001
        logging.error("续期失败: %s", exc)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
