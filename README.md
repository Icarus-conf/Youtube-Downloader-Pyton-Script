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
2. Install the required dependencies
3. Run the script:
   ```bash
   python yd.py
   ```
4. When prompted, enter the YouTube URL (video or playlist)
5. The download will start automatically and save to a `downloads` folder

## Example

```bash
$ python yd.py
Enter YouTube URL: https://www.youtube.com/watch?v=dQw4w9WgXcQ
Downloading: Rick Astley - Never Gonna Give You Up (Video)
[====================] 100% - 7.3MB/s - 7.4MB
Download complete! Saved as: downloads/Rick Astley - Never Gonna Give You Up (Video).mp4
```

## Features in Detail

- **Smart URL Handling**: Automatically handles youtu.be short links and normalizes YouTube URLs
- **Safe Filenames**: Removes special characters that could cause issues on different operating systems
- **No Overwrites**: Automatically appends numbers to avoid overwriting existing files
- **Progress Tracking**: See download progress and speed in real-time

## License

This project is open source and available under the [MIT License](LICENSE).

## Note

Please respect YouTube's Terms of Service and only download videos you have the right to access.
