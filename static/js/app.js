// ==================== Configuration ====================
const socket = io();
let isDownloading = false;
let audioOnly = false;

// ==================== DOM Elements ====================
const downloadForm = document.getElementById('downloadForm');
const urlInput = document.getElementById('url');
const qualitySelect = document.getElementById('quality');
const downloadBtn = document.getElementById('downloadBtn');
const toggleBtns = document.querySelectorAll('.toggle-btn');
const progressSection = document.getElementById('progressSection');
const progressBar = document.getElementById('progressBar');
const progressPercent = document.getElementById('progressPercent');
const progressTitle = document.getElementById('progressTitle');
const progressMessage = document.getElementById('progressMessage');
const videoInfo = document.getElementById('videoInfo');
const videoThumbnail = document.getElementById('videoThumbnail');
const videoTitle = document.getElementById('videoTitle');
const videoAuthor = document.getElementById('videoAuthor');
const videoDuration = document.getElementById('videoDuration');
const downloadsList = document.getElementById('downloadsList');

// ==================== Socket.IO Events ====================
socket.on('connect', () => {
    console.log('Connected to server');
});

socket.on('download_progress', (data) => {
    updateProgress(data);
});

socket.on('disconnect', () => {
    console.log('Disconnected from server');
});

const pasteBtn = document.getElementById('pasteBtn');

// ==================== Toast System ====================
function showToast(message, type = 'info') {
    const container = document.querySelector('.toast-container') || createToastContainer();

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <span class="toast-icon">${getToastIcon(type)}</span>
        <span class="toast-message">${message}</span>
    `;

    container.appendChild(toast);

    // Remove after 3 seconds
    setTimeout(() => {
        toast.style.animation = 'fadeOut 0.3s forwards';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function createToastContainer() {
    const container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
    return container;
}

function getToastIcon(type) {
    switch (type) {
        case 'success': return '✅';
        case 'error': return '❌';
        default: return 'ℹ️';
    }
}

// ==================== Event Listeners ====================
downloadForm.addEventListener('submit', handleDownload);

pasteBtn.addEventListener('click', async () => {
    try {
        const text = await navigator.clipboard.readText();
        if (text) {
            urlInput.value = text;
            showToast('Pasted from clipboard', 'success');
        }
    } catch (err) {
        showToast('Failed to read clipboard', 'error');
    }
});

toggleBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
        toggleBtns.forEach(b => b.classList.remove('active'));
        e.target.closest('.toggle-btn').classList.add('active');
        audioOnly = e.target.closest('.toggle-btn').dataset.value === 'audio';

        // Disable quality select for audio
        qualitySelect.disabled = audioOnly;
    });
});

// ==================== Functions ====================

async function handleDownload(e) {
    e.preventDefault();

    if (isDownloading) return;

    const url = urlInput.value.trim();
    const quality = qualitySelect.value;

    if (!url) {
        showToast('Please enter a YouTube URL', 'error');
        return;
    }

    // Start download
    isDownloading = true;
    downloadBtn.disabled = true;
    downloadBtn.classList.add('loading');
    downloadBtn.innerHTML = `
        <div class="spinner"></div>
        Processing...
    `;

    // Show progress section
    progressSection.classList.remove('hidden');
    videoInfo.classList.add('hidden');
    resetProgress();

    try {
        const response = await fetch('/api/download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                url: url,
                quality: quality,
                audio_only: audioOnly
            })
        });

        const result = await response.json();

        if (!result.success) {
            throw new Error(result.error || 'Download failed');
        }

        showToast('Download started', 'info');

    } catch (error) {
        console.error('Download error:', error);
        showToast(error.message, 'error');
        resetDownloadButton();
        progressSection.classList.add('hidden');
    }
}

function updateProgress(data) {
    const { message, progress, video_info } = data;

    progressMessage.textContent = message;

    if (progress !== undefined) {
        progressBar.style.width = `${progress}%`;
        progressPercent.textContent = `${progress}%`;

        if (progress === 100) {
            progressTitle.textContent = 'Download Complete! ✓';
            showToast('Download completed successfully!', 'success');
            setTimeout(() => {
                resetDownloadButton();
                loadDownloads();
            }, 2000);
        } else if (progress === 0 && message && message.toLowerCase().includes('error')) {
            // Show the actual error message as the title
            progressTitle.textContent = '❌ ' + message;
            progressMessage.textContent = 'Check terminal for details.';
            showToast(message, 'error');
            setTimeout(() => {
                resetDownloadButton();
                progressSection.classList.add('hidden');
            }, 5000);
        }
    }

    if (video_info) {
        showVideoInfo(video_info);
    }
}

function showVideoInfo(info) {
    videoThumbnail.src = info.thumbnail;
    videoTitle.textContent = info.title;
    videoAuthor.textContent = info.author;
    videoDuration.textContent = info.duration;
    videoInfo.classList.remove('hidden');
}

function resetProgress() {
    progressBar.style.width = '0%';
    progressPercent.textContent = '0%';
    progressTitle.textContent = 'Preparing download...';
    progressMessage.textContent = '';
}

function resetDownloadButton() {
    isDownloading = false;
    downloadBtn.disabled = false;
    downloadBtn.classList.remove('loading');
    downloadBtn.innerHTML = `
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
            <polyline points="7 10 12 15 17 10"></polyline>
            <line x1="12" y1="15" x2="12" y2="3"></line>
        </svg>
        Download
    `;
}

async function loadDownloads() {
    try {
        const response = await fetch('/api/downloads');
        const result = await response.json();

        if (result.success && result.files.length > 0) {
            displayDownloads(result.files);
        } else {
            downloadsList.innerHTML = '<p style="color: var(--text-secondary); text-align: center;">No downloads yet</p>';
        }
    } catch (error) {
        console.error('Error loading downloads:', error);
    }
}

function displayDownloads(files) {
    downloadsList.innerHTML = '';

    files.forEach(file => {
        // Skip thumbnail files in the list
        if (file.filename.endsWith('.jpg')) return;

        const card = document.createElement('div');
        card.className = 'download-card';

        const fileSize = formatFileSize(file.size);
        const fileName = file.filename;
        const fileType = fileName.endsWith('.mp3') ? '🎵 Audio' : '🎥 Video';

        // Use thumbnail if available, otherwise generic placeholder
        const thumbHtml = file.thumbnail
            ? `<img src="${file.thumbnail}" class="card-thumbnail" alt="${fileName}">`
            : `<div class="card-thumbnail" style="display:flex;align-items:center;justify-content:center;color:var(--text-muted)">
                 <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
                    <rect x="2" y="2" width="20" height="20" rx="5" ry="5"></rect>
                    <path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37z"></path>
                    <line x1="17.5" y1="6.5" x2="17.51" y2="6.5"></line>
                 </svg>
               </div>`;

        card.innerHTML = `
            <button class="delete-btn" onclick="deleteFile('${fileName}')" title="Delete file">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="3 6 5 6 21 6"></polyline>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                </svg>
            </button>
            ${thumbHtml}
            <h4 title="${fileName}">${fileName}</h4>
            <div class="download-meta">
                <span>${fileType}</span>
                <span>${fileSize}</span>
            </div>
            <button class="download-card-btn" onclick="downloadFile('${fileName}')">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                    <polyline points="7 10 12 15 17 10"></polyline>
                    <line x1="12" y1="15" x2="12" y2="3"></line>
                </svg>
                Download
            </button>
        `;

        downloadsList.appendChild(card);
    });
}

async function deleteFile(filename) {
    if (!confirm(`Are you sure you want to delete "${filename}"?`)) return;

    try {
        const response = await fetch(`/api/downloads/${encodeURIComponent(filename)}`, {
            method: 'DELETE'
        });
        const result = await response.json();

        if (result.success) {
            showToast('File deleted successfully', 'success');
            loadDownloads();
        } else {
            showToast(result.error || 'Failed to delete file', 'error');
        }
    } catch (error) {
        showToast('Error deleting file', 'error');
    }
}

function downloadFile(filename) {
    window.location.href = `/api/download-file/${encodeURIComponent(filename)}`;
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// ==================== Initialize ====================
loadDownloads();
