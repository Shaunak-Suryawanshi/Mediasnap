import os
import shutil
import yt_dlp
from pathlib import Path
from django.conf import settings


def _get_ffmpeg_location():
    """Return the path to ffmpeg, or None if not found."""
    if shutil.which('ffmpeg'):
        return shutil.which('ffmpeg')
    
    # Check the local virtual environment path where we installed the static build
    venv_ffmpeg = Path(__file__).resolve().parent.parent.parent / 'myenv' / 'bin' / 'ffmpeg'
    if venv_ffmpeg.exists():
        return str(venv_ffmpeg)
    
    return None

def _ffmpeg_available() -> bool:
    """Return True if ffmpeg is available."""
    return _get_ffmpeg_location() is not None


def detect_platform(url: str) -> str:
    """Detect social media platform from URL."""
    url_lower = url.lower()
    if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
        return 'youtube'
    elif 'instagram.com' in url_lower:
        return 'instagram'
    elif 'facebook.com' in url_lower or 'fb.watch' in url_lower or 'fb.com' in url_lower:
        return 'facebook'
    return 'unknown'


def detect_media_type(url: str, platform: str) -> str:
    """Guess media type from URL."""
    url_lower = url.lower()
    if 'reel' in url_lower:
        return 'reel'
    if any(ext in url_lower for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
        return 'image'
    if platform == 'instagram' and '/p/' in url_lower:
        return 'image'
    return 'video'


def get_download_dir() -> Path:
    """Return and create the download directory."""
    dl_dir = Path(settings.DOWNLOAD_DIR)
    dl_dir.mkdir(parents=True, exist_ok=True)
    return dl_dir


def fetch_media_info(url: str) -> dict:
    """Fetch media info (title, thumbnail, duration, formats) without downloading."""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'cookiefile': None,
    }
    ffmpeg_loc = _get_ffmpeg_location()
    if ffmpeg_loc:
        ydl_opts['ffmpeg_location'] = ffmpeg_loc
        
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if info is None:
                return {'error': 'Could not extract info from URL'}

            # Build available quality list
            formats = info.get('formats', [])
            qualities = []
            seen = set()
            for f in reversed(formats):
                height = f.get('height')
                if height and height not in seen and f.get('vcodec', 'none') != 'none':
                    seen.add(height)
                    qualities.append({
                        'format_id': f.get('format_id'),
                        'label': f'{height}p',
                        'ext': f.get('ext', 'mp4'),
                        'filesize': f.get('filesize') or f.get('filesize_approx') or 0,
                    })

            # Duration formatting
            duration_sec = info.get('duration', 0)
            duration_str = ''
            if duration_sec:
                mins = int(duration_sec // 60)
                secs = int(duration_sec % 60)
                duration_str = f'{mins}:{secs:02d}'

            return {
                'title': info.get('title', 'Unknown Title'),
                'thumbnail': info.get('thumbnail', ''),
                'duration': duration_str,
                'uploader': info.get('uploader', ''),
                'view_count': info.get('view_count', 0),
                'qualities': qualities[:6],  # top 6 quality options
                'platform': detect_platform(url),
            }
    except yt_dlp.utils.DownloadError as e:
        return {'error': str(e)}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}'}


def download_media(url: str, quality: str = 'best', download_id: int = None) -> dict:
    """Download media and return result dict with file path and metadata."""
    dl_dir = get_download_dir()

    # Build output template
    safe_id = str(download_id) if download_id else '%(id)s'
    outtmpl = str(dl_dir / f'{safe_id}_%(title).80s.%(ext)s')

    # ── Format selection ─────────────────────────────────────────────────
    # Automatically use ffmpeg-merged HD formats when ffmpeg is installed on
    # the server; otherwise fall back to pre-merged single-file formats that
    # work without ffmpeg.  Either way visitors get the best quality possible.
    has_ffmpeg = _ffmpeg_available()

    if quality == 'audio':
        if has_ffmpeg:
            format_sel = 'bestaudio/best'
            postprocessors = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        else:
            format_sel = 'bestaudio[ext=m4a]/bestaudio[ext=mp3]/bestaudio/best'
            postprocessors = []

    elif quality == 'best' or not quality:
        if has_ffmpeg:
            # Merge separate video+audio streams → true best quality
            format_sel = (
                'bestvideo[ext=mp4]+bestaudio[ext=m4a]'
                '/bestvideo+bestaudio'
                '/best[ext=mp4]/best'
            )
        else:
            # Pick the single best pre-merged file — no ffmpeg needed
            format_sel = 'best[ext=mp4]/best[ext=webm]/best'
        postprocessors = []

    else:
        # Specific height, e.g. "720"
        try:
            h = int(quality.replace('p', ''))
            if has_ffmpeg:
                format_sel = (
                    f'bestvideo[height<={h}][ext=mp4]+bestaudio[ext=m4a]'
                    f'/bestvideo[height<={h}]+bestaudio'
                    f'/best[height<={h}][ext=mp4]/best[height<={h}]/best'
                )
            else:
                format_sel = (
                    f'best[height<={h}][ext=mp4]'
                    f'/best[height<={h}]'
                    '/best'
                )
        except ValueError:
            format_sel = 'best[ext=mp4]/best'
        postprocessors = []

    ydl_opts = {
        'format': format_sel,
        'outtmpl': outtmpl,
        'quiet': True,
        'no_warnings': True,
        'merge_output_format': 'mp4',
        'postprocessors': postprocessors,
        'http_headers': {
            'User-Agent': (
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/122.0.0.0 Safari/537.36'
            ),
        },
    }
    
    ffmpeg_loc = _get_ffmpeg_location()
    if ffmpeg_loc:
        ydl_opts['ffmpeg_location'] = ffmpeg_loc

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)

        downloaded_file = None
        if info and info.get('requested_downloads'):
            downloaded_file = info['requested_downloads'][0].get('filepath')
        if not downloaded_file and info:
            downloaded_file = info.get('_filename')

        # Fallback: search for file avoiding .part and intermediate .f140 etc
        if not downloaded_file or not os.path.exists(downloaded_file):
            valid_exts = {'.mp4', '.mkv', '.webm', '.m4a', '.mp3', '.jpg', '.webp'}
            candidates = []
            for f in dl_dir.glob(f'{safe_id}_*'):
                if f.suffix in valid_exts and not f.name.endswith('.part'):
                    candidates.append(f)
            if candidates:
                candidates.sort(key=os.path.getmtime, reverse=True)
                downloaded_file = str(candidates[0])

        file_size = 0
        if downloaded_file and os.path.exists(downloaded_file):
            file_size = os.path.getsize(downloaded_file)

        # Relative path for serving via Django
        rel_path = ''
        if downloaded_file:
            try:
                rel_path = os.path.relpath(downloaded_file, settings.MEDIA_ROOT)
            except Exception:
                rel_path = downloaded_file

        duration_sec = info.get('duration', 0) if info else 0
        duration_str = ''
        if duration_sec:
            mins = int(duration_sec // 60)
            secs = int(duration_sec % 60)
            duration_str = f'{mins}:{secs:02d}'

        return {
            'success': True,
            'title': info.get('title', '') if info else '',
            'thumbnail': info.get('thumbnail', '') if info else '',
            'file_path': rel_path,
            'file_size': file_size,
            'duration': duration_str,
            'quality': quality,
        }
    except yt_dlp.utils.DownloadError as e:
        return {'success': False, 'error': str(e)}
    except Exception as e:
        return {'success': False, 'error': f'Unexpected error: {str(e)}'}
