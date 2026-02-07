# Xiaohongshu Video Downloader

[English](#english) | [中文](#中文)

<a name="english"></a>

A Claude Code skill for downloading videos from Xiaohongshu (小红书/RedNote) using [yt-dlp](https://github.com/yt-dlp/yt-dlp).

## Features

- Download Xiaohongshu videos in best available quality (up to 1080p)
- Support multiple URL formats (explore links, discovery links, short links)
- Automatic browser cookie extraction for authentication
- Configurable video quality (best / 1080p / 720p / 480p)
- Audio-only download mode (MP3)
- Format listing without downloading

## Prerequisites

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) installed (`brew install yt-dlp` on macOS or `pip install yt-dlp`)
- [ffmpeg](https://ffmpeg.org/) installed (`brew install ffmpeg` on macOS)
- Python 3.8+
- A browser logged into [xiaohongshu.com](https://www.xiaohongshu.com)

## Installation

### As a Claude Code Skill (Recommended)

Copy the skill to your Claude Code skills directory:

```bash
cp -r xiaohongshu-downloader ~/.claude/skills/
```

Then simply ask Claude: "download this xiaohongshu video: <URL>"

### Standalone Usage

```bash
python scripts/download_xiaohongshu.py "https://www.xiaohongshu.com/explore/VIDEO_ID"
```

## Supported URL Formats

| Format | Example |
|--------|---------|
| Explore link | `https://www.xiaohongshu.com/explore/<id>` |
| Discovery link | `https://www.xiaohongshu.com/discovery/item/<id>?xsec_token=...` |
| Short link | `http://xhslink.com/a/<id>` |

> **Tip:** Always copy the full share URL (including `xsec_token` parameters) from Xiaohongshu's share button for best results.

## Usage

### Basic Download

```bash
python scripts/download_xiaohongshu.py "URL"
```

### Options

| Option | Description | Default |
|--------|-------------|---------|
| `-o, --output` | Output directory | `~/Downloads` |
| `-q, --quality` | Video quality (`best`, `1080p`, `720p`, `480p`) | `best` |
| `--browser` | Browser for cookie extraction (`chrome`, `firefox`, `safari`, `none`) | `chrome` |
| `-a, --audio-only` | Download audio only as MP3 | `false` |
| `--list-formats` | List available formats without downloading | `false` |

### Examples

```bash
# Download with default settings (best quality, Chrome cookies)
python scripts/download_xiaohongshu.py "https://www.xiaohongshu.com/explore/69821980000000000e03c95f"

# Download in 720p
python scripts/download_xiaohongshu.py "URL" -q 720p

# Download to a specific directory
python scripts/download_xiaohongshu.py "URL" -o ~/Videos/

# Download audio only
python scripts/download_xiaohongshu.py "URL" -a

# List available formats
python scripts/download_xiaohongshu.py "URL" --list-formats

# Use Firefox cookies instead of Chrome
python scripts/download_xiaohongshu.py "URL" --browser firefox
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `No video formats found` | Log into xiaohongshu.com in your browser first, then retry with `--browser chrome` |
| `Unable to extract initial state` | CAPTCHA triggered — open the URL in your browser, solve it, then retry |
| Link expired | Copy a fresh share link from Xiaohongshu (tokens expire) |
| Low quality only | Maximum is 1080p (platform limitation). Use `-q best` |

## How It Works

This tool leverages yt-dlp's built-in XiaoHongShu extractor which:

1. Downloads the Xiaohongshu webpage and extracts `window.__INITIAL_STATE__` JSON
2. Parses video metadata including multiple codec formats (H.264, H.265/HEVC, AV1)
3. Uses browser cookies (`web_session`) to authenticate with the platform
4. Downloads the video stream and merges audio/video if needed via ffmpeg

## License

[MIT](LICENSE)

## Disclaimer

This tool is for personal and educational use only. Please respect copyright laws and Xiaohongshu's terms of service. Always ensure you have the right to download content before using this tool.

---

<a name="中文"></a>

# 小红书视频下载器

一个基于 [yt-dlp](https://github.com/yt-dlp/yt-dlp) 的 Claude Code 技能，用于下载小红书 (RedNote) 视频。

## 功能特点

- 下载小红书视频，最高画质可达 1080p
- 支持多种链接格式（探索链接、发现链接、短链接）
- 自动提取浏览器 Cookie 进行身份验证
- 可配置视频画质（best / 1080p / 720p / 480p）
- 仅下载音频模式（MP3）
- 列出可用格式（不下载）

## 前置要求

- 安装 [yt-dlp](https://github.com/yt-dlp/yt-dlp)：macOS 使用 `brew install yt-dlp`，或 `pip install yt-dlp`
- 安装 [ffmpeg](https://ffmpeg.org/)：macOS 使用 `brew install ffmpeg`
- Python 3.8+
- 浏览器已登录 [xiaohongshu.com](https://www.xiaohongshu.com)

## 安装

### 作为 Claude Code Skill 使用（推荐）

将 skill 复制到 Claude Code 技能目录：

```bash
cp -r xiaohongshu-downloader ~/.claude/skills/
```

然后直接对 Claude 说："帮我下载这个小红书视频：<链接>"

### 独立使用

```bash
python scripts/download_xiaohongshu.py "https://www.xiaohongshu.com/explore/视频ID"
```

## 支持的链接格式

| 格式 | 示例 |
|------|------|
| 探索链接 | `https://www.xiaohongshu.com/explore/<id>` |
| 发现链接 | `https://www.xiaohongshu.com/discovery/item/<id>?xsec_token=...` |
| 短链接 | `http://xhslink.com/a/<id>` |

> **提示：** 建议从小红书的分享按钮复制完整链接（包含 `xsec_token` 参数），效果最佳。

## 使用方法

### 基本下载

```bash
python scripts/download_xiaohongshu.py "链接"
```

### 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-o, --output` | 输出目录 | `~/Downloads` |
| `-q, --quality` | 视频画质（`best`, `1080p`, `720p`, `480p`） | `best` |
| `--browser` | 提取 Cookie 的浏览器（`chrome`, `firefox`, `safari`, `none`） | `chrome` |
| `-a, --audio-only` | 仅下载音频（MP3） | `false` |
| `--list-formats` | 列出可用格式（不下载） | `false` |

### 使用示例

```bash
# 默认设置下载（最佳画质，Chrome Cookie）
python scripts/download_xiaohongshu.py "https://www.xiaohongshu.com/explore/69821980000000000e03c95f"

# 下载 720p 画质
python scripts/download_xiaohongshu.py "链接" -q 720p

# 下载到指定目录
python scripts/download_xiaohongshu.py "链接" -o ~/Videos/

# 仅下载音频
python scripts/download_xiaohongshu.py "链接" -a

# 使用 Firefox Cookie
python scripts/download_xiaohongshu.py "链接" --browser firefox
```

## 常见问题

| 问题 | 解决方案 |
|------|----------|
| `No video formats found` | 先在浏览器中登录小红书，然后使用 `--browser chrome` 重试 |
| `Unable to extract initial state` | 触发了验证码 — 在浏览器中打开链接并完成验证，再重试 |
| 链接失效 | 从小红书重新复制分享链接（token 会过期） |
| 画质低 | 最高支持 1080p（平台限制），使用 `-q best` |

## 工作原理

本工具利用 yt-dlp 内置的小红书提取器：

1. 下载小红书网页，提取 `window.__INITIAL_STATE__` JSON 数据
2. 解析视频元数据，包括多种编码格式（H.264、H.265/HEVC、AV1）
3. 使用浏览器 Cookie（`web_session`）进行平台身份验证
4. 下载视频流，必要时通过 ffmpeg 合并音视频

## 许可证

[MIT](LICENSE)

## 免责声明

本工具仅供个人学习和教育用途。请遵守版权法和小红书的服务条款。使用前请确保您有权下载相关内容。

---

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=smile7up/xiaohongshu-downloader&type=Date)](https://star-history.com/#smile7up/xiaohongshu-downloader&Date)
