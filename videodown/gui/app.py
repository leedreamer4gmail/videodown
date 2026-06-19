"""
videodown 桌面主界面。

职责：URL 输入、解析清晰度、目录选择、进度展示、后台下载调度。
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from tkinter import filedialog, messagebox
from typing import Any

import customtkinter as ctk

from videodown.core.desktop import notify_startup_complete
from videodown.core.downloader import (
    DownloadResult,
    ParseResult,
    VideoDownloader,
    VideoFormat,
    extract_urls,
    parse_video,
)
from videodown.core.paths import default_download_dir
from videodown.gui.ctk_patch import apply_linux_ctk_patches

logger = logging.getLogger(__name__)

apply_linux_ctk_patches()
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# === 界面尺寸 ===
_PADX = 36
_PADY = 16
_FONT_TITLE = 16
_FONT_HINT = 11
_FONT_BODY = 12
_FONT_BTN = 12
_FONT_LOG = 11
_FONT_STATUS = 11

_INPUT_BG = "#F5F5F4"
_INPUT_FG = "#1C1917"
_INPUT_BORDER = "#D6D3D1"


class VideoDownApp(ctk.CTk):
    """视频下载器主窗口。"""

    def __init__(self) -> None:
        super().__init__()
        self.title("VideoDown — 视频下载器")
        self.geometry("1180x880")
        self.minsize(1000, 760)

        self._output_dir = default_download_dir()
        self._busy = False
        self._closing = False
        self._parse_anim = False
        self._parse_anim_job: str | None = None
        self._startup_notified = False

        self._parsed: ParseResult | None = None
        self._format_map: dict[str, VideoFormat] = {}

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.bind("<Map>", self._on_first_map, add="+")

        self._build_ui()
        self._set_action_state()

    # === UI 构建 ===

    def _build_ui(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(7, weight=1)

        header = ctk.CTkFrame(self, fg_color="transparent")
        header.grid(row=0, column=0, padx=_PADX, pady=(22, 12), sticky="ew")
        ctk.CTkLabel(
            header,
            text="粘贴视频链接 → 解析 → 选择清晰度 → 下载",
            font=ctk.CTkFont(size=_FONT_TITLE, weight="bold"),
            anchor="w",
        ).pack(anchor="w", pady=(0, 6))
        ctk.CTkLabel(
            header,
            text="支持抖音、B站、YouTube 等（由 yt-dlp 提供）",
            font=ctk.CTkFont(size=_FONT_HINT),
            text_color="gray",
            anchor="w",
        ).pack(anchor="w")

        self._url_box = ctk.CTkTextbox(
            self,
            height=130,
            font=ctk.CTkFont(size=_FONT_BODY),
            wrap="word",
            fg_color=_INPUT_BG,
            text_color=_INPUT_FG,
            border_color=_INPUT_BORDER,
        )
        self._url_box.grid(row=1, column=0, padx=_PADX, pady=(0, 14), sticky="ew")
        self._url_box.insert("1.0", "https://v.douyin.com/ndbUluzN0OA/")

        dir_frame = ctk.CTkFrame(self, fg_color="transparent")
        dir_frame.grid(row=2, column=0, padx=_PADX, pady=(0, 14), sticky="ew")
        dir_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(dir_frame, text="保存到:", font=ctk.CTkFont(size=_FONT_BODY)).grid(
            row=0, column=0, padx=(0, 12),
        )
        self._dir_label = ctk.CTkLabel(
            dir_frame, text=str(self._output_dir), anchor="w",
            font=ctk.CTkFont(size=_FONT_BODY),
        )
        self._dir_label.grid(row=0, column=1, sticky="ew")
        ctk.CTkButton(
            dir_frame, text="浏览…", width=88, height=34,
            font=ctk.CTkFont(size=_FONT_BODY), command=self._pick_dir,
        ).grid(row=0, column=2, padx=(12, 0))

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.grid(row=3, column=0, padx=_PADX, pady=(0, 14), sticky="ew")

        self._parse_btn = ctk.CTkButton(
            btn_frame, text="解析链接", width=108, height=38,
            font=ctk.CTkFont(size=_FONT_BTN, weight="bold"),
            command=self._start_parse,
        )
        self._parse_btn.pack(side="left")

        self._download_btn = ctk.CTkButton(
            btn_frame, text="开始下载", width=108, height=38,
            font=ctk.CTkFont(size=_FONT_BTN, weight="bold"),
            command=self._start_download,
        )
        self._download_btn.pack(side="left", padx=(12, 0))

        self._clear_btn = ctk.CTkButton(
            btn_frame, text="清空日志", width=88, height=38,
            font=ctk.CTkFont(size=_FONT_BODY),
            fg_color="gray30", hover_color="gray40",
            command=self._clear_log,
        )
        self._clear_btn.pack(side="left", padx=(12, 0))

        self._info_frame = ctk.CTkFrame(self)
        self._info_frame.grid(row=4, column=0, padx=_PADX, pady=(0, 14), sticky="ew")
        self._info_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            self._info_frame, text="视频标题:", font=ctk.CTkFont(size=_FONT_BODY),
        ).grid(row=0, column=0, padx=(16, 10), pady=(14, 6), sticky="nw")
        self._title_label = ctk.CTkLabel(
            self._info_frame, text="请先点击「解析链接」",
            font=ctk.CTkFont(size=_FONT_BODY), anchor="w", wraplength=820,
        )
        self._title_label.grid(row=0, column=1, padx=(0, 16), pady=(14, 6), sticky="ew")

        ctk.CTkLabel(
            self._info_frame, text="清晰度:", font=ctk.CTkFont(size=_FONT_BODY),
        ).grid(row=1, column=0, padx=(16, 10), pady=(6, 14), sticky="w")
        self._quality_var = ctk.StringVar(value="—")
        self._quality_menu = ctk.CTkOptionMenu(
            self._info_frame,
            variable=self._quality_var,
            values=["—"],
            width=520,
            height=34,
            font=ctk.CTkFont(size=_FONT_BODY),
            fg_color=_INPUT_BG,
            text_color=_INPUT_FG,
            button_color="#E7E5E4",
            button_hover_color="#D6D3D1",
            dropdown_fg_color=_INPUT_BG,
            dropdown_text_color=_INPUT_FG,
            state="disabled",
        )
        self._quality_menu.grid(row=1, column=1, padx=(0, 16), pady=(6, 14), sticky="w")

        prog_frame = ctk.CTkFrame(self, fg_color="transparent")
        prog_frame.grid(row=5, column=0, padx=_PADX, pady=(0, 8), sticky="ew")
        prog_frame.grid_columnconfigure(0, weight=1)

        self._progress = ctk.CTkProgressBar(prog_frame, height=16)
        self._progress.grid(row=0, column=0, sticky="ew")
        self._progress.set(0)
        self._progress_pct = ctk.CTkLabel(
            prog_frame, text="0%", width=48,
            font=ctk.CTkFont(size=_FONT_STATUS),
        )
        self._progress_pct.grid(row=0, column=1, padx=(10, 0))

        self._status = ctk.CTkLabel(
            self, text="就绪 — 粘贴链接后先解析", anchor="w",
            font=ctk.CTkFont(size=_FONT_STATUS),
        )
        self._status.grid(row=6, column=0, padx=_PADX, pady=(0, 10), sticky="ew")

        self._log_box = ctk.CTkTextbox(
            self,
            font=ctk.CTkFont(family="monospace", size=_FONT_LOG),
            wrap="word",
            fg_color=_INPUT_BG,
            text_color=_INPUT_FG,
            border_color=_INPUT_BORDER,
        )
        self._log_box.grid(row=7, column=0, padx=_PADX, pady=(0, 22), sticky="nsew")

    # === 生命周期 ===

    def _on_first_map(self, _event: object = None) -> None:
        if self._startup_notified:
            return
        self._startup_notified = True
        try:
            self.update_idletasks()
            self.tk.call("wm", "class", self._w, "VideoDown")
        except Exception:
            pass
        notify_startup_complete()

    def _on_close(self) -> None:
        self._closing = True
        self._parse_anim = False
        if self._parse_anim_job is not None:
            try:
                self.after_cancel(self._parse_anim_job)
            except Exception:
                pass
            self._parse_anim_job = None
        self._cleanup_ctk_trackers()
        self.destroy()

    def _cleanup_ctk_trackers(self) -> None:
        try:
            from customtkinter.windows.widgets.scaling.scaling_tracker import ScalingTracker

            ScalingTracker.window_widgets_dict.pop(self, None)
            ScalingTracker.window_dpi_scaling_dict.pop(self, None)
            ScalingTracker.update_loop_running = False
        except Exception:
            pass
        try:
            from customtkinter.windows.widgets.appearance_mode.appearance_mode_tracker import (
                AppearanceModeTracker,
            )

            if self in AppearanceModeTracker.app_list:
                AppearanceModeTracker.app_list.remove(self)
            AppearanceModeTracker.update_loop_running = False
        except Exception:
            pass

    def _ui(self, callback) -> None:
        """从后台线程安全地调度 UI 更新。"""
        if self._closing:
            return
        try:
            if self.winfo_exists():
                self.after(0, callback)
        except Exception:
            pass

    # === 状态与进度 ===

    def _set_progress(self, value: float, text: str | None = None) -> None:
        clamped = max(0.0, min(1.0, value))
        self._progress.set(clamped)
        self._progress_pct.configure(text=text or f"{clamped:.0%}")

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        self._set_action_state()
        if not busy:
            self._parse_anim = False
            self._set_progress(0)

    def _set_action_state(self) -> None:
        state = "disabled" if self._busy else "normal"
        self._parse_btn.configure(state=state)
        can_download = (not self._busy) and self._parsed and not self._parsed.error
        self._download_btn.configure(state="normal" if can_download else "disabled")
        q_state = "normal" if can_download and len(self._format_map) > 0 else "disabled"
        self._quality_menu.configure(state=q_state)

    def _start_parse_animation(self) -> None:
        self._parse_anim = True
        self._tick_parse_animation(0.0, 1)

    def _tick_parse_animation(self, value: float, direction: int) -> None:
        if not self._parse_anim or self._closing:
            return
        next_val = value + direction * 0.04
        if next_val >= 0.92:
            next_val, direction = 0.92, -1
        elif next_val <= 0.05:
            next_val, direction = 0.05, 1
        self._set_progress(next_val)
        self._parse_anim_job = self.after(
            80, lambda: self._tick_parse_animation(next_val, direction),
        )

    # === 事件处理 ===

    def _pick_dir(self) -> None:
        chosen = filedialog.askdirectory(initialdir=str(self._output_dir))
        if chosen:
            self._output_dir = Path(chosen)
            self._dir_label.configure(text=chosen)

    def _clear_log(self) -> None:
        self._log_box.delete("1.0", "end")

    def _append_log(self, msg: str) -> None:
        self._log_box.insert("end", f"{msg}\n")
        self._log_box.see("end")

    def _set_status(self, msg: str) -> None:
        self._status.configure(text=msg)

    def _first_url(self) -> str | None:
        text = self._url_box.get("1.0", "end").strip()
        urls = extract_urls(text)
        if not urls:
            messagebox.showwarning("提示", "未检测到有效链接，请粘贴视频地址。")
            return None
        if len(urls) > 1:
            self._append_log(f"检测到 {len(urls)} 个链接，本次解析第一个。")
        return urls[0]

    def _apply_parse_result(self, result: ParseResult) -> None:
        self._parsed = result
        self._format_map.clear()
        if result.error:
            self._title_label.configure(text="解析失败")
            self._quality_var.set("—")
            self._quality_menu.configure(values=["—"], state="disabled")
            self._set_action_state()
            return

        duration = f"{result.duration // 60}:{result.duration % 60:02d}" if result.duration else "未知"
        self._title_label.configure(text=f"{result.title}  （时长 {duration}）")

        if not result.formats:
            self._quality_var.set("默认")
            self._quality_menu.configure(values=["默认"], state="disabled")
        else:
            labels = [f.label for f in result.formats]
            self._format_map = {f.label: f for f in result.formats}
            self._quality_var.set(labels[0])
            self._quality_menu.configure(values=labels)
        self._set_action_state()

    def _start_parse(self) -> None:
        if self._busy:
            return
        url = self._first_url()
        if not url:
            return
        self._set_busy(True)
        self._set_status("正在解析链接，请稍候…")
        self._append_log(f"── 解析: {url}")
        self._start_parse_animation()
        threading.Thread(target=self._parse_worker, args=(url,), daemon=True).start()

    def _parse_worker(self, url: str) -> None:
        result = parse_video(url)

        def _done() -> None:
            self._parse_anim = False
            self._apply_parse_result(result)
            self._set_busy(False)
            if result.error:
                self._set_progress(0)
                self._set_status(f"解析失败: {result.error}")
                self._append_log(f"✗ 解析失败: {result.error}")
            else:
                self._set_progress(1.0, "100%")
                n = len(result.formats)
                self._set_status(f"解析完成，共 {n or 1} 种清晰度可选")
                self._append_log(f"✓ 解析成功: {result.title}")
                for fmt in result.formats:
                    self._append_log(f"  · {fmt.label}")

        self._ui(_done)

    def _selected_format_id(self) -> str | None:
        if not self._parsed or self._parsed.error:
            return None
        label = self._quality_var.get()
        fmt = self._format_map.get(label)
        return fmt.format_id if fmt else None

    def _start_download(self) -> None:
        if self._busy or not self._parsed or self._parsed.error:
            messagebox.showinfo("提示", "请先解析链接并选择清晰度。")
            return
        self._set_busy(True)
        self._append_log("── 开始下载 ──")
        fmt_id = self._selected_format_id()
        if fmt_id:
            self._append_log(f"清晰度: {self._quality_var.get()} (id={fmt_id})")
        threading.Thread(
            target=self._download_worker,
            args=(self._parsed.url, fmt_id),
            daemon=True,
        ).start()

    def _download_worker(self, url: str, format_id: str | None) -> None:
        downloader = VideoDownloader(self._output_dir)

        def on_progress(data: dict[str, Any]) -> None:
            if data.get("status") != "downloading":
                return
            downloaded = data.get("downloaded_bytes") or 0
            total_bytes = data.get("total_bytes") or data.get("total_bytes_estimate") or 0
            if not total_bytes:
                return
            pct = downloaded / total_bytes
            speed = data.get("_speed_str", "")
            eta = data.get("_eta_str", "")

            def _update() -> None:
                self._set_progress(pct, f"{pct:.0%}")
                self._set_status(f"下载中 {pct:.0%}  {speed}  剩余 {eta}")

            self._ui(_update)

        def on_log(msg: str) -> None:
            self._ui(lambda m=msg: self._append_log(m))

        result = downloader.download(url, format_id=format_id, on_progress=on_progress, on_log=on_log)

        def _done() -> None:
            self._set_busy(False)
            if result.success:
                self._set_progress(1.0, "100%")
                self._set_status("下载完成")
                self._append_log(f"✓ 完成: {result.title}")
            else:
                self._set_progress(0)
                self._set_status("下载失败")
                self._append_log(f"✗ 失败: {result.error}")

        self._ui(_done)


def run_app() -> None:
    """启动 GUI 应用。"""
    logging.basicConfig(level=logging.INFO)
    app = VideoDownApp()
    app.mainloop()
