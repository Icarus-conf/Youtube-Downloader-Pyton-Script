# 📺 YouTube Downloader Web App

A premium, modern web application for downloading YouTube videos and audio with real-time progress tracking. Built with Flask, Socket.IO, and a beautiful glassmorphism UI.

![Premium Interface](/Users/icarus/.gemini/antigravity/brain/62578632-dd18-4e07-af52-272da7e3af93/thumbnail_verification_final_1764371684042.png)

## ✨ Features

### 🎥 Core Functionality
- **High Quality Video**: Download videos in 1080p, 720p, 480p, or 360p.
- **Audio Extraction**: Convert videos to high-quality MP3 audio automatically.
- **Playlist Support**: Download entire playlists with a single click.
- **Real-time Progress**: Live progress bar and status updates via WebSockets.

### 💎 Premium Experience
- **Smart Paste**: One-click button to paste URLs from your clipboard.
- **Visual History**: View your recent downloads with video thumbnails.
- **File Management**: Delete unwanted files directly from the interface.
- **Toast Notifications**: Smooth, non-intrusive alerts for actions.
- **Dark Mode UI**: Sleek, responsive design with glassmorphism effects.

## 🚀 Quick Start

### Option 1: Docker (Recommended)
The easiest way to run the app. Requires Docker Desktop.

```bash
# Start the app
docker compose up -d

# Stop the app
docker compose down
```
Access the app at **http://localhost:5001**

### Option 2: Local Python Setup
If you prefer running without Docker. Requires Python 3.8+ and ffmpeg.

1. **Install ffmpeg**
   ```bash
   brew install ffmpeg  # macOS
   sudo apt install ffmpeg  # Ubuntu
   ```

2. **Install Dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Run the Server**
   ```bash
   python app.py
   ```

## 🛠 Tech Stack

- **Backend**: Flask, Flask-SocketIO, Pytubefix
- **Frontend**: HTML5, CSS3 (Variables, Flexbox/Grid), JavaScript (ES6+)
- **Real-time**: Socket.IO (WebSockets)
- **Processing**: FFmpeg (Audio conversion/merging)
- **Deployment**: Docker & Docker Compose

## 📝 License
MIT License - Free to use and modify.
