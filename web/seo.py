"""SEO / GEO / AIO 静态资源生成。"""

from __future__ import annotations

from videodown.web.site_config import CONTACT_EMAIL, SITE_BASE, SITE_NAME

ROBOTS_TXT = f"""User-agent: *
Allow: /

User-agent: GPTBot
Allow: /

User-agent: ChatGPT-User
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: anthropic-ai
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: PerplexityBot
Allow: /

Sitemap: {SITE_BASE}/sitemap.xml
"""

LLMS_TXT = f"""# {SITE_NAME}

> Free online video downloader and parser. Paste a share link from Douyin, Xiaohongshu (RED), YouTube, Bilibili, Kuaishou, X (Twitter) or TikTok, choose quality, save to phone or PC. No login required. Videos are streamed, not stored on disk.

## Canonical URL

- Chinese: {SITE_BASE}/?lang=zh
- English: {SITE_BASE}/?lang=en

## What VideoDown does

VideoDown is a web-based multimedia tool that:
1. Accepts pasted share URLs or share text from major video platforms
2. Parses available stream qualities server-side
3. Streams the selected file to the visitor's browser for local save

Privacy: temporary server-side buffering only during transfer; no long-term storage.

## Supported platforms

| Platform | Notes |
|----------|-------|
| Douyin (抖音) | Share links and short URLs |
| Xiaohongshu (小红书) | Server cookie may be required |
| YouTube | Public videos; cookie for age-restricted |
| Bilibili (哔哩哔哩) | May be region-sensitive |
| Kuaishou (快手) | Full /video/ links preferred over short URLs |
| X (Twitter) | Video posts via syndication API |
| TikTok | Mobile page parsing; full video URL preferred |

## How to use (visitors)

1. Copy video share link or full share text from the app
2. Open {SITE_BASE}
3. Paste into the URL field and click Parse
4. Select quality and download – browser saves the file locally

## HTTP API (for integrators)

- `POST /api/parse` – JSON body `{{"text": "<share text or url>"}}` → title, formats, url
- `GET /api/platforms` – live platform health probe
- `POST /api/stream` – form: url, title, ext, format_id → video stream

## Language

- `?lang=zh` – Simplified Chinese (default for CN/TW/HK/SG)
- `?lang=en` – English (suggested for US/EU visitors)
- Cookie `vd_lang` persists preference

## Contact

- Site: {SITE_BASE}
- Email: {CONTACT_EMAIL}

## Terms

For personal learning and research only. Respect platform terms of service and copyright.
"""


def sitemap_xml() -> str:
    """双语 hreflang sitemap。"""
    zh = f"{SITE_BASE}/?lang=zh"
    en = f"{SITE_BASE}/?lang=en"
    root = f"{SITE_BASE}/"
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:xhtml="http://www.w3.org/1999/xhtml">
  <url>
    <loc>{root}</loc>
    <changefreq>weekly</changefreq>
    <priority>1.0</priority>
    <xhtml:link rel="alternate" hreflang="zh-CN" href="{zh}"/>
    <xhtml:link rel="alternate" hreflang="en" href="{en}"/>
    <xhtml:link rel="alternate" hreflang="x-default" href="{zh}"/>
  </url>
  <url>
    <loc>{zh}</loc>
    <changefreq>weekly</changefreq>
    <priority>0.9</priority>
    <xhtml:link rel="alternate" hreflang="zh-CN" href="{zh}"/>
    <xhtml:link rel="alternate" hreflang="en" href="{en}"/>
    <xhtml:link rel="alternate" hreflang="x-default" href="{zh}"/>
  </url>
  <url>
    <loc>{en}</loc>
    <changefreq>weekly</changefreq>
    <priority>0.9</priority>
    <xhtml:link rel="alternate" hreflang="zh-CN" href="{zh}"/>
    <xhtml:link rel="alternate" hreflang="en" href="{en}"/>
    <xhtml:link rel="alternate" hreflang="x-default" href="{zh}"/>
  </url>
</urlset>
"""
