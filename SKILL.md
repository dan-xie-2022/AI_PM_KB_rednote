---
name: xiaohongshu-downloader
description: Download Xiaohongshu (小红书/RedNote) videos to local storage. This skill should be used when the user asks to "download xiaohongshu video", "下载小红书视频", "save rednote video", "download from xiaohongshu", "小红书视频下载", or mentions downloading content from xiaohongshu.com or xhslink.com. Supports multiple URL formats and quality options.
version: 1.0.0
---

# Xiaohongshu Video Downloader

Download videos from Xiaohongshu (小红书/RedNote) using yt-dlp with built-in XiaoHongShu extractor support.

## Quick Start

The simplest way to download a video:

```bash
python scripts/download_xiaohongshu.py "https://www.xiaohongshu.com/explore/VIDEO_ID"
```

This downloads the video in best available quality as MP4 to `~/Downloads/`.

## Supported URL Formats

Three URL formats are supported:

| Format | Example |
|--------|---------|
| Explore link | `https://www.xiaohongshu.com/explore/676a35670000000013002578` |
| Discovery link | `https://www.xiaohongshu.com/discovery/item/676a35670000000013002578?source=webshare&xhsshare=pc_web&xsec_token=TOKEN&xsec_source=pc_share` |
| Short link | `http://xhslink.com/a/xxxxx` |

When copying from Xiaohongshu's share button, always use the full URL including all query parameters (`xsec_token`, `xsec_source`, etc.), as these are needed for authentication.

## Options

### Cookie Authentication

Use `--browser` to specify which browser to extract cookies from (required for most videos):

- `chrome` (default): Google Chrome
- `firefox`: Mozilla Firefox
- `safari`: Safari
- `none`: Skip cookie extraction

Example:
```bash
python scripts/download_xiaohongshu.py "URL" --browser chrome
```

### Quality Settings

Use `-q` or `--quality` to specify video quality:

- `best` (default): Highest quality available (typically 1080p)
- `1080p`: Full HD
- `720p`: HD
- `480p`: Standard definition

Example:
```bash
python scripts/download_xiaohongshu.py "URL" -q 720p
```

### Custom Output Directory

Use `-o` or `--output` to specify a different output directory:

```bash
python scripts/download_xiaohongshu.py "URL" -o /path/to/directory
```

### Audio Only

Use `-a` or `--audio-only` to download only audio:

```bash
python scripts/download_xiaohongshu.py "URL" -a
```

### List Formats

Use `--list-formats` to see all available formats without downloading:

```bash
python scripts/download_xiaohongshu.py "URL" --list-formats
```

## Complete Examples

1. Download video with Chrome cookies (recommended):
```bash
python scripts/download_xiaohongshu.py "https://www.xiaohongshu.com/explore/676a35670000000013002578" --browser chrome
```

2. Download from a share link:
```bash
python scripts/download_xiaohongshu.py "https://www.xiaohongshu.com/discovery/item/676a35670000000013002578?source=webshare&xhsshare=pc_web&xsec_token=TOKEN&xsec_source=pc_share"
```

3. Download in 720p to custom directory:
```bash
python scripts/download_xiaohongshu.py "URL" -q 720p -o ~/Videos/
```

4. Download audio only:
```bash
python scripts/download_xiaohongshu.py "URL" -a
```

## How It Works

The skill uses yt-dlp's built-in XiaoHongShu extractor which:
- Parses `window.__INITIAL_STATE__` from the webpage to extract video metadata
- Supports H.264, H.265/HEVC, and AV1 codec formats
- Extracts video streams at various qualities (up to 1080p)
- Handles URL redirects from short links (xhslink.com)
- Uses browser cookies to authenticate and bypass anti-scraping measures

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `No video formats found` | Ensure browser cookies are passed: `--browser chrome`. Log into xiaohongshu.com in Chrome first. |
| `Unable to extract initial state` | CAPTCHA triggered. Open the URL in browser first, solve CAPTCHA, then retry. |
| Link expires | Copy a fresh share link from Xiaohongshu — `xsec_token` parameters expire. |
| Low quality only | Maximum available is 1080p. Use `-q best` for highest quality. |

## Important Notes

- Downloads are saved to `~/Downloads/` by default
- Always use the **full share URL** (with `xsec_token`) for best results
- Log into xiaohongshu.com in your browser before downloading
- Maximum video quality is typically 1080p (platform limitation)
- Respect copyright and Xiaohongshu's terms of service
- The `web_session` cookie from your browser is the key authentication credential
