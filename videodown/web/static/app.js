/**
 * VideoDown 主逻辑（依赖 i18n.js）
 */
(function () {
  const { I18N, PLATFORMS_EN, getLang, setLang, fmt, SITE, apiUrl } = window.VD_I18N;
  const $ = (id) => document.getElementById(id);
  let parsed = null;
  let lang = getLang();

  const isMobile =
    /Android|iPhone|iPad|iPod|Mobile|MicroMessenger|Weibo|QQ\//i.test(navigator.userAgent) ||
    (navigator.maxTouchPoints > 0 && window.innerWidth < 1280) ||
    window.matchMedia("(pointer: coarse)").matches;
  const isIOS = /iPhone|iPad|iPod/i.test(navigator.userAgent);
  const isAndroid = /Android/i.test(navigator.userAgent);

  function L() {
    return I18N[lang];
  }

  function platformDisplayName(name) {
    return lang === "en" && PLATFORMS_EN[name] ? PLATFORMS_EN[name] : name;
  }

  function applyI18n() {
    const dict = L();
    document.documentElement.lang = dict.htmlLang;
    document.title = dict.title;
    const setMeta = (sel, content) => {
      const el = document.querySelector(sel);
      if (el) el.setAttribute("content", content);
    };
    setMeta('meta[name="description"]', dict.description);
    setMeta('meta[name="keywords"]', dict.keywords);
    setMeta('meta[property="og:title"]', dict.title);
    setMeta('meta[property="og:description"]', dict.description);
    setMeta('meta[property="og:locale"]', dict.ogLocale);
    setMeta('meta[name="twitter:title"]', dict.title);
    setMeta('meta[name="twitter:description"]', dict.description);

    document.querySelectorAll("[data-i18n]").forEach((el) => {
      const key = el.getAttribute("data-i18n");
      if (dict[key] !== undefined) el.textContent = dict[key];
    });
    document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
      const key = el.getAttribute("data-i18n-placeholder");
      if (dict[key]) el.placeholder = dict[key];
    });

    $("hintTarget").textContent = isMobile ? dict.hintTargetMobile : dict.hintTargetDesktop;
    const hintPrefix = $("hintPrefix");
    const hintSuffix = $("hintSuffix");
    if (hintPrefix) hintPrefix.textContent = dict.hint;
    if (hintSuffix) hintSuffix.textContent = dict.hintSuffix;
    $("btnDownload").textContent = isMobile ? dict.btnDownloadMobile : dict.btnDownloadDesktop;
    $("tipDesktop").style.display = isMobile ? "none" : "block";
    $("tipMobile").style.display = isMobile ? "block" : "none";
    $("navLang").textContent = dict.navLang;
    $("navLang").title = dict.navLangTitle;
    $("status").textContent = dict.statusReady;
    const videoTitle = $("videoTitle");
    if (videoTitle && !parsed) videoTitle.textContent = dict.titleEmpty;
    $("platformCheckedAt").textContent = dict.platformChecking;
    $("platformRow").textContent = dict.platformProbing;
    $("btnSaveAlbum").textContent = dict.saveAlbum;

    const faqEl = $("faqList");
    faqEl.innerHTML = "";
    dict.faq.forEach((item) => {
      const li = document.createElement("li");
      li.innerHTML = `<strong>${item.q}</strong><p>${item.a}</p>`;
      faqEl.appendChild(li);
    });
    const howEl = $("howSteps");
    howEl.innerHTML = "";
    dict.seoHowSteps.forEach((step) => {
      const li = document.createElement("li");
      li.textContent = step;
      howEl.appendChild(li);
    });
    $("footerCopyright").textContent = fmt(dict.footerCopyright, { year: new Date().getFullYear() });
    updateIosTip();

    injectJsonLd(dict);
    updateCanonical();
  }

  function updateCanonical() {
    const base = SITE.base || location.origin + location.pathname.replace(/\/$/, "");
    const href = `${base}/?lang=${lang}`;
    let link = document.querySelector('link[rel="canonical"]');
    if (!link) {
      link = document.createElement("link");
      link.rel = "canonical";
      document.head.appendChild(link);
    }
    link.href = href;
  }

  function injectJsonLd(dict) {
    const base = SITE.base || location.origin;
    const data = {
      "@context": "https://schema.org",
      "@graph": [
        {
          "@type": "WebSite",
          "@id": `${base}/#website`,
          url: base,
          name: lang === "en" ? "VideoDown" : "VideoDown 视频下载",
          description: dict.description,
          inLanguage: [lang === "en" ? "en" : "zh-CN"],
        },
        {
          "@type": "WebApplication",
          "@id": `${base}/#app`,
          name: "VideoDown",
          url: base,
          applicationCategory: "MultimediaApplication",
          operatingSystem: "Web",
          offers: { "@type": "Offer", price: "0", priceCurrency: "USD" },
          description: dict.description,
          featureList:
            "Douyin, Xiaohongshu, YouTube, Bilibili, Kuaishou, X, TikTok video download",
        },
        {
          "@type": "FAQPage",
          "@id": `${base}/#faq`,
          mainEntity: dict.faq.map((f) => ({
            "@type": "Question",
            name: f.q,
            acceptedAnswer: { "@type": "Answer", text: f.a },
          })),
        },
        {
          "@type": "Organization",
          "@id": `${base}/#org`,
          name: "VideoDown",
          url: base,
        },
      ],
    };
    let script = document.getElementById("jsonld");
    if (!script) {
      script = document.createElement("script");
      script.id = "jsonld";
      script.type = "application/ld+json";
      document.head.appendChild(script);
    }
    script.textContent = JSON.stringify(data);
  }

  function log(msg) {
    const box = $("log");
    box.textContent += msg + "\n";
    box.scrollTop = box.scrollHeight;
  }

  function setBusy(busy) {
    $("btnParse").disabled = busy;
    $("btnDownload").disabled = busy || !parsed;
  }

  function setProgress(pct, text) {
    $("progress").value = Math.round(pct * 100);
    if (text) $("status").textContent = text;
  }

  function selectedFormat() {
    const id = $("quality").value;
    return (parsed.formats || []).find((f) => f.format_id === id) || parsed.formats?.[0];
  }

  function buildFilename(title, ext) {
    return (title || "video").replace(/[\\/:*?"<>|]/g, "_") + "." + (ext || "mp4");
  }

  function submitStreamForm(parsedData, fmt) {
    const form = document.createElement("form");
    form.method = "POST";
    form.action = apiUrl("api/stream");
    form.target = "downloadFrame";
    form.style.display = "none";
    const fields = {
      url: parsedData.url,
      title: parsedData.title || "video",
      ext: fmt?.ext || "mp4",
    };
    if (fmt?.format_id) fields.format_id = fmt.format_id;
    Object.entries(fields).forEach(([name, value]) => {
      const input = document.createElement("input");
      input.type = "hidden";
      input.name = name;
      input.value = value;
      form.appendChild(input);
    });
    document.body.appendChild(form);
    form.submit();
    setTimeout(() => form.remove(), 1000);
  }

  function albumGuideSteps() {
    const d = L();
    if (isIOS) return d.albumStepsIOS;
    if (isAndroid) return d.albumStepsAndroid;
    return d.albumStepsOther;
  }

  function canShareVideoFiles() {
    if (!navigator.canShare) return false;
    try {
      const probe = new File(["x"], "probe.mp4", { type: "video/mp4" });
      return navigator.canShare({ files: [probe] });
    } catch {
      return false;
    }
  }

  async function saveToAlbum(parsedData, fmt) {
    const d = L();
    const filename = buildFilename(parsedData.title, fmt?.ext);
    const btn = $("btnSaveAlbum");
    btn.disabled = true;
    setProgress(15, d.statusPreparing);
    log(d.logSaveAlbum);
    try {
      const body = new FormData();
      body.append("url", parsedData.url);
      body.append("title", parsedData.title || "video");
      body.append("ext", fmt?.ext || "mp4");
      if (fmt?.format_id) body.append("format_id", fmt.format_id);
      const res = await fetch(apiUrl("api/stream"), { method: "POST", body });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || res.statusText);
      }
      const blob = await res.blob();
      const file = new File([blob], filename, { type: blob.type || "video/mp4" });
      if (!navigator.canShare || !navigator.canShare({ files: [file] })) {
        throw new Error(d.errShareUnsupported);
      }
      await navigator.share({ files: [file], title: parsedData.title || filename });
      setProgress(100, d.statusShareOk);
      log(d.logShareOk);
    } catch (e) {
      if (e.name === "AbortError") {
        setProgress(100, d.statusShareCancel);
        log(d.logShareCancel);
      } else {
        setProgress(0, d.statusSaveFail);
        log("✗ " + e.message);
        alert(e.message);
      }
    } finally {
      btn.disabled = false;
    }
  }

  function showDownloadPanel(filename) {
    const d = L();
    const panel = $("downloadPanel");
    const anchor = $("downloadPanelLink");
    const steps = $("downloadPanelSteps");
    const saveBtn = $("btnSaveAlbum");
    steps.innerHTML = "";
    albumGuideSteps().forEach((text) => {
      const li = document.createElement("li");
      li.textContent = text;
      steps.appendChild(li);
    });
    if (isMobile && canShareVideoFiles()) {
      saveBtn.style.display = "block";
      saveBtn.onclick = () => parsed && saveToAlbum(parsed, selectedFormat());
    } else {
      saveBtn.style.display = "none";
    }
    $("downloadPanelHint").innerHTML = isMobile
      ? `<strong>${d.dlPanelHintMobile}</strong>`
      : d.dlPanelHintDesktop;
    if (!isMobile) steps.innerHTML = "";
    anchor.onclick = (e) => {
      e.preventDefault();
      if (parsed) submitStreamForm(parsed, selectedFormat());
    };
    const short = filename.length > 28 ? filename.slice(0, 27) + "…" : filename;
    anchor.textContent = d.dlRetry + short;
    panel.classList.add("show");
  }

  function hideDownloadPanel() {
    $("downloadPanel").classList.remove("show");
  }

  async function api(path, options) {
    const res = await fetch(apiUrl(path), options);
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.detail || res.statusText);
    return data;
  }

  async function loadPlatforms() {
    const d = L();
    const row = $("platformRow");
    const checked = $("platformCheckedAt");
    const showNames = ["抖音", "小红书", "YouTube", "B站", "快手", "X", "TikTok"];
    checked.textContent = d.platformChecking;
    row.textContent = d.platformProbing;
    try {
      const res = await fetch(apiUrl("api/platforms?_=" + Date.now()), { cache: "no-store" });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.detail || res.statusText);
      row.innerHTML = "";
      const icon = { ok: "✅", cookie_required: "⚠️", unstable: "⚠️", varies: "ℹ️", error: "❌" };
      const byName = Object.fromEntries((data.platforms || []).map((p) => [p.name, p]));
      showNames.forEach((name) => {
        const p = byName[name];
        const span = document.createElement("span");
        span.className = "platform-tag";
        const label = platformDisplayName(name);
        if (!p) {
          span.textContent = `• ${label}`;
        } else {
          span.textContent = `${icon[p.status] || "•"}${label}`;
          span.title = p.note || "";
        }
        row.appendChild(span);
      });
      checked.textContent = data.checked_at
        ? `${d.platformUpdated} ${data.checked_at}`
        : d.platformUpdatedDone;
    } catch (e) {
      row.innerHTML = `<span style="color:#f87171">${d.platformProbeFail}${e.message}</span>`;
      checked.textContent = d.platformProbeFail;
    }
  }

  function shareUrl() {
    const base = (SITE.base || location.origin).replace(/\/$/, "");
    return `${base}/?lang=${lang}`;
  }

  async function shareApp() {
    const d = L();
    const url = shareUrl();
    const payload = { title: d.shareTitle, text: d.shareText, url };
    try {
      if (navigator.share) {
        await navigator.share(payload);
        return;
      }
      await navigator.clipboard.writeText(`${d.shareText}\n${url}`);
      alert(d.shareCopied);
    } catch (e) {
      if (e.name === "AbortError") return;
      try {
        await navigator.clipboard.writeText(`${d.shareText}\n${url}`);
        alert(d.shareCopied);
      } catch {
        prompt(d.shareCopied, url);
      }
    }
  }

  function setCopyButtonEnabled(on) {
    const btn = $("btnCopyText");
    if (btn) btn.disabled = !on;
  }

  function showVideoCopy(text, loading) {
    const panel = $("copyPanel");
    const box = $("videoCopy");
    if (!panel || !box) return;
    panel.hidden = false;
    if (loading) {
      box.textContent = L().transcribing;
      setCopyButtonEnabled(false);
      return;
    }
    const copy = (text || "").trim();
    if (!copy || copy === L().transcribing || copy === L().copyEmpty) {
      box.textContent = copy || L().copyEmpty;
      setCopyButtonEnabled(false);
      return;
    }
    box.textContent = copy;
    setCopyButtonEnabled(true);
  }

  async function fetchTranscript(parsedData) {
    const fmt = (parsedData.formats || [])[0];
    showVideoCopy("", true);
    try {
      const data = await api("api/transcribe", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          url: parsedData.url,
          format_id: fmt?.format_id || null,
        }),
      });
      showVideoCopy(data.transcript || "");
    } catch (e) {
      showVideoCopy(L().copyEmpty);
    }
  }

  function looksLikeVideoLink(text) {
    return /https?:\/\/|v\.douyin|tiktok|youtube|youtu\.be|b23\.tv|bilibili|xiaohongshu|xhslink|kuaishou|twitter\.com|x\.com/i.test(text);
  }

  async function offerClipboardPaste() {
    const box = $("url");
    if (!box || box.value.trim()) return;
    if (!navigator.clipboard?.readText) return;
    let clip = "";
    try {
      clip = (await navigator.clipboard.readText()).trim();
    } catch {
      return;
    }
    if (!clip || !looksLikeVideoLink(clip)) return;
    if (confirm(L().clipboardPaste)) {
      box.value = clip;
    }
  }

  function setupClipboardPaste() {
    const box = $("url");
    if (!box) return;
    let asked = false;
    box.addEventListener("focus", () => {
      if (asked || box.value.trim()) return;
      asked = true;
      offerClipboardPaste();
    });
    if (!box.value.trim()) offerClipboardPaste();
  }

  function bindEvents() {
    $("navLang").onclick = (e) => {
      e.preventDefault();
      setLang(lang === "zh" ? "en" : "zh");
    };

    $("btnShare").onclick = (e) => {
      e.preventDefault();
      shareApp();
    };

    $("btnCopyText").onclick = async () => {
      const text = ($("videoCopy")?.textContent || "").trim();
      const d = L();
      if (!text || text === d.transcribing || text === d.copyEmpty) return;
      try {
        await navigator.clipboard.writeText(text);
        const btn = $("btnCopyText");
        const old = btn.textContent;
        btn.textContent = d.copyDone;
        setTimeout(() => { btn.textContent = old; }, 1500);
      } catch {
        prompt(d.copyDone, text);
      }
    };

    $("btnParse").onclick = async () => {
      const d = L();
      const text = $("url").value.trim();
      if (!text) return alert(d.alertNoUrl);
      setBusy(true);
      parsed = null;
      $("copyPanel").hidden = true;
      setCopyButtonEnabled(false);
      setProgress(0, d.statusParsing);
      log(d.logParseStart);
      try {
        const data = await api("api/parse", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ text }),
        });
        parsed = data;
        const dur = data.duration
          ? ` （${Math.floor(data.duration / 60)}:${String(data.duration % 60).padStart(2, "0")}）`
          : "";
        $("videoTitle").textContent = data.title + dur;
        fetchTranscript(data);
        const sel = $("quality");
        sel.innerHTML = "";
        (data.formats || []).forEach((f) => {
          const opt = document.createElement("option");
          opt.value = f.format_id;
          opt.textContent = f.label;
          sel.appendChild(opt);
        });
        sel.disabled = !(data.formats && data.formats.length);
        setProgress(100, fmt(d.statusParseDone, { n: (data.formats || []).length || 1 }));
        log("✓ " + data.title + (data.extractor ? ` [${data.extractor}]` : ""));
        (data.formats || []).forEach((f) => log("  · " + f.label));
        $("btnDownload").disabled = false;
      } catch (e) {
        setProgress(0, d.statusParseFail);
        log("✗ " + e.message);
      } finally {
        setBusy(false);
      }
    };

    $("btnDownload").onclick = () => {
      if (!parsed) return;
      const d = L();
      const fmtSel = selectedFormat();
      const filename = buildFilename(parsed.title, fmtSel?.ext);
      setBusy(true);
      hideDownloadPanel();
      log(d.logDownloadStart);
      log(d.logQuality + " " + (fmtSel?.label || "default"));
      setProgress(30, d.statusPreparing);
      log(d.statusSubmitted);
      submitStreamForm(parsed, fmtSel);
      showDownloadPanel(filename);
      setBusy(false);
    };

    $("btnClear").onclick = () => {
      $("log").textContent = "";
    };
  }

  function isStandalonePwa() {
    return (
      window.matchMedia("(display-mode: standalone)").matches ||
      window.navigator.standalone === true
    );
  }

  function isIosBrowser() {
    return /iPhone|iPad|iPod/i.test(navigator.userAgent);
  }

  function isInAppBrowser() {
    return /MicroMessenger|Weibo|QQ\//i.test(navigator.userAgent);
  }

  function updateIosTip() {
    const el = $("iosTip");
    const text = $("iosTipText");
    if (!el || isStandalonePwa() || !isIosBrowser()) return;
    const d = L();
    if (text) text.textContent = isInAppBrowser() ? d.iosTipWechat : d.iosTip;
    el.hidden = false;
  }

  function registerServiceWorker() {
    if (!("serviceWorker" in navigator)) return;
    const scope = (() => {
      try {
        return new URL(apiUrl("sw.js")).pathname.replace(/sw\.js$/, "");
      } catch {
        return "/videodown/";
      }
    })();
    navigator.serviceWorker.register(apiUrl("sw.js"), { scope }).catch(() => {});
  }

  function init() {
    if (isStandalonePwa()) {
      document.documentElement.classList.add("standalone");
      document.body.classList.add("standalone");
    }
    lang = getLang();
    applyI18n();
    const urlBox = $("url");
    if (urlBox) urlBox.value = "";
    bindEvents();
    setupClipboardPaste();
    registerServiceWorker();
    loadPlatforms();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
