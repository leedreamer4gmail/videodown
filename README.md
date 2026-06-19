# videodown 🎬

基于 [yt-dlp](https://github.com/yt-dlp/yt-dlp) 的跨平台视频下载器，支持桌面 GUI 和 Web 界面。

## ✨ 功能特点

- **多平台支持** — 桌面 GUI（基于 CustomTkinter）和 Web 界面
- **多平台视频下载** — 支持 YouTube、抖音/TikTok、快手、小红书等平台
- **字幕/音频提取** — 下载字幕、提取音频、语音转文本
- **智能 URL 识别** — 自动识别并处理各平台视频链接
- **Cookie 管理** — 支持平台登录 Cookie 以提高下载成功率
- **跨平台** — 支持 Windows、macOS、Linux

## 🚀 快速开始

### 安装依赖

```bash
pip install -r requirements-web.txt
```

### 运行 Web 服务

```bash
python3 __main__.py
# 或
bash run-web.sh
```

### 运行桌面 GUI

```bash
python3 gui/app.py
```

## 📁 项目结构

```
videodown/
├── core/           # 核心下载与处理模块
│   ├── downloader.py    # 下载引擎
│   ├── transcribe.py    # 语音转文本
│   ├── copy.py          # 剪贴板操作
│   ├── url_normalize.py # URL 标准化
│   ├── ytdlp_config.py  # yt-dlp 配置
│   ├── platform_probe.py# 平台探测
│   └── models.py        # 数据模型
├── web/            # Web 界面 (FastAPI)
├── gui/            # 桌面 GUI (CustomTkinter)
├── deploy/         # 部署配置
├── scripts/        # 辅助脚本
├── config/         # 配置文件（Cookie 等）
└── downloads/      # 下载文件输出目录
```

## ⚙️ 配置

在 `config/` 目录下放置各平台的 Cookie 文件即可启用对应平台的下载功能：

- `youtube_cookies.txt` — YouTube Cookie
- `xiaohongshu_cookies.txt` — 小红书 Cookie

## 🛠️ 技术栈

- **Python 3.12+**
- **yt-dlp** — 视频下载引擎
- **FastAPI + Uvicorn** — Web 服务
- **CustomTkinter** — 桌面 GUI 框架
- **Whisper** — 语音识别

## 📄 许可证

[MIT](LICENSE)

## 🙏 致谢

- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter)
- [FastAPI](https://fastapi.tiangolo.com/)
