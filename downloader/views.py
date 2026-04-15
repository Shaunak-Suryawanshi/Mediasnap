import os
import json
from pathlib import Path
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, FileResponse, Http404
from django.views.decorators.http import require_POST, require_http_methods
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.contrib import messages
from django.conf import settings
from .models import DownloadHistory
from .utils import detect_platform, detect_media_type, fetch_media_info, download_media


@ensure_csrf_cookie
def home(request):
    """Home page — main downloader interface."""
    if not request.session.session_key:
        request.session.create()
    recent = DownloadHistory.objects.filter(
        session_key=request.session.session_key, 
        status='success'
    ).order_by('-created_at')[:6]
    return render(request, 'downloader/home.html', {'recent_downloads': recent})


@require_POST
def fetch_info(request):
    """AJAX: fetch media info (title, thumbnail, formats) without downloading."""
    try:
        data = json.loads(request.body)
        url = data.get('url', '').strip()
    except (json.JSONDecodeError, AttributeError):
        url = request.POST.get('url', '').strip()

    if not url:
        return JsonResponse({'error': 'Please provide a URL.'}, status=400)

    platform = detect_platform(url)
    if platform == 'unknown':
        # Still try, yt-dlp supports many sites
        pass

    info = fetch_media_info(url)
    if 'error' in info:
        return JsonResponse({'error': info['error']}, status=422)

    info['platform'] = platform
    return JsonResponse(info)


@require_POST
def start_download(request):
    """AJAX: perform the actual download and record in DB."""
    try:
        data = json.loads(request.body)
        url = data.get('url', '').strip()
        quality = data.get('quality', 'best').strip()
    except (json.JSONDecodeError, AttributeError):
        url = request.POST.get('url', '').strip()
        quality = request.POST.get('quality', 'best').strip()

    if not url:
        return JsonResponse({'error': 'Please provide a URL.'}, status=400)

    if not request.session.session_key:
        request.session.create()
    session_key = request.session.session_key

    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip_address = x_forwarded_for.split(',')[0]
    else:
        ip_address = request.META.get('REMOTE_ADDR')

    platform = detect_platform(url)
    media_type = detect_media_type(url, platform)

    # Create a pending history record first
    record = DownloadHistory.objects.create(
        url=url,
        platform=platform,
        media_type=media_type,
        status='pending',
        quality=quality,
        ip_address=ip_address,
        session_key=session_key,
    )

    result = download_media(url, quality=quality, download_id=record.pk)

    if result.get('success'):
        record.status = 'success'
        record.title = result.get('title', '')[:500]
        record.thumbnail = result.get('thumbnail', '')[:2048]
        record.file_path = result.get('file_path', '')
        record.file_size = result.get('file_size', 0)
        record.duration = result.get('duration', '')
        record.quality = quality
        record.save()
        return JsonResponse({
            'success': True,
            'id': str(record.pk),
            'title': record.title,
            'thumbnail': record.thumbnail,
            'duration': record.duration,
            'file_size_mb': record.file_size_mb,
            'download_url': f'/serve/{record.pk}/',
        })
    else:
        record.status = 'failed'
        record.error_message = result.get('error', 'Unknown error')
        record.save()
        return JsonResponse({'error': result.get('error', 'Download failed')}, status=422)


def history(request):
    """Download history page."""
    if not request.session.session_key:
        request.session.create()
    downloads = DownloadHistory.objects.filter(session_key=request.session.session_key).order_by('-created_at')
    return render(request, 'downloader/history.html', {'downloads': downloads})


@require_POST
def clear_history(request):
    """Delete all history records and their files."""
    if request.session.session_key:
        items = DownloadHistory.objects.filter(session_key=request.session.session_key)
        for item in items:
            _delete_file(item)
        items.delete()
    messages.success(request, 'History cleared successfully.')
    return redirect('downloader:history')


@require_http_methods(['POST', 'DELETE'])
def delete_history_item(request, pk):
    """Delete a single history record and its file."""
    if not request.session.session_key:
        raise Http404("Not found")
    item = get_object_or_404(DownloadHistory, pk=pk, session_key=request.session.session_key)
    _delete_file(item)
    item.delete()
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    messages.success(request, 'Download deleted.')
    return redirect('downloader:history')


def serve_file(request, pk):
    """Serve / download a file from the media directory."""
    record = get_object_or_404(DownloadHistory, pk=pk)
    if not record.file_path:
        raise Http404("File not found")

    full_path = Path(settings.MEDIA_ROOT) / record.file_path
    if not full_path.exists():
        raise Http404("File no longer exists on disk")

    filename = full_path.name
    response = FileResponse(open(full_path, 'rb'), as_attachment=True, filename=filename)
    return response


# ─── helpers ────────────────────────────────────────────────────────────────

def _delete_file(item: DownloadHistory):
    """Remove the physical file if it exists."""
    if item.file_path:
        full_path = Path(settings.MEDIA_ROOT) / item.file_path
        if full_path.exists():
            try:
                os.remove(full_path)
            except OSError:
                pass
