#!/usr/bin/env python3
"""
Xiaohongshu (小红书/RedNote) Downloader v2.1
Supports both video posts and image posts.
- Video post: downloads video + optional audio/subtitles/transcript/AI summary
- Image post: downloads all images + saves title and description as post.txt
"""

import argparse
import subprocess
import sys
import json
import re
import os
import glob as globmod
from pathlib import Path


def check_yt_dlp():
    """Check if yt-dlp is installed."""
    try:
        result = subprocess.run(["yt-dlp", "--version"], capture_output=True, text=True, check=True)
        print(f"yt-dlp version: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: yt-dlp is not installed.")
        print("Install it with: brew install yt-dlp (macOS) or pip install yt-dlp")
        return False


def check_ffmpeg():
    """Check if ffmpeg is installed."""
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: ffmpeg is not installed.")
        print("Install it with: brew install ffmpeg (macOS)")
        return False


def _normalize_url(url):
    """Convert rednote.com URLs to xiaohongshu.com so yt-dlp can handle them."""
    return url.replace('www.rednote.com', 'www.xiaohongshu.com')


def validate_url(url):
    """Validate that the URL is a Xiaohongshu URL."""
    patterns = [
        r'https?://www\.xiaohongshu\.com/(?:explore|discovery/item)/[\da-f]+',
        r'https?://www\.rednote\.com/(?:explore|discovery/item)/[\da-f]+',
        r'https?://xhslink\.com/',
    ]
    for pattern in patterns:
        if re.search(pattern, url):
            return True
    return False


def get_video_info(url, browser="chrome"):
    """Get video information without downloading."""
    url = _normalize_url(url)
    cmd = ["yt-dlp", "--dump-json", "--no-playlist"]
    if browser and browser != "none":
        cmd.extend(["--cookies-from-browser", browser])
    cmd.append(url)

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        stderr = e.stderr or ""
        if "Unable to extract initial state" in stderr:
            print("Error: Anti-scraping CAPTCHA triggered.")
            print("Solution: Open the URL in your browser, solve the CAPTCHA, then retry.")
            return None
        elif "No video formats found" in stderr:
            # Image post — yt-dlp found the page but no video; treat as image post
            # Try to salvage any partial JSON from stdout
            if e.stdout and e.stdout.strip():
                try:
                    return json.loads(e.stdout)
                except json.JSONDecodeError:
                    pass
            # Extract post ID from URL as fallback title
            id_match = re.search(r'/explore/([0-9a-f]+)', url)
            post_id = id_match.group(1) if id_match else 'unknown'
            return {'_is_image_post': True, 'title': post_id, 'uploader': 'Unknown', 'description': ''}
        else:
            print(f"Error getting video info: {stderr}")
            return None


def list_formats(url, browser="chrome"):
    """List all available formats for the video."""
    url = _normalize_url(url)
    cmd = ["yt-dlp", "--list-formats", "--no-playlist"]
    if browser and browser != "none":
        cmd.extend(["--cookies-from-browser", browser])
    cmd.append(url)
    subprocess.run(cmd)


def sanitize_title(title):
    """Sanitize the title for use as a directory name."""
    # Remove characters invalid in filenames
    sanitized = re.sub(r'[<>:"/\\|?*]', '', title)
    # Collapse whitespace
    sanitized = re.sub(r'\s+', ' ', sanitized).strip()
    # Truncate to reasonable length
    if len(sanitized) > 100:
        sanitized = sanitized[:100].rstrip()
    return sanitized or "untitled"


def detect_post_type(info):
    """Return 'video' or 'image' based on yt-dlp info dict."""
    if not info:
        return 'video'
    if info.get('_is_image_post'):
        return 'image'
    formats = info.get('formats', [])
    has_video_stream = any(
        f.get('vcodec') not in (None, 'none', '')
        for f in formats
    )
    if has_video_stream:
        return 'video'
    return 'image'


_MOBILE_UA = (
    'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) '
    'AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1'
)


def _parse_mobile_state(html):
    """Parse window.__INITIAL_STATE__ from mobile-UA page response.

    XHS serves a different SSR payload for mobile UAs that includes the full
    note data (imageList, title, desc) under state.noteData.data.noteData.

    Returns (image_urls, title, description) or ([], '', '') on failure.
    """
    idx = html.find('window.__INITIAL_STATE__')
    if idx == -1:
        return [], '', ''
    raw = html[idx + len('window.__INITIAL_STATE__='):]
    end = raw.find('</script>')
    raw = raw[:end].rstrip('; \n\r')
    raw = re.sub(r':\s*undefined\b', ': null', raw)
    try:
        state = json.loads(raw)
    except json.JSONDecodeError:
        return [], '', ''

    note_data = state.get('noteData', {}).get('data', {}).get('noteData', {})
    if not note_data:
        return [], '', ''

    title = note_data.get('title', '')
    description = note_data.get('desc', '')
    image_list = note_data.get('imageList', [])

    image_urls = []
    for img in image_list:
        # Prefer H5_DTL (1080px JPEG) from infoList, fall back to top-level url
        url = ''
        for entry in img.get('infoList', []):
            if entry.get('imageScene') == 'H5_DTL':
                url = entry.get('url', '')
                break
        if not url:
            url = img.get('url', '') or img.get('urlDefault', '')
        if url:
            image_urls.append(url)

    return image_urls, title, description


def _fetch_mobile_page(url, browser='chrome'):
    """Fetch a Xiaohongshu page with a mobile user-agent using yt-dlp's auth."""
    import tempfile, urllib.request, http.cookiejar, time as _time

    MAX_EXPIRY = int(_time.time()) + 10 * 365 * 86400

    # Export browser cookies to a temp file
    cookie_file = os.path.join(tempfile.gettempdir(), 'xhs_cookies.txt')
    subprocess.run(
        ["yt-dlp", "--cookies-from-browser", browser,
         "--cookies", cookie_file, "--skip-download", "--quiet", url],
        capture_output=True)

    cj = http.cookiejar.MozillaCookieJar()
    if os.path.exists(cookie_file):
        try:
            cj.load(cookie_file, ignore_discard=True, ignore_expires=True)
        except Exception:
            pass

    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    opener.addheaders = [
        ('User-Agent', _MOBILE_UA),
        ('Accept', 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'),
        ('Accept-Language', 'zh-CN,zh;q=0.9'),
        ('Referer', 'https://www.xiaohongshu.com/'),
    ]
    try:
        return opener.open(url, timeout=30).read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Warning: Mobile page fetch failed: {e}")
        return ''


def _download_image_urls(image_urls, output_dir):
    """Download a list of image URLs into output_dir, named 01.jpg, 02.jpg, …"""
    import urllib.request
    downloaded = []
    for i, img_url in enumerate(image_urls, 1):
        # Determine extension: prefer explicit suffix in URL, default jpg
        ext_match = re.search(r'!h5_\d+([a-z]+)$', img_url)
        if ext_match:
            ext = ext_match.group(1)
        else:
            ext_match2 = re.search(r'\.(jpe?g|png|webp|gif)(?:[?!@]|$)', img_url, re.IGNORECASE)
            ext = ext_match2.group(1).lower() if ext_match2 else 'jpg'
        dest = os.path.join(output_dir, f"{i:02d}.{ext}")
        try:
            req = urllib.request.Request(img_url, headers={
                'User-Agent': _MOBILE_UA,
                'Referer': 'https://www.xiaohongshu.com/',
            })
            with urllib.request.urlopen(req, timeout=30) as resp, open(dest, 'wb') as f:
                f.write(resp.read())
            size_kb = os.path.getsize(dest) / 1024
            print(f"  {i:02d}.{ext:4s}  {size_kb:.1f} KB")
            downloaded.append(dest)
        except Exception as e:
            print(f"  Warning: Failed to download image {i}: {e}")
    return downloaded


def download_image_post(url, info, output_path, browser="chrome", summary_mode=False):
    """Download all images and text from a Xiaohongshu image post."""
    url = _normalize_url(url)

    # Extract post ID for page parsing
    id_match = re.search(r'/explore/([0-9a-f]+)', url)
    post_id = id_match.group(1) if id_match else 'unknown'

    # Use info dict values if available; the fallback sentinel only has id as title
    title = (info.get('title', '') if info else '') or post_id
    description = info.get('description', '') if info else ''
    uploader = info.get('uploader', 'Unknown') if info else 'Unknown'

    safe_title = sanitize_title(title)
    output_dir = os.path.join(output_path, safe_title)
    os.makedirs(output_dir, exist_ok=True)

    print(f"Post ID: {post_id}")
    print(f"Uploader: {uploader}")
    print(f"Type: image post")
    print(f"Output: {output_dir}\n")

    image_exts = {'.jpg', '.jpeg', '.png', '.webp', '.gif'}

    # --- Strategy 1: yt-dlp native (works if XHS extractor ever gains image support) ---
    print("Image strategy 1/2: Trying yt-dlp native download...")
    pre_existing = set(os.listdir(output_dir))
    cmd = ["yt-dlp"]
    if browser and browser != "none":
        cmd.extend(["--cookies-from-browser", browser])
    cmd.extend(["-o", os.path.join(output_dir, "%(autonumber)02d.%(ext)s")])
    cmd.append(url)
    subprocess.run(cmd, capture_output=True, text=True)

    downloaded_images = sorted([
        f for f in os.listdir(output_dir)
        if os.path.splitext(f)[1].lower() in image_exts and f not in pre_existing
    ])

    # --- Strategy 2: mobile-UA page fetch + JSON parse ---
    if not downloaded_images:
        print("yt-dlp native failed. Trying mobile-UA page parse...")
        html = _fetch_mobile_page(url, browser) if browser and browser != "none" else ''
        image_urls, scraped_title, scraped_desc = _parse_mobile_state(html)

        if image_urls:
            print(f"Found {len(image_urls)} image(s). Downloading...")
            _download_image_urls(image_urls, output_dir)

        if scraped_title and scraped_title != post_id:
            title = scraped_title
            new_safe = sanitize_title(title)
            new_dir = os.path.join(output_path, new_safe)
            if new_dir != output_dir:
                if not os.path.exists(new_dir):
                    os.rename(output_dir, new_dir)
                    output_dir = new_dir
                else:
                    # Target dir already exists (e.g. re-running --summary) —
                    # move any new files in, then clean up the ID-named temp dir
                    for fname in os.listdir(output_dir):
                        src = os.path.join(output_dir, fname)
                        dst = os.path.join(new_dir, fname)
                        if not os.path.exists(dst):
                            os.rename(src, dst)
                    try:
                        os.rmdir(output_dir)
                    except OSError:
                        pass
                    output_dir = new_dir
        if scraped_desc:
            description = scraped_desc

        downloaded_images = sorted([
            f for f in os.listdir(output_dir)
            if os.path.splitext(f)[1].lower() in image_exts
        ])

    if not downloaded_images:
        print("\nError: Could not download images.")
        print("Tips:")
        print("  1. Make sure you are logged into xiaohongshu.com in Chrome")
        print("  2. Try opening the URL in your browser first, then retry")
        return False

    print(f"\nDownloaded {len(downloaded_images)} image(s).")

    # Save title + description to post.txt
    text_path = os.path.join(output_dir, "post.txt")
    with open(text_path, "w", encoding="utf-8") as f:
        f.write(f"{title}\n")
        if description and description.strip() != title.strip():
            f.write(f"\n{description}\n")
    print(f"Text saved: {text_path}")

    # Save metadata for Claude to use when generating summary
    if summary_mode:
        meta_path = os.path.join(output_dir, ".meta.json")
        meta = {
            "title": title,
            "url": url,
            "platform": "Xiaohongshu (小红书)",
            "uploader": uploader,
            "post_type": "image",
            "image_count": len(downloaded_images),
            "image_files": downloaded_images,
        }
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        print(f"Metadata saved: {meta_path}")
        print("Summary mode enabled — Claude will generate summary.md by reading the images.")

    # Print summary
    print(f"\n{'='*50}")
    print(f"Title: {title}")
    print(f"Resource pack saved to: {output_dir}")
    print(f"{'='*50}")
    for img in downloaded_images:
        size_kb = os.path.getsize(os.path.join(output_dir, img)) / 1024
        print(f"  {img:20s} {size_kb:>8.1f} KB")
    print(f"  {'post.txt':20s} (title + description)")
    if summary_mode:
        print(f"  {'.meta.json':20s} (metadata for summary)")

    return True


def extract_audio(video_path, output_dir):
    """Extract MP3 audio from a video file using ffmpeg.

    Args:
        video_path: Path to the input video file.
        output_dir: Directory to save audio.mp3.

    Returns:
        Path to the extracted audio file, or None on failure.
    """
    audio_path = os.path.join(output_dir, "audio.mp3")
    cmd = [
        "ffmpeg", "-i", video_path,
        "-vn",                    # no video
        "-acodec", "libmp3lame",  # MP3 codec
        "-q:a", "2",              # high quality (~190 kbps VBR)
        "-y",                     # overwrite
        audio_path,
    ]
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"Audio extracted: {audio_path}")
        return audio_path
    except subprocess.CalledProcessError as e:
        print(f"Error extracting audio: {e.stderr}")
        return None


def download_subtitles(url, output_dir, browser="chrome", audio_path=None):
    """Three-tier subtitle acquisition strategy.

    1. Try manual subtitles via yt-dlp --write-subs
    2. Try auto-generated subtitles via yt-dlp --write-auto-subs
    3. Fall back to local Whisper transcription via parallel_transcribe.py

    Args:
        url: Video URL.
        output_dir: Directory to save subtitle files.
        browser: Browser for cookie extraction.
        audio_path: Path to audio file (for Whisper fallback).

    Returns:
        Path to the VTT subtitle file, or None on failure.
    """
    vtt_path = os.path.join(output_dir, "subtitle.vtt")
    temp_prefix = os.path.join(output_dir, "temp_sub")

    # --- Strategy 1: Manual subtitles ---
    print("Subtitle strategy 1/3: Trying manual subtitles...")
    cmd = [
        "yt-dlp",
        "--write-subs",
        "--sub-lang", "zh,en,zh-Hans,zh-CN",
        "--sub-format", "vtt",
        "--skip-download",
        "--no-playlist",
        "-o", f"{temp_prefix}.%(ext)s",
    ]
    if browser and browser != "none":
        cmd.extend(["--cookies-from-browser", browser])
    cmd.append(url)

    subprocess.run(cmd, capture_output=True, text=True)
    found = _find_and_rename_vtt(output_dir, "temp_sub", vtt_path)
    if found:
        print(f"Manual subtitles found: {vtt_path}")
        return vtt_path

    # --- Strategy 2: Auto-generated subtitles ---
    print("Subtitle strategy 2/3: Trying auto-generated subtitles...")
    cmd = [
        "yt-dlp",
        "--write-auto-subs",
        "--sub-lang", "zh,en,zh-Hans,zh-CN",
        "--sub-format", "vtt",
        "--skip-download",
        "--no-playlist",
        "-o", f"{temp_prefix}.%(ext)s",
    ]
    if browser and browser != "none":
        cmd.extend(["--cookies-from-browser", browser])
    cmd.append(url)

    subprocess.run(cmd, capture_output=True, text=True)
    found = _find_and_rename_vtt(output_dir, "temp_sub", vtt_path)
    if found:
        print(f"Auto-generated subtitles found: {vtt_path}")
        return vtt_path

    # --- Strategy 3: Whisper local transcription ---
    print("Subtitle strategy 3/3: Falling back to Whisper transcription...")
    if not audio_path or not os.path.exists(audio_path):
        print("Warning: No audio file available for Whisper transcription.")
        return None

    script_dir = os.path.dirname(os.path.abspath(__file__))
    transcribe_script = os.path.join(script_dir, "parallel_transcribe.py")

    if not os.path.exists(transcribe_script):
        print("Warning: parallel_transcribe.py not found.")
        return None

    # Try uv run first, then fall back to direct python
    cmd_uv = ["uv", "run", transcribe_script, audio_path, "-o", output_dir]
    cmd_py = [sys.executable, transcribe_script, audio_path, "-o", output_dir]

    try:
        subprocess.run(cmd_uv, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("uv not available, trying direct Python execution...")
        try:
            subprocess.run(cmd_py, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Whisper transcription failed: {e}")
            return None

    if os.path.exists(vtt_path):
        print(f"Whisper transcription complete: {vtt_path}")
        return vtt_path

    print("Warning: Whisper transcription did not produce subtitle.vtt")
    return None


def _find_and_rename_vtt(output_dir, prefix, target_path):
    """Find any VTT files matching the prefix and rename to target."""
    pattern = os.path.join(output_dir, f"{prefix}*.vtt")
    matches = globmod.glob(pattern)
    if matches:
        # Pick the first match
        os.rename(matches[0], target_path)
        # Clean up any other temp subtitle files
        for f in globmod.glob(os.path.join(output_dir, f"{prefix}*")):
            try:
                os.remove(f)
            except OSError:
                pass
        return True
    return False


def generate_transcript(vtt_path, output_dir):
    """Strip timestamps from VTT to produce a plain text transcript.

    Args:
        vtt_path: Path to the VTT subtitle file.
        output_dir: Directory to save transcript.txt.

    Returns:
        Path to the transcript file, or None on failure.
    """
    transcript_path = os.path.join(output_dir, "transcript.txt")
    try:
        with open(vtt_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        text_lines = []
        seen = set()
        for line in lines:
            line = line.strip()
            # Skip WEBVTT header, timestamps, numeric cue IDs, empty lines
            if not line:
                continue
            if line.startswith("WEBVTT"):
                continue
            if line.startswith("NOTE"):
                continue
            if re.match(r'^\d+$', line):
                continue
            if re.match(r'\d{2}:\d{2}[\.:]\d{2}', line):
                continue
            # Remove VTT inline tags like <c>, </c>, <00:01:02.345>, etc.
            cleaned = re.sub(r'<[^>]+>', '', line).strip()
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                text_lines.append(cleaned)

        with open(transcript_path, "w", encoding="utf-8") as f:
            f.write("\n".join(text_lines) + "\n")

        print(f"Transcript generated: {transcript_path}")
        return transcript_path
    except Exception as e:
        print(f"Error generating transcript: {e}")
        return None


def download_video(url, output_path=None, quality="best", browser="chrome",
                   audio_only=False, full_mode=False, summary_mode=False):
    """
    Download a Xiaohongshu video, optionally as a full resource pack.

    Args:
        url: Xiaohongshu video URL
        output_path: Directory to save the video
        quality: Quality setting (best, 1080p, 720p, 480p)
        browser: Browser to extract cookies from
        audio_only: Download only audio
        full_mode: Enable full resource pack (video + audio + subtitles + transcript)
        summary_mode: Flag that summary.md is requested (handled by SKILL.md / Claude)
    """
    if not check_yt_dlp():
        return False

    if full_mode and not check_ffmpeg():
        return False

    if output_path is None:
        output_path = os.path.expanduser("~/Downloads")

    url = _normalize_url(url)

    # Get post info first
    info = get_video_info(url, browser)
    title = "Unknown"
    duration = 0
    uploader = "Unknown"
    if info:
        title = info.get("title", "Unknown")
        duration = int(info.get("duration", 0) or 0)
        uploader = info.get("uploader", "Unknown")

    # Detect post type and dispatch to image handler if needed
    post_type = detect_post_type(info)
    if post_type == 'image':
        print("Detected: image post (no video stream)\n")
        if full_mode and not summary_mode:
            print("Note: --full is not applicable to image posts (images are always downloaded).\n")
        return download_image_post(url, info, output_path, browser, summary_mode=summary_mode)

    # --- Video post ---
    if info:
        if duration:
            print(f"Title: {title}")
            print(f"Duration: {duration // 60}:{duration % 60:02d}")
            print(f"Uploader: {uploader}\n")
        else:
            print(f"Title: {title}")
            print(f"Uploader: {uploader}\n")

    # Determine output directory
    if full_mode:
        safe_title = sanitize_title(title)
        output_dir = os.path.join(output_path, safe_title)
        os.makedirs(output_dir, exist_ok=True)
        video_output = os.path.join(output_dir, "video.%(ext)s")
    else:
        output_dir = output_path
        video_output = os.path.join(output_path, "%(title)s [%(id)s].%(ext)s")

    # Build yt-dlp command
    cmd = ["yt-dlp"]

    if browser and browser != "none":
        cmd.extend(["--cookies-from-browser", browser])

    if audio_only:
        cmd.extend([
            "-x",
            "--audio-format", "mp3",
            "--audio-quality", "0",
        ])
    else:
        if quality == "best":
            format_string = "bestvideo+bestaudio/best"
        else:
            height = quality.replace("p", "")
            format_string = f"bestvideo[height<={height}]+bestaudio/best[height<={height}]"

        cmd.extend([
            "-f", format_string,
            "--merge-output-format", "mp4",
        ])

    cmd.extend([
        "-o", video_output,
        "--no-playlist",
    ])
    cmd.append(url)

    print(f"URL: {url}")
    print(f"Quality: {quality}")
    print(f"Format: {'mp3 (audio only)' if audio_only else 'mp4'}")
    print(f"Mode: {'full resource pack' if full_mode else 'video only'}")
    print(f"Cookies: from {browser}" if browser != "none" else "Cookies: none")
    print(f"Output: {output_dir}\n")

    # Download video
    try:
        subprocess.run(cmd, check=True)
        print(f"\nVideo download complete!")
    except subprocess.CalledProcessError as e:
        print(f"\nError downloading video: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure you're logged into xiaohongshu.com in your browser")
        print("2. Try copying a fresh share link (tokens expire)")
        print("3. If CAPTCHA appears, open the URL in browser first")
        return False

    if not full_mode:
        print(f"Saved to: {output_dir}")
        return True

    # --- Full resource pack mode ---
    # Find the downloaded video file
    video_path = None
    for ext in ["mp4", "mkv", "webm"]:
        candidate = os.path.join(output_dir, f"video.{ext}")
        if os.path.exists(candidate):
            video_path = candidate
            break

    if not video_path:
        print("Warning: Could not find downloaded video file for further processing.")
        return True

    # Step: Extract audio
    print("\n--- Extracting audio ---")
    audio_path = extract_audio(video_path, output_dir)

    # Step: Get subtitles
    print("\n--- Acquiring subtitles ---")
    vtt_path = download_subtitles(url, output_dir, browser, audio_path)

    # Step: Generate transcript from subtitles
    if vtt_path:
        print("\n--- Generating transcript ---")
        generate_transcript(vtt_path, output_dir)

    # If summary mode requested, write metadata for Claude to use
    if summary_mode:
        meta_path = os.path.join(output_dir, ".meta.json")
        meta = {
            "title": title,
            "url": url,
            "duration": f"{duration // 60}:{duration % 60:02d}" if duration else "unknown",
            "platform": "Xiaohongshu (小红书)",
            "uploader": uploader,
        }
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)
        print(f"\nMetadata saved: {meta_path}")
        print("Summary mode enabled — Claude will generate summary.md using the transcript.")

    # Print summary
    print(f"\n{'='*50}")
    print(f"Resource pack saved to: {output_dir}")
    print(f"{'='*50}")
    for fname in ["video.mp4", "audio.mp3", "subtitle.vtt", "transcript.txt"]:
        fpath = os.path.join(output_dir, fname)
        if os.path.exists(fpath):
            size_mb = os.path.getsize(fpath) / (1024 * 1024)
            print(f"  {fname:20s} {size_mb:>8.1f} MB")
        else:
            print(f"  {fname:20s} (not generated)")

    return True


def _read_batch_file(filepath):
    """Return list of (line_index, url) for all pending (non-done, non-blank, non-comment) lines."""
    with open(filepath, encoding='utf-8') as f:
        lines = f.readlines()
    pending = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        url = stripped.split()[0]
        pending.append((i, url))
    return pending


def _mark_done(filepath, line_index):
    """Prefix a line in the batch file with '# [done] ' to skip it on future runs."""
    with open(filepath, encoding='utf-8') as f:
        lines = f.readlines()
    lines[line_index] = '# [done] ' + lines[line_index]
    with open(filepath, 'w', encoding='utf-8') as f:
        f.writelines(lines)


def batch_download(filepath, output_path, quality, browser, audio_only, full_mode, summary_mode):
    """Download all pending URLs in a batch file, marking each done after success."""
    if not os.path.exists(filepath):
        print(f"Error: batch file not found: {filepath}")
        return False

    pending = _read_batch_file(filepath)
    if not pending:
        print("No pending URLs found in batch file.")
        return True

    print(f"Found {len(pending)} pending URL(s) in {filepath}\n")

    results = []
    for i, (line_idx, url) in enumerate(pending, 1):
        print(f"{'='*60}")
        print(f"[{i}/{len(pending)}] {url}")
        print(f"{'='*60}")
        try:
            success = download_video(
                url=url,
                output_path=output_path,
                quality=quality,
                browser=browser,
                audio_only=audio_only,
                full_mode=full_mode,
                summary_mode=summary_mode,
            )
        except Exception as e:
            print(f"Unexpected error: {e}")
            success = False

        results.append((url, success))
        if success:
            _mark_done(filepath, line_idx)
            print(f"\n[done] Marked as complete in batch file.\n")
        else:
            print(f"\n[failed] URL kept in batch file for retry.\n")

    print(f"{'='*60}")
    print(f"Batch complete: {sum(s for _, s in results)}/{len(results)} succeeded")
    failed = [u for u, s in results if not s]
    if failed:
        print("Failed URLs (still in batch file):")
        for u in failed:
            print(f"  {u}")
    return all(s for _, s in results)


def main():
    parser = argparse.ArgumentParser(
        description="Download Xiaohongshu (小红书) videos using yt-dlp"
    )
    parser.add_argument("url", nargs='?', help="Xiaohongshu video URL (explore, discovery, or xhslink.com)")
    parser.add_argument(
        "--batch",
        metavar="FILE",
        help="Batch download: read URLs from FILE, mark each done after success"
    )
    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Output directory (default: ~/Downloads)"
    )
    parser.add_argument(
        "-q", "--quality",
        default="best",
        choices=["best", "1080p", "720p", "480p"],
        help="Video quality (default: best)"
    )
    parser.add_argument(
        "--browser",
        default="chrome",
        choices=["chrome", "firefox", "safari", "none"],
        help="Browser to extract cookies from (default: chrome)"
    )
    parser.add_argument(
        "-a", "--audio-only",
        action="store_true",
        help="Download only audio as MP3"
    )
    parser.add_argument(
        "--list-formats",
        action="store_true",
        help="List available formats without downloading"
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Full resource pack: video + audio + subtitles + transcript"
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Enable AI summary mode (saves metadata for Claude to generate summary.md)"
    )

    args = parser.parse_args()

    if not args.url and not args.batch:
        parser.error("provide a URL or --batch FILE")

    # --summary implies --full
    if args.summary:
        args.full = True

    # Batch mode
    if args.batch:
        success = batch_download(
            filepath=args.batch,
            output_path=args.output,
            quality=args.quality,
            browser=args.browser,
            audio_only=args.audio_only,
            full_mode=args.full,
            summary_mode=args.summary,
        )
        sys.exit(0 if success else 1)

    # Single URL mode
    if not validate_url(args.url):
        print("Warning: URL does not match known Xiaohongshu patterns.")
        print("Supported formats:")
        print("  - https://www.xiaohongshu.com/explore/<id>")
        print("  - https://www.xiaohongshu.com/discovery/item/<id>")
        print("  - http://xhslink.com/a/<id>")
        print("Proceeding anyway...\n")

    if args.list_formats:
        list_formats(args.url, args.browser)
        return

    success = download_video(
        url=args.url,
        output_path=args.output,
        quality=args.quality,
        browser=args.browser,
        audio_only=args.audio_only,
        full_mode=args.full,
        summary_mode=args.summary,
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
