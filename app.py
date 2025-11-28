"""
YouTube Downloader Web Application
Flask backend with WebSocket support for real-time progress updates
"""

import os
import re
import tempfile
import subprocess
import threading
import requests
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from pytubefix import YouTube, Playlist
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'youtube-downloader-secret-key'
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

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


def emit_progress(message, progress=None, video_info=None):
    """Emit progress update via WebSocket"""
    data = {'message': message}
    if progress is not None:
        data['progress'] = progress
    if video_info:
        data['video_info'] = video_info
    socketio.emit('download_progress', data)


# ---------------------- Core Download Functions ----------------------

def download_video_web(url, target_quality="720", audio_only=False):
    """Download video with WebSocket progress updates"""
    try:
        emit_progress("Fetching video information...", 0)
        
        def progress_callback(stream, chunk, bytes_remaining):
            total = stream.filesize
            downloaded = total - bytes_remaining
            percent = int((downloaded / total) * 100)
            emit_progress(f"Downloading... {percent}%", percent)
        
        yt = YouTube(url, on_progress_callback=progress_callback)
        
        video_info = {
            'title': yt.title,
            'author': yt.author,
            'duration': f"{yt.length // 60}m {yt.length % 60}s",
            'thumbnail': yt.thumbnail_url
        }
        
        emit_progress(f"Processing: {yt.title}", 10, video_info)
        
        emit_progress(f"Processing: {yt.title}", 10, video_info)

        def save_thumbnail(url, final_filename):
            """Save thumbnail with same basename as video/audio file"""
            try:
                # Get high res thumbnail
                thumb_url = url
                base_name = os.path.splitext(final_filename)[0]
                thumb_path = os.path.join(DOWNLOADS_DIR, f"{base_name}.jpg")
                
                response = requests.get(thumb_url)
                if response.status_code == 200:
                    with open(thumb_path, 'wb') as f:
                        f.write(response.content)
            except Exception as e:
                print(f"Failed to save thumbnail: {e}")

        if audio_only:
            emit_progress("Downloading audio only...", 20)
            stream = yt.streams.filter(only_audio=True).order_by("abr").desc().first()
            
            if not stream:
                emit_progress("Error: No audio stream found", 0)
                return {"success": False, "error": "No audio stream available"}
            
            audio_file_path = stream.download(output_path=DOWNLOADS_DIR)
            
            # Get the base name without extension and create MP3 path
            base_name = os.path.splitext(audio_file_path)[0]
            mp3_path = base_name + ".mp3"

            emit_progress("Converting to MP3...", 80)
            
            try:
                result = subprocess.run(
                    ["ffmpeg", "-y", "-i", audio_file_path, "-q:a", "0", "-map", "a", mp3_path],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    timeout=300  # 5 minute timeout
                )
                
                if result.returncode != 0:
                    error_msg = result.stderr.decode('utf-8', errors='ignore')
                    print(f"ffmpeg error: {error_msg}")
                    emit_progress(f"Conversion failed: {error_msg[:100]}", 0)
                    return {"success": False, "error": f"Audio conversion failed: {error_msg[:100]}"}
                
                # Remove original audio file only if conversion succeeded
                if os.path.exists(mp3_path) and os.path.getsize(mp3_path) > 0:
                    os.remove(audio_file_path)
                    save_thumbnail(yt.thumbnail_url, os.path.basename(mp3_path))
                    emit_progress("Download complete!", 100)
                    return {"success": True, "filename": os.path.basename(mp3_path), "type": "audio"}
                else:
                    emit_progress("Error: MP3 file not created properly", 0)
                    return {"success": False, "error": "MP3 conversion produced empty file"}
                    
            except subprocess.TimeoutExpired:
                emit_progress("Error: Conversion timeout", 0)
                return {"success": False, "error": "Audio conversion timed out"}
            except Exception as conv_error:
                emit_progress(f"Error: {str(conv_error)}", 0)
                return {"success": False, "error": f"Conversion error: {str(conv_error)}"}

        # List available resolutions
        available_res = sorted(
            {s.resolution for s in yt.streams.filter(adaptive=True, type="video") if s.resolution},
            key=lambda x: int(x.replace("p", "")), reverse=True
        )

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
            emit_progress("Using progressive stream fallback...", 30)
            stream = (
                yt.streams.filter(progressive=True, file_extension="mp4", res=f"{target_quality}p")
                .order_by("resolution").desc().first()
                or yt.streams.filter(progressive=True).order_by("resolution").desc().first()
            )
            file_path = stream.download(output_path=DOWNLOADS_DIR)
            save_thumbnail(yt.thumbnail_url, os.path.basename(file_path))
            emit_progress("Download complete!", 100)
            return {"success": True, "filename": os.path.basename(file_path), "type": "video"}

        audio_stream = audio_streams.first()
        emit_progress(f"Downloading video ({selected_video.resolution})...", 30)

        video_path = selected_video.download(output_path=tempfile.gettempdir(), filename_prefix="video_")
        
        emit_progress(f"Downloading audio ({audio_stream.abr})...", 60)
        audio_path = audio_stream.download(output_path=tempfile.gettempdir(), filename_prefix="audio_")

        output_file = get_unique_path(os.path.join(
            DOWNLOADS_DIR, f"{sanitize_filename(yt.title)} ({selected_video.resolution}).mp4"
        ))

        emit_progress("Merging audio and video...", 85)
        if merge_audio_video(video_path, audio_path, output_file):
            save_thumbnail(yt.thumbnail_url, os.path.basename(output_file))
            emit_progress("Download complete!", 100)
            return {"success": True, "filename": os.path.basename(output_file), "type": "video"}
        else:
            emit_progress("Merge failed, but files saved", 100)
            return {"success": False, "error": "Merge failed"}

    except Exception as e:
        emit_progress(f"Error: {str(e)}", 0)
        return {"success": False, "error": str(e)}


def download_playlist_web(url, target_quality="720", audio_only=False):
    """Download playlist with progress updates"""
    try:
        emit_progress("Fetching playlist information...", 0)
        pl = Playlist(url)
        total_videos = len(pl.videos)
        
        emit_progress(f"Playlist: {pl.title} ({total_videos} videos)", 5)
        
        results = []
        for idx, video in enumerate(pl.videos, 1):
            emit_progress(f"[{idx}/{total_videos}] {video.title}", int((idx / total_videos) * 90))
            result = download_video_web(video.watch_url, target_quality, audio_only)
            results.append(result)
        
        emit_progress("Playlist download complete!", 100)
        return {"success": True, "results": results, "type": "playlist"}
        
    except Exception as e:
        emit_progress(f"Error: {str(e)}", 0)
        return {"success": False, "error": str(e)}


# ---------------------- API Routes ----------------------

@app.route('/')
def index():
    """Serve the main web interface"""
    return render_template('index.html')


@app.route('/api/download', methods=['POST'])
def api_download():
    """API endpoint to initiate download"""
    data = request.json
    url = data.get('url', '').strip()
    quality = data.get('quality', '720')
    audio_only = data.get('audio_only', False)
    
    if not url:
        return jsonify({"success": False, "error": "URL is required"}), 400
    
    url = clean_youtube_url(url)
    
    # Start download in background thread
    def download_task():
        if "playlist" in url:
            download_playlist_web(url, quality, audio_only)
        else:
            download_video_web(url, quality, audio_only)
    
    thread = threading.Thread(target=download_task)
    thread.daemon = True
    thread.start()
    
    return jsonify({"success": True, "message": "Download started"})


@app.route('/api/downloads', methods=['GET'])
def api_downloads():
    """List all downloaded files"""
    try:
        files = []
        for filename in os.listdir(DOWNLOADS_DIR):
            filepath = os.path.join(DOWNLOADS_DIR, filename)
            if os.path.isfile(filepath):
                stat = os.stat(filepath)
                # Check for thumbnail
                thumb_name = os.path.splitext(filename)[0] + ".jpg"
                thumb_path = os.path.join(DOWNLOADS_DIR, thumb_name)
                has_thumbnail = os.path.exists(thumb_path)
                
                files.append({
                    'filename': filename,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'thumbnail': f"/api/thumbnails/{thumb_name}" if has_thumbnail else None
                })
        
        # Sort by modified time, newest first
        files.sort(key=lambda x: x['modified'], reverse=True)
        return jsonify({"success": True, "files": files})
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/download-file/<filename>')
def api_download_file(filename):
    """Download a specific file"""
    try:
        filepath = os.path.join(DOWNLOADS_DIR, filename)
        if not os.path.exists(filepath):
            return jsonify({"success": False, "error": "File not found"}), 404
        
        # Send file with explicit download name and attachment header
        # This triggers browser's "Save As" dialog
        return send_file(
            filepath, 
            as_attachment=True,
            download_name=filename
        )
    
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/downloads/<filename>', methods=['DELETE'])
def api_delete_file(filename):
    """Delete a downloaded file"""
    try:
        filepath = os.path.join(DOWNLOADS_DIR, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            
            # Also try to remove thumbnail if it exists
            thumb_name = os.path.splitext(filename)[0] + ".jpg"
            thumb_path = os.path.join(DOWNLOADS_DIR, thumb_name)
            if os.path.exists(thumb_path):
                os.remove(thumb_path)
                
            return jsonify({"success": True, "message": "File deleted"})
        return jsonify({"success": False, "error": "File not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/thumbnails/<filename>')
def api_thumbnail(filename):
    """Serve thumbnail image"""
    return send_file(os.path.join(DOWNLOADS_DIR, filename))



# ---------------------- WebSocket Events ----------------------

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print("Client connected")
    emit('connected', {'message': 'Connected to server'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print("Client disconnected")


# ---------------------- Main ----------------------

if __name__ == '__main__':
    print(f"YouTube Downloader Web App")
    print(f"Server starting on http://localhost:5001")
    print(f"Downloads directory: {DOWNLOADS_DIR}")
    socketio.run(app, host='0.0.0.0', port=5001, debug=True)
