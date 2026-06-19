"""
桌面环境集成：启动通知、忙碌光标修复。
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

_startup_id: str | None = os.environ.pop("DESKTOP_STARTUP_ID", None)


def capture_startup_id() -> None:
    """启动时接管 DESKTOP_STARTUP_ID，避免子进程继承。"""
    global _startup_id
    if _startup_id is None:
        _startup_id = os.environ.pop("DESKTOP_STARTUP_ID", None)


def notify_startup_complete() -> None:
    """告知桌面环境窗口已就绪，停止启动阶段的忙碌光标。"""
    global _startup_id
    try:
        import gi

        gi.require_version("Gdk", "3.0")
        from gi.repository import Gdk

        Gdk.notify_startup_complete()
        _startup_id = None
        return
    except Exception as exc:
        logger.debug("Gdk 启动通知不可用: %s", exc)

    _startup_id = None
    os.environ.pop("DESKTOP_STARTUP_ID", None)
