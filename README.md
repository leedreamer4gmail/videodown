# videodown 🎬

基于 [yt-dlp](https://github.com/yt-dlp/yt-dlp) 的跨平台视频下载器，支持桌面 GUI 和 Web 界面。

A cross-platform video downloader built on [yt-dlp](https://github.com/yt-dlp/yt-dlp), featuring both a desktop GUI and a web interface.

---

## ✨ 功能特点 / Features

### 中文
- **多平台支持** — 桌面 GUI（基于 CustomTkinter）和 Web 界面
- **多平台视频下载** — 支持 YouTube、抖音/TikTok、快手、小红书等平台
- **字幕/音频提取** — 下载字幕、提取音频、语音转文本
- **智能 URL 识别** — 自动识别并处理各平台视频链接
- **Cookie 管理** — 支持平台登录 Cookie 以提高下载成功率
- **跨平台** — 支持 Windows、macOS、Linux

### English
- **Dual Interface** — Desktop GUI (CustomTkinter) and Web UI (FastAPI)
- **Multi-Platform Downloads** — YouTube, Douyin/TikTok, Kuaishou, Xiaohongshu, and more
- **Subtitle & Audio Extraction** — Download subtitles, extract audio, transcribe speech to text
- **Smart URL Detection** — Automatically recognizes and processes video links from various platforms
- **Cookie Management** — Use platform login cookies for authenticated downloads
- **Cross-Platform** — Windows, macOS, Linux

---

## 🚀 快速开始 / Quick Start

### 安装依赖 / Install Dependencies

```bash
pip install -r requirements-web.txt
```

### 运行 Web 服务 / Run Web Server

```bash
python3 __main__.py
# or
bash run-web.sh
```

### 运行桌面 GUI / Run Desktop GUI

```bash
python3 gui/app.py
```

---

## 📁 项目结构 / Project Structure

```
videodown/
├── core/           # 核心下载与处理模块 / Core download & processing modules
│   ├── downloader.py       # 下载引擎 / Download engine
│   ├── transcribe.py       # 语音转文本 / Speech-to-text
│   ├── copy.py             # 剪贴板操作 / Clipboard operations
│   ├── url_normalize.py    # URL 标准化 / URL normalization
│   ├── ytdlp_config.py     # yt-dlp 配置 / yt-dlp configuration
│   ├── platform_probe.py   # 平台探测 / Platform detection
│   └── models.py           # 数据模型 / Data models
├── web/             # Web 界面 / Web interface (FastAPI)
├── gui/             # 桌面 GUI / Desktop GUI (CustomTkinter)
├── deploy/          # 部署配置 / Deployment config
├── scripts/         # 辅助脚本 / Helper scripts
├── config/          # 配置文件（Cookie 等）/ Config files (Cookies, etc.)
└── downloads/       # 下载文件输出目录 / Download output directory
```

---

## ⚙️ 配置 / Configuration

Place platform cookie files in the `config/` directory to enable downloads on those platforms:

```text
config/
├── youtube_cookies.txt          # YouTube
├── xiaohongshu_cookies.txt      # 小红书 / Xiaohongshu
└── xhs_probe_url.txt.example    # 探测 URL 模板 / Probe URL template
```

---

## 🛠️ 技术栈 / Tech Stack

| Technology | Purpose |
|---|---|
| **Python 3.12+** | Core language |
| **yt-dlp** | Video download engine |
| **FastAPI + Uvicorn** | Web service |
| **CustomTkinter** | Desktop GUI framework |
| **Whisper** | Speech recognition |

---

## 📄 许可证 / License

[MIT](LICENSE)

---

## 🙏 致谢 / Acknowledgements

- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
- [FastAPI](https://fastapi.tiangolo.com/)
