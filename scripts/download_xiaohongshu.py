#!/usr/bin/env python3
"""
Xiaohongshu (小红书/RedNote) Video Downloader
Downloads videos from Xiaohongshu using yt-dlp's built-in XiaoHongShu extractor.
"""

import argparse
import subprocess
import sys
import json
import re
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


def validate_url(url):
    """Validate that the URL is a Xiaohongshu URL."""
    patterns = [
        r'https?://www\.xiaohongshu\.com/(?:explore|discovery/item)/[\da-f]+',
        r'https?://xhslink\.com/',
    ]
    for pattern in patterns:
        if re.search(pattern, url):
            return True
    return False


def get_video_info(url, browser="chrome"):
    """Get video information without downloading."""
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
        elif "No video formats found" in stderr:
            print("Error: No video formats found.")
            print("Solution: Make sure you're logged into xiaohongshu.com in your browser.")
        else:
            print(f"Error getting video info: {stderr}")
        return None


def list_formats(url, browser="chrome"):
    """List all available formats for the video."""
    cmd = ["yt-dlp", "--list-formats", "--no-playlist"]
    if browser and browser != "none":
        cmd.extend(["--cookies-from-browser", browser])
    cmd.append(url)
    subprocess.run(cmd)


def download_video(url, output_path=None, quality="best", browser="chrome",
                   audio_only=False):
    """
    Download a Xiaohongshu video.

    Args:
        url: Xiaohongshu video URL
        output_path: Directory to save the video
        quality: Quality setting (best, 1080p, 720p, 480p)
        browser: Browser to extract cookies from
        audio_only: Download only audio
    """
    if not check_yt_dlp():
        return False

    if output_path is None:
        import os
        output_path = os.path.expanduser("~/Downloads")

    cmd = ["yt-dlp"]

    # Cookie authentication
    if browser and browser != "none":
        cmd.extend(["--cookies-from-browser", browser])

    if audio_only:
        cmd.extend([
            "-x",
            "--audio-format", "mp3",
            "--audio-quality", "0",
        ])
    else:
        # Video quality settings
        if quality == "best":
            format_string = "bestvideo+bestaudio/best"
        else:
            height = quality.replace("p", "")
            format_string = f"bestvideo[height<={height}]+bestaudio/best[height<={height}]"

        cmd.extend([
            "-f", format_string,
            "--merge-output-format", "mp4",
        ])

    # Output template
    cmd.extend([
        "-o", f"{output_path}/%(title)s [%(id)s].%(ext)s",
        "--no-playlist",
    ])

    cmd.append(url)

    print(f"URL: {url}")
    print(f"Quality: {quality}")
    print(f"Format: {'mp3 (audio only)' if audio_only else 'mp4'}")
    print(f"Cookies: from {browser}" if browser != "none" else "Cookies: none")
    print(f"Output: {output_path}\n")

    # Get video info first
    info = get_video_info(url, browser)
    if info:
        title = info.get("title", "Unknown")
        duration = int(info.get("duration", 0) or 0)
        uploader = info.get("uploader", "Unknown")
        if duration:
            print(f"Title: {title}")
            print(f"Duration: {duration // 60}:{duration % 60:02d}")
            print(f"Uploader: {uploader}\n")
        else:
            print(f"Title: {title}")
            print(f"Uploader: {uploader}\n")

    try:
        subprocess.run(cmd, check=True)
        print(f"\nDownload complete! Saved to: {output_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\nError downloading video: {e}")
        print("\nTroubleshooting tips:")
        print("1. Make sure you're logged into xiaohongshu.com in your browser")
        print("2. Try copying a fresh share link (tokens expire)")
        print("3. If CAPTCHA appears, open the URL in browser first")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Download Xiaohongshu (小红书) videos using yt-dlp"
    )
    parser.add_argument("url", help="Xiaohongshu video URL (explore, discovery, or xhslink.com)")
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

    args = parser.parse_args()

    # Validate URL
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
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
