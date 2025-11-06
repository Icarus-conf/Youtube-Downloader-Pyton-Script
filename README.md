# YouTube Video Downloader

A simple Python script to download YouTube videos and playlists with progress tracking and proper error handling.

## Features

- Download single YouTube videos
- Download entire playlists
- Progress bar with download status
- Clean filenames (removes illegal characters)
- Prevents file overwrites with automatic numbering
- Supports both standard YouTube URLs and youtu.be short links

## Prerequisites

- Python 3.6+
- Required packages (install via `pip`):
    ```bash
    pip install pytubefix colorama
    ```

## Usage

1. Clone this repository or download the script
    ```bash
    git clone https://github.com/yourusername/youtube-downloader.git
    cd youtube-downloader
    ```

2. Install the required dependencies
    ```bash
    pip install -r requirements.txt
    ```

3. Run the script:
    ```bash
    python yd.py
    ```

4. When prompted, enter the YouTube URL (video or playlist)
5. The download will start automatically and save to a `downloads` folder

## Example

    ```bash
    $ python yd.py
    Enter YouTube URL: https://www.youtube.com/watch?v=xnP7qKxwzjg
    Download (v)ideo or (a)udio only? [v/a]: v
    Quality (1080, 720, 480, 360): 720

    🎬 Tame Impala - Dracula (Official Video)
    📺 tameimpalaVEVO
    ⏱ Duration: 3m 53s

    🎞 Available resolutions: 2160p, 1440p, 1080p, 720p, 480p, 360p, 240p, 144p
    🎥 Downloading video (720p) ...
    🎧 Downloading audio (160kbps) ...
    💾 Estimated final size: 17.62 MB
    🔄 Merging audio and video ...
    ✅ Download complete: /Users/icarus/python/downloads/Tame Impala - Dracula (Official Video) (720p).mp4
    ```

## Features in Detail

- **Smart URL Handling**: Automatically handles youtu.be short links and normalizes YouTube URLs
- **Safe Filenames**: Removes special characters that could cause issues on different operating systems
- **No Overwrites**: Automatically appends numbers to avoid overwriting existing files
- **Progress Tracking**: See download progress and speed in real-time


## Note

Please respect YouTube's Terms of Service and only download videos you have the right to access.
