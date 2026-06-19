/**
 * VideoDown 中英双语与 SEO 文案
 */
(function (global) {
  const SITE = {
    base: (document.querySelector('meta[name="vd:base"]') || {}).content || "",
    name: "VideoDown",
  };

  const PLATFORMS_EN = {
    抖音: "Douyin",
    小红书: "Xiaohongshu",
    YouTube: "YouTube",
    B站: "Bilibili",
    快手: "Kuaishou",
    X: "X",
    TikTok: "TikTok",
  };

  const I18N = {
    zh: {
      htmlLang: "zh-CN",
      title: "VideoDown 免费在线视频下载 | 抖音 小红书 YouTube TikTok X 解析",
      description:
        "VideoDown 免费在线视频下载工具：粘贴抖音、小红书、YouTube、B站、快手、X（推特）、TikTok 分享链接，一键解析清晰度并下载到手机或电脑。访客无需登录，服务器不落盘，隐私安全。",
      keywords:
        "视频下载,在线下载,抖音下载,小红书下载,YouTube下载,B站下载,快手下载,TikTok下载,X视频下载,推特下载,无水印,免费",
      ogLocale: "zh_CN",
      navLang: "English",
      navLangTitle: "Switch to English",
      navShare: "分享",
      shareTitle: "VideoDown 视频下载",
      shareText: "免费视频下载工具，抖音/小红书/YouTube/TikTok 等链接粘贴即用。\n用 Safari 打开后：分享 → 添加到主屏幕，即可装到手机桌面。",
      shareCopied: "链接已复制，发给朋友即可",
      h1: "VideoDown 视频下载",
      hint: "粘贴链接 → 解析 → 选清晰度 → 下载到",
      hintTargetDesktop: "本机",
      hintTargetMobile: "手机",
      hintSuffix: "（访客无需登录，由服务器统一解析）",
      platformSupport: "平台支持",
      platformChecking: "检测中…",
      platformProbing: "正在探测…",
      platformUpdated: "更新于",
      platformUpdatedDone: "已更新",
      platformProbeFail: "探测失败：",
      urlLabel: "视频链接",
      urlPlaceholder: "粘贴分享文案或链接",
      clipboardPaste: "剪贴板里有链接，要粘贴吗？",
      btnParse: "解析链接",
      btnDownloadDesktop: "下载到本机",
      btnDownloadMobile: "下载到手机",
      btnClear: "清空日志",
      titleLabel: "视频标题",
      titleEmpty: "请先解析链接",
      qualityLabel: "清晰度",
      statusReady: "就绪",
      statusParsing: "解析中…",
      statusParseDone: "解析完成，{n} 种清晰度",
      statusParseFail: "解析失败",
      statusPreparing: "服务器准备中，请稍候（约几秒）…",
      statusSubmitted: "已提交；大文件需等待几秒后开始，请看浏览器下载栏",
      tipDesktop: "下载由浏览器接管，请看浏览器底部/右上角下载栏的进度（本页进度条仅表示已提交）。",
      tipMobile: "手机：下载后在通知栏或「文件/下载」中查看；完成后可点绿色「保存到相册」。",
      dlPanelHintMobile: "下载已提交 — 网页不能直接写入相册，按下方步骤查找或点绿色按钮",
      dlPanelHintDesktop: "若未开始下载，请点下方按钮重试",
      dlRetry: "点击重新下载：",
      saveAlbum: "保存到相册",
      alertNoUrl: "请粘贴链接",
      logParseStart: "── 开始解析 ──",
      logDownloadStart: "── 下载到本机（浏览器原生下载，不占网页内存）──",
      logQuality: "清晰度:",
      logSaveAlbum: "── 保存到相册（系统分享）──",
      logShareOk: "✓ 请在弹出的面板中选择「存储视频」或「保存到相册」",
      logShareCancel: "· 用户取消了分享",
      statusShareOk: "已调起系统分享，请选择「存储视频/保存到相册」",
      statusShareCancel: "已取消分享",
      statusSaveFail: "保存失败",
      errShareUnsupported: "当前浏览器不支持直接分享视频，请按上方步骤在「文件/下载」中手动保存",
      seoH2: "支持的短视频与长视频平台",
      seoP1:
        "VideoDown 是面向访客免费的在线视频解析下载服务。支持抖音、小红书、YouTube、哔哩哔哩、快手、X（原 Twitter）、TikTok 等平台分享链接。粘贴口令或 URL，选择清晰度后即可保存到本机。",
      seoH2How: "如何使用",
      seoHowSteps: [
        "复制视频分享链接或整段分享文案",
        "粘贴到上方输入框，点击「解析链接」",
        "选择清晰度后点击下载，文件由浏览器保存到手机或电脑",
      ],
      seoH2Faq: "常见问题",
      faq: [
        {
          q: "下载的视频保存在哪里？",
          a: "文件由您的浏览器下载到系统默认「下载」目录。手机用户可在通知栏、文件 App 或下载文件夹中查看；部分浏览器支持「保存到相册」。",
        },
        {
          q: "服务器会保存我的视频吗？",
          a: "不会。VideoDown 仅在转发时短暂缓存，发送完成后立即删除，不在服务器长期存储。",
        },
        {
          q: "需要登录抖音或 YouTube 吗？",
          a: "访客无需登录。抖音、快手、TikTok、X 等可直接解析；小红书与部分 YouTube 内容由服务器统一 Cookie 支持。",
        },
        {
          q: "为什么快手或 TikTok 短链失败？",
          a: "部分短链在服务器端无法跳转，请从 App 复制带 /video/ 或完整域名的长链接再试。",
        },
      ],
      footerTagline: "免费在线视频解析 · 隐私优先 · 服务器不落盘",
      footerCopyright: "© {year} VideoDown · leedreamer.cn 保留所有权利",
      footerPrivacy: "隐私：视频仅作转发，不在服务器长期保存",
      footerTerms: "仅供个人学习与研究，请遵守各平台版权与用户协议",
      albumStepsIOS: [
        "看屏幕顶部/底部是否弹出「下载完成」，点一下即可预览",
        "或打开「文件」App →「我的 iPhone」→「下载」找到视频",
        "在文件中长按视频 →「共享」→ 选「存储视频」即可进相册",
        "也可点下方绿色「保存到相册」（调起系统分享面板）",
      ],
      albumStepsAndroid: [
        "下拉通知栏，点「下载完成」通知直接打开",
        "或打开「文件管理」/「下载」文件夹",
        "部分机型：长按视频 →「分享」→ 选「保存到相册」",
        "支持时可用下方绿色「保存到相册」",
      ],
      albumStepsOther: ["请看浏览器下载栏或系统「下载」文件夹"],
      copyLabel: "语音文字",
      copyEmpty: "未识别到语音，可能无对白或背景音过小",
      copyBtn: "一键复制文案",
      copyDone: "已复制",
      transcribing: "正在把视频声音转成文字，请稍候…",
      transcribeFail: "语音识别失败",
      iosTip: "添加后就是桌面 App，和微信抖音一样点开用。Safari 点「分享」→「添加到主屏幕」",
      iosTipWechat: "微信里先点 ··· →「在 Safari 中打开」，再点分享 → 添加到主屏幕",
    },
    en: {
      htmlLang: "en",
      title: "VideoDown – Free Online Video Downloader | Douyin, TikTok, YouTube, X, Bilibili",
      description:
        "VideoDown is a free online video downloader for Douyin, Xiaohongshu (RED), YouTube, Bilibili, Kuaishou, X (Twitter) and TikTok. Paste any share link, pick HD quality, save to iPhone, Android or PC. No signup, no watermark fee, privacy-first streaming with zero server storage.",
      keywords:
        "video downloader,online video download,free video saver,Douyin downloader,TikTok video download,YouTube downloader,Bilibili download,Kuaishou downloader,Xiaohongshu download,Twitter X video download,no watermark,save TikTok without watermark,MP4 download",
      ogLocale: "en_US",
      navLang: "中文",
      navLangTitle: "切换到中文",
      navShare: "Share",
      shareTitle: "VideoDown",
      shareText: "Free video downloader for Douyin, YouTube, TikTok and more.\nOpen in Safari → Share → Add to Home Screen.",
      shareCopied: "Link copied — send it to a friend",
      h1: "VideoDown – Video Downloader",
      hint: "Paste link → Parse → Choose quality → Save to",
      hintTargetDesktop: "your device",
      hintTargetMobile: "your phone",
      hintSuffix: "(no login required; parsed on our server)",
      platformSupport: "Platforms",
      platformChecking: "Checking…",
      platformProbing: "Probing…",
      platformUpdated: "Updated",
      platformUpdatedDone: "Up to date",
      platformProbeFail: "Probe failed: ",
      urlLabel: "Video URL",
      urlPlaceholder: "Paste share text or URL",
      clipboardPaste: "Paste link from clipboard?",
      btnParse: "Parse link",
      btnDownloadDesktop: "Download",
      btnDownloadMobile: "Download",
      btnClear: "Clear log",
      titleLabel: "Title",
      titleEmpty: "Parse a link first",
      qualityLabel: "Quality",
      statusReady: "Ready",
      statusParsing: "Parsing…",
      statusParseDone: "Done – {n} quality option(s)",
      statusParseFail: "Parse failed",
      statusPreparing: "Preparing on server, please wait…",
      statusSubmitted: "Submitted – check your browser download bar",
      tipDesktop: "Your browser handles the download; watch the download icon for progress.",
      tipMobile: "On mobile: check notifications or Files/Downloads; use Save to Photos when available.",
      dlPanelHintMobile: "Download started – find the file below or tap Save to Photos",
      dlPanelHintDesktop: "If download did not start, tap retry below",
      dlRetry: "Retry download: ",
      saveAlbum: "Save to Photos",
      alertNoUrl: "Please paste a link",
      logParseStart: "── Parse started ──",
      logDownloadStart: "── Browser download (no in-page buffer) ──",
      logQuality: "Quality:",
      logSaveAlbum: "── Save to Photos (share sheet) ──",
      logShareOk: "✓ Choose Save Video / Save to Photos in the share sheet",
      logShareCancel: "· Share cancelled",
      statusShareOk: "Share sheet opened",
      statusShareCancel: "Cancelled",
      statusSaveFail: "Save failed",
      errShareUnsupported: "Sharing not supported – save manually from Downloads",
      seoH2: "Supported platforms",
      seoP1:
        "VideoDown is a free, browser-based video parser and downloader trusted by users worldwide. Paste share links from Douyin (Chinese TikTok), Xiaohongshu / RED, YouTube, Bilibili, Kuaishou, X (formerly Twitter) and TikTok. Select resolution, download MP4 to your device instantly. Ideal for saving clips for offline viewing, research and personal archiving — we never keep your files on our servers.",
      seoH2How: "How to use",
      seoHowSteps: [
        "Copy the video share link or full share text",
        "Paste above and click Parse link",
        "Pick quality and download – your browser saves the file",
      ],
      seoH2Faq: "FAQ",
      faq: [
        {
          q: "Is VideoDown free and safe?",
          a: "Yes. VideoDown is free with no account required. Videos are streamed through our server only during download and deleted immediately afterward — we do not store your content.",
        },
        {
          q: "Where is my downloaded video?",
          a: "Files go to your browser's default Downloads folder. On phones, check notifications, Files app, or Downloads.",
        },
        {
          q: "Do you store videos on the server?",
          a: "No. We only stream through temporarily and delete immediately after transfer.",
        },
        {
          q: "Do I need to log in?",
          a: "No account needed for visitors. Douyin, Kuaishou, TikTok and X work directly; Xiaohongshu and some YouTube use server cookies.",
        },
        {
          q: "Why do short Kuaishou/TikTok links fail?",
          a: "Some short URLs cannot redirect on the server. Copy the full /video/ link from the app.",
        },
      ],
      footerTagline: "Free online parser · Privacy-first · No server storage",
      footerCopyright: "© {year} VideoDown · leedreamer.cn · All rights reserved",
      footerPrivacy: "Privacy: videos are streamed, not stored on disk",
      footerTerms: "For personal use only; respect platform terms and copyright",
      albumStepsIOS: [
        "Tap the download banner if shown",
        "Or open Files → On My iPhone → Downloads",
        "Long-press video → Share → Save Video",
        "Or tap green Save to Photos below",
      ],
      albumStepsAndroid: [
        "Open the download notification",
        "Or Files / Download folder",
        "Long-press → Share → Save to gallery if needed",
        "Or use Save to Photos button when shown",
      ],
      albumStepsOther: ["Check browser downloads folder"],
      copyLabel: "Speech to text",
      copyEmpty: "No speech detected in this video",
      copyBtn: "Copy transcript",
      copyDone: "Copied",
      transcribing: "Transcribing audio, please wait…",
      transcribeFail: "Transcription failed",
      iosTip: "Adds to Home Screen as a real app. Safari → Share → Add to Home Screen",
      iosTipWechat: "In WeChat: ··· → Open in Safari, then Share → Add to Home Screen",
    },
  };

  function getLang() {
    const params = new URLSearchParams(location.search);
    const q = params.get("lang");
    if (q === "en" || q === "zh") return q;
    const stored = localStorage.getItem("vd_lang");
    if (stored === "en" || stored === "zh") return stored;
    return document.documentElement.lang.startsWith("en") ? "en" : "zh";
  }

  function setLang(lang) {
    localStorage.setItem("vd_lang", lang);
    document.cookie = `vd_lang=${lang};path=/;max-age=31536000;SameSite=Lax`;
    const url = new URL(location.href);
    url.searchParams.set("lang", lang);
    location.href = url.toString();
  }

  function t(key, lang) {
    const L = I18N[lang || getLang()];
    return L[key];
  }

  function fmt(str, vars) {
    return str.replace(/\{(\w+)\}/g, (_, k) => vars[k] ?? "");
  }

  function apiUrl(path) {
    const base = (SITE.base || "").replace(/\/$/, "");
    const p = path.replace(/^\//, "");
    return base ? `${base}/${p}` : path;
  }

  global.VD_I18N = { SITE, I18N, PLATFORMS_EN, getLang, setLang, t, fmt, apiUrl };
})(window);
