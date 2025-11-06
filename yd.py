import os
import re
import tempfile
import subprocess
from pytubefix import YouTube, Playlist
from pytubefix.cli import on_progress
from colorama import Fore, Style, init

init(autoreset=True)

DOWNLOADS_DIR = os.path.join(os.getcwd(), "downloads")
os.makedirs(DOWNLOADS_DIR, exist_ok=True)


# ---------------------- Helpers ----------------------

def sanitize_filename(name: str) -> str:
    """Remove illegal filename characters for macOS."""
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()


def get_unique_path(path: str) -> str:
    """Ensure unique filename (avoid overwriting)."""
    base, ext = os.path.splitext(path)
    counter = 1
    while os.path.exists(path):
        path = f"{base}_{counter}{ext}"
        counter += 1
    return path


def clean_youtube_url(url: str) -> str:
    """Normalize YouTube URLs (handle youtu.be short links)."""
    match = re.match(r"https?://youtu\.be/([a-zA-Z0-9_-]{11})", url)
    if match:
        video_id = match.group(1)
        return f"https://www.youtube.com/watch?v={video_id}"
    if "watch?v=" in url:
        url = url.split("&")[0]
    return url


def merge_audio_video(video_path, audio_path, output_path):
    """Merge video + audio using ffmpeg."""
    try:
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", video_path,
                "-i", audio_path,
                "-c:v", "copy",
                "-c:a", "aac",
                "-filter:a", "loudnorm",
                output_path
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
        os.remove(video_path)
        os.remove(audio_path)
        return True
    except Exception:
        return False


# ---------------------- Core ----------------------

def download_video(url, target_quality="720", audio_only=False):
    try:
        yt = YouTube(url, on_progress_callback=on_progress)
        print(Fore.CYAN + f"\n🎬 {yt.title}")
        print(Fore.YELLOW + f"📺 {yt.author}")
        print(Fore.MAGENTA + f"⏱ Duration: {yt.length // 60}m {yt.length % 60}s\n")

        if audio_only:
            print(Fore.GREEN + "🎵 Downloading audio only ...")
            stream = yt.streams.filter(only_audio=True).order_by("abr").desc().first()
            mp4_path = stream.download(output_path=DOWNLOADS_DIR)
            mp3_path = mp4_path.replace(".mp4", ".mp3")

            subprocess.run(
                ["ffmpeg", "-y", "-i", mp4_path, mp3_path],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            os.remove(mp4_path)
            print(Fore.GREEN + f"✅ Audio saved as: {mp3_path}\n")
            return

        # List available resolutions
        available_res = sorted(
            {s.resolution for s in yt.streams.filter(adaptive=True, type="video") if s.resolution},
            key=lambda x: int(x.replace("p", "")), reverse=True
        )
        print(Fore.CYAN + f"🎞 Available resolutions: {', '.join(available_res)}")

        target_quality = str(target_quality).replace("p", "")

        # Select video & audio streams
        video_streams = yt.streams.filter(adaptive=True, type="video", file_extension="mp4").order_by("resolution").desc()
        audio_streams = yt.streams.filter(adaptive=True, type="audio").order_by("abr").desc()

        selected_video = None
        for s in video_streams:
            res = int(s.resolution.replace("p", ""))
            if res <= int(target_quality):
                selected_video = s
                break
        if not selected_video:
            selected_video = video_streams.first()

        if not selected_video or not audio_streams:
            print(Fore.RED + "⚠️ No suitable adaptive stream found, trying progressive fallback...")
            stream = (
                yt.streams.filter(progressive=True, file_extension="mp4", res=f"{target_quality}p")
                .order_by("resolution").desc().first()
                or yt.streams.filter(progressive=True).order_by("resolution").desc().first()
            )
            file_path = stream.download(output_path=DOWNLOADS_DIR)
            print(Fore.GREEN + f"\n✅ Download complete: {file_path}\n")
            return

        audio_stream = audio_streams.first()
        print(Fore.GREEN + f"🎥 Downloading video ({selected_video.resolution}) ...")
        print(Fore.GREEN + f"🎧 Downloading audio ({audio_stream.abr}) ...")

        video_path = selected_video.download(output_path=tempfile.gettempdir(), filename_prefix="video_")
        audio_path = audio_stream.download(output_path=tempfile.gettempdir(), filename_prefix="audio_")

        output_file = get_unique_path(os.path.join(
            DOWNLOADS_DIR, f"{sanitize_filename(yt.title)} ({selected_video.resolution}).mp4"
        ))

        est_size = round((selected_video.filesize + audio_stream.filesize) / (1024 * 1024), 2)
        print(Fore.YELLOW + f"💾 Estimated final size: {est_size} MB")

        print(Fore.CYAN + "🔄 Merging audio and video ...")
        if merge_audio_video(video_path, audio_path, output_file):
            print(Fore.GREEN + f"✅ Download complete: {output_file}\n")
        else:
            print(Fore.RED + f"⚠️ Merge failed. Files saved separately.\n")

    except Exception as e:
        print(Fore.RED + f"❌ Error downloading video: {e}")


def download_playlist(url, target_quality="720", audio_only=False):
    try:
        pl = Playlist(url)
        print(Fore.CYAN + f"\n📜 Playlist: {pl.title}")
        print(Fore.YELLOW + f"📼 Videos: {len(pl.videos)}\n")

        for idx, video in enumerate(pl.videos, 1):
            print(Fore.MAGENTA + f"\n➡️ [{idx}/{len(pl.videos)}] {video.title}")
            download_video(video.watch_url, target_quality, audio_only)

        print(Fore.GREEN + "\n✅ Playlist download complete!\n")

    except Exception as e:
        print(Fore.RED + f"❌ Error downloading playlist: {e}")


# ---------------------- Entry ----------------------

def main():
    print(Fore.CYAN + "=== 🎥 YouTube Downloader ===")
    url = input("Enter YouTube video or playlist URL: ").strip()
    url = clean_youtube_url(url)

    mode = input("Download (v)ideo or (a)udio only? [v/a]: ").lower().strip() or "v"
    audio_only = mode == "a"

    quality = None
    if not audio_only:
        quality = input("Quality (1080, 720, 480, 360): ").strip() or "720"

    if "playlist" in url:
        download_playlist(url, quality, audio_only)
    else:
        download_video(url, quality, audio_only)


if __name__ == "__main__":
    main()