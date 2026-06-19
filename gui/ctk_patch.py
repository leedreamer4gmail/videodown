"""
关闭 CustomTkinter 在 Linux 上无用的 30ms/100ms 后台轮询。

这些轮询会导致 GNOME 长时间显示忙碌光标，关闭窗口后仍可能持续数秒。
"""

from __future__ import annotations

import sys


def apply_linux_ctk_patches() -> None:
    """禁用 Linux 下 CTk 的主题/DPI 轮询循环。"""
    if not sys.platform.startswith("linux"):
        return

    from customtkinter.windows.widgets.appearance_mode.appearance_mode_tracker import (
        AppearanceModeTracker,
    )
    from customtkinter.windows.widgets.scaling.scaling_tracker import ScalingTracker

    @classmethod
    def _stop_appearance_loop(cls) -> None:
        cls.update_loop_running = False

    @classmethod
    def _stop_scaling_loop(cls) -> None:
        cls.update_loop_running = False

    @classmethod
    def _add_widget_no_loop(cls, widget_callback, widget) -> None:
        window_root = cls.get_window_root_of_widget(widget)
        if window_root not in cls.window_widgets_dict:
            cls.window_widgets_dict[window_root] = [widget_callback]
        else:
            cls.window_widgets_dict[window_root].append(widget_callback)
        if window_root not in cls.window_dpi_scaling_dict:
            cls.window_dpi_scaling_dict[window_root] = 1.0

    @classmethod
    def _add_appearance_no_loop(cls, callback, widget=None) -> None:
        cls.callback_list.append(callback)
        if widget is None:
            return
        app = cls.get_tk_root_of_widget(widget)
        if app not in cls.app_list:
            cls.app_list.append(app)

    AppearanceModeTracker.update = _stop_appearance_loop
    AppearanceModeTracker.add = _add_appearance_no_loop
    ScalingTracker.check_dpi_scaling = _stop_scaling_loop
    ScalingTracker.add_widget = _add_widget_no_loop
    ScalingTracker.deactivate_automatic_dpi_awareness = True
