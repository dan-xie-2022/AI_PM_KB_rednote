---
name: xiaohongshu-downloader
description: Download and summarize Xiaohongshu (小红书/RedNote) posts — both videos and image posts. Produces a full resource pack with optional AI summary. This skill should be used when the user asks to "download xiaohongshu video", "下载小红书视频", "下载小红书图文", "总结小红书", "save rednote post", "download from xiaohongshu", "小红书视频下载", "总结小红书视频", "summarize xiaohongshu", or mentions downloading/summarizing content from xiaohongshu.com or xhslink.com.
version: 2.3.0
---

# Xiaohongshu Downloader & Summarizer

Download posts from Xiaohongshu (小红书/RedNote). The script **automatically detects** whether the URL is a video post or an image post and handles each accordingly.

## Workflow

Follow these steps in order:

### Step 1: Check Dependencies

```bash
yt-dlp --version
ffmpeg -version
```

Both must be available. If missing:
- `brew install yt-dlp` (macOS) or `pip install yt-dlp`
- `brew install ffmpeg` (macOS)

### Step 2: Get Post Information

```bash
python3 scripts/download_xiaohongshu.py "URL" --list-formats
```

This shows available formats and verifies the URL works with cookie authentication.

### Step 3: Download

The script auto-detects the post type. Use the same commands for both video and image posts:

For **basic download**:

```bash
python3 scripts/download_xiaohongshu.py "URL" -o content/
```

For **full resource pack** (video posts: + audio + subtitles + transcript; image posts: all images + text):

```bash
python3 scripts/download_xiaohongshu.py "URL" --full -o content/
```

For **full resource pack + AI summary** (both video and image posts):

```bash
python3 scripts/download_xiaohongshu.py "URL" --summary -o content/
```

**Video post** — `--full` creates `content/<title>/` with:
- `video.mp4` — original video
- `audio.mp3` — extracted audio
- `subtitle.vtt` — WebVTT subtitles (via 3-tier strategy)
- `transcript.txt` — plain text transcription

**Image post** — always creates `content/<title>/` with:
- `01.jpg`, `02.jpg`, … — all images in the post
- `post.txt` — post title and description text

When `--summary` is used on an image post, `.meta.json` is also saved and Claude will read the images to generate `summary.md`.

### Step 4: Subtitle Acquisition — Video Posts Only (Automatic 3-Tier Strategy)

1. **Manual subtitles** — `yt-dlp --write-subs --sub-lang zh,en,zh-Hans,zh-CN`
2. **Auto-generated subtitles** — `yt-dlp --write-auto-subs`
3. **Whisper local transcription** — Falls back to `parallel_transcribe.py` using faster-whisper

### Step 5: Generate Transcript — Video Posts Only (Automatic)

The script automatically strips timestamps from VTT to produce `transcript.txt`.

### Step 6: AI Summary — Video Posts (Claude generates summary.md from transcript)

If the user requested a summary on a **video post** (via `--summary` or by asking to "summarize"):

1. Read the transcript file:
   ```
   content/<video title>/transcript.txt
   ```

2. Read the metadata file:
   ```
   content/<video title>/.meta.json
   ```

3. Read the summary prompt template:
   ```
   reference/summary-prompt.md
   ```

4. Replace the template placeholders with actual values:
   - `{{TITLE}}` — from .meta.json
   - `{{URL}}` — from .meta.json
   - `{{DURATION}}` — from .meta.json
   - `{{PLATFORM}}` — "Xiaohongshu (小红书)"
   - `{{TRANSCRIPT}}` — contents of transcript.txt

5. Generate the summary following the template structure.

6. Save the result to:
   ```
   content/<video title>/summary.md
   ```

### Step 7: AI Summary — Image Posts (Claude reads images to generate summary.md)

If the user requested a summary on an **image post** (via `--summary` or by asking to "summarize"):

1. Read the instructions template:
   ```
   reference/image-summary-prompt.md
   ```

2. Read the metadata file:
   ```
   content/<post title>/.meta.json
   ```

3. Read `post.txt`:
   ```
   content/<post title>/post.txt
   ```

4. Read **every image** in the directory using the Read tool:
   ```
   content/<post title>/01.jpg
   content/<post title>/02.jpg
   … (all images listed in .meta.json → image_files)
   ```
   For each image, extract all visible text and identify what the slide is communicating.

5. Generate the summary following the output format in `reference/image-summary-prompt.md`.

6. Save the result to:
   ```
   content/<post title>/summary.md
   ```

## Options Reference

| Option | Description | Default |
|--------|-------------|---------|
| `-o, --output` | Output directory | `content/` |
| `-q, --quality` | Video quality (`best`, `1080p`, `720p`, `480p`) | `best` |
| `--browser` | Browser for cookies (`chrome`, `firefox`, `safari`, `none`) | `chrome` |
| `-a, --audio-only` | Download audio only as MP3 | `false` |
| `--list-formats` | List available formats | `false` |
| `--full` | Full resource pack mode | `false` |
| `--summary` | AI summary mode (implies `--full`) | `false` |

## Output Structure

### Video post — basic mode
```
content/
└── <title> [<id>].mp4
```

### Video post — full resource pack (`--full` or `--summary`)
```
content/<video title>/
├── video.mp4          # Original video
├── audio.mp3          # Extracted audio
├── subtitle.vtt       # WebVTT subtitles
├── transcript.txt     # Plain text transcript
├── .meta.json         # Video metadata (--summary only)
└── summary.md         # AI-generated summary (--summary only, written by Claude)
```

### Image post — basic / `--full`
```
content/<post title>/
├── 01.jpg             # First image
├── 02.jpg             # Second image
├── ...
└── post.txt           # Post title + description
```

### Image post — `--summary`
```
content/<post title>/
├── 01.jpg
├── 02.jpg
├── ...
├── post.txt           # Post title + description
├── .meta.json         # Metadata for summary generation
└── summary.md         # AI-generated summary (written by Claude after reading images)
```

## Supported URL Formats

| Format | Example |
|--------|---------|
| Explore link | `https://www.xiaohongshu.com/explore/676a35670000000013002578` |
| Discovery link | `https://www.xiaohongshu.com/discovery/item/676a35670000000013002578?xsec_token=TOKEN` |
| Short link | `http://xhslink.com/a/xxxxx` |

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `No video formats found` | Log into xiaohongshu.com in browser first, use `--browser chrome` |
| `Unable to extract initial state` | CAPTCHA triggered — open URL in browser, solve it, retry |
| Link expired | Copy fresh share link (tokens expire) |
| No subtitles found | Script will fall back to Whisper transcription automatically |
| Whisper not available | Install uv (`brew install uv`) for automatic dependency management |

## Important Notes

- Always use the **full share URL** (with `xsec_token`) for best results
- Log into xiaohongshu.com in your browser before downloading
- Maximum video quality is typically 1080p (platform limitation)
- Whisper transcription requires `uv` for automatic dependency management, or `faster-whisper` installed manually
- Respect copyright and Xiaohongshu's terms of service
