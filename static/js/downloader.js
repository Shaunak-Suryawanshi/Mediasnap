// downloader.js — home page interaction logic

const urlInput      = document.getElementById('urlInput');
const fetchBtn      = document.getElementById('fetchBtn');
const pasteBtn      = document.getElementById('pasteBtn');
const mediaPreview  = document.getElementById('mediaPreview');
const errorBanner   = document.getElementById('errorBanner');
const errorText     = document.getElementById('errorText');
const successBanner = document.getElementById('successBanner');
const successText   = document.getElementById('successText');
const successDlLink = document.getElementById('successDownloadLink');
const downloadBtn   = document.getElementById('downloadBtn');
const qualityGrid   = document.getElementById('qualityGrid');
const platformIcon  = document.getElementById('platformIcon');

const previewThumb    = document.getElementById('previewThumb');
const previewTitle    = document.getElementById('previewTitle');
const previewMeta     = document.getElementById('previewMeta');
const previewDuration = document.getElementById('previewDuration');
const platformBadge   = document.getElementById('platformBadge');

// CSRF token — read from meta tag set by Django in base.html
function getCsrf() {
  return document.querySelector('meta[name="csrf-token"]')?.content || '';
}

// ─── Platform icon SVGs ──────────────────────────────────────
const PLATFORM_ICONS = {
  youtube: `<svg width="20" height="20" viewBox="0 0 24 24" fill="#ff4444"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>`,
  instagram: `<svg width="20" height="20" viewBox="0 0 24 24" fill="#e1306c"><path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/></svg>`,
  facebook: `<svg width="20" height="20" viewBox="0 0 24 24" fill="#1877f2"><path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/></svg>`,
  link: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>`,
};

// ─── Helpers ─────────────────────────────────────────────────
function showError(msg) {
  errorText.textContent = msg;
  errorBanner.classList.remove('hidden');
  successBanner.classList.add('hidden');
  mediaPreview.classList.add('hidden');
}
function hideError() { errorBanner.classList.add('hidden'); }
function showSuccess(msg, dlUrl) {
  successText.textContent = msg;
  successDlLink.href = dlUrl;
  successBanner.classList.remove('hidden');
  errorBanner.classList.add('hidden');
}
function setFetchLoading(on) {
  fetchBtn.querySelector('.btn-text').classList.toggle('hidden', on);
  fetchBtn.querySelector('.btn-loader').classList.toggle('hidden', !on);
  fetchBtn.disabled = on;
}
function setDownloadLoading(on) {
  downloadBtn.querySelector('.btn-text').classList.toggle('hidden', on);
  downloadBtn.querySelector('.btn-loader').classList.toggle('hidden', !on);
  downloadBtn.disabled = on;
}

function detectPlatform(url) {
  if (!url) return 'link';
  const u = url.toLowerCase();
  if (u.includes('youtube.com') || u.includes('youtu.be')) return 'youtube';
  if (u.includes('instagram.com'))  return 'instagram';
  if (u.includes('facebook.com') || u.includes('fb.watch') || u.includes('fb.com')) return 'facebook';
  return 'link';
}

function updatePlatformIcon(url) {
  const p = detectPlatform(url);
  platformIcon.innerHTML = PLATFORM_ICONS[p] || PLATFORM_ICONS.link;
}

// Live icon swap as user types
urlInput.addEventListener('input', () => {
  updatePlatformIcon(urlInput.value);
  hideError();
  successBanner.classList.add('hidden');
  mediaPreview.classList.add('hidden');
});

// Paste from clipboard
pasteBtn.addEventListener('click', async () => {
  try {
    const text = await navigator.clipboard.readText();
    urlInput.value = text;
    updatePlatformIcon(text);
    urlInput.dispatchEvent(new Event('input'));
  } catch {
    urlInput.focus();
  }
});

// ─── Fetch media info ─────────────────────────────────────────
fetchBtn.addEventListener('click', fetchInfo);
urlInput.addEventListener('keydown', e => { if (e.key === 'Enter') fetchInfo(); });

let currentUrl = '';
let selectedQuality = 'best';

async function fetchInfo() {
  const url = urlInput.value.trim();
  if (!url) { showError('Please paste a URL first.'); return; }
  currentUrl = url;
  hideError();
  successBanner.classList.add('hidden');
  mediaPreview.classList.add('hidden');
  setFetchLoading(true);

  try {
    const res = await fetch('/fetch-info/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
      body: JSON.stringify({ url }),
    });
    const data = await res.json();
    if (!res.ok || data.error) { showError(data.error || 'Failed to fetch media info.'); return; }
    renderPreview(data);
  } catch (err) {
    showError('Request failed: ' + (err.message || err));
  } finally {
    setFetchLoading(false);
  }
}

function renderPreview(data) {
  previewTitle.textContent = data.title || 'Untitled';
  previewMeta.textContent  = [data.uploader, data.view_count ? `${Number(data.view_count).toLocaleString()} views` : ''].filter(Boolean).join(' · ');
  previewDuration.textContent = data.duration || '';

  if (data.thumbnail) {
    previewThumb.src = data.thumbnail;
    previewThumb.style.display = 'block';
  } else {
    previewThumb.style.display = 'none';
  }

  const platform = data.platform || 'unknown';
  platformBadge.textContent = platform.charAt(0).toUpperCase() + platform.slice(1);
  platformBadge.className = `platform-badge platform-badge--${platform}`;

  // Build quality chips
  qualityGrid.innerHTML = '';
  const qualities = [];

  // Add "Best" always
  qualities.push({ label: '🏆 Best', value: 'best' });

  if (data.qualities && data.qualities.length) {
    data.qualities.forEach(q => {
      qualities.push({ label: q.label, value: q.label.replace('p', '') });
    });
  } else {
    // Fallback options
    ['1080', '720', '480', '360'].forEach(h => {
      qualities.push({ label: h + 'p', value: h });
    });
  }

  // Audio option
  qualities.push({ label: '🎵 Audio', value: 'audio' });

  selectedQuality = 'best';

  qualities.forEach((q, i) => {
    const chip = document.createElement('button');
    chip.className = 'quality-chip' + (i === 0 ? ' selected' : '');
    chip.textContent = q.label;
    chip.dataset.value = q.value;
    chip.addEventListener('click', () => {
      document.querySelectorAll('.quality-chip').forEach(c => c.classList.remove('selected'));
      chip.classList.add('selected');
      selectedQuality = q.value;
    });
    qualityGrid.appendChild(chip);
  });

  mediaPreview.classList.remove('hidden');
  // Smooth scroll to preview
  mediaPreview.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// ─── Download ────────────────────────────────────────────────
downloadBtn.addEventListener('click', async () => {
  if (!currentUrl) return;
  setDownloadLoading(true);
  successBanner.classList.add('hidden');
  hideError();

  try {
    const res = await fetch('/download/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCsrf() },
      body: JSON.stringify({ url: currentUrl, quality: selectedQuality }),
    });
    const data = await res.json();

    if (res.ok && data.success) {
      const size = data.file_size_mb ? ` (${data.file_size_mb} MB)` : '';
      showSuccess(`✓ Downloaded: ${data.title || 'File ready'}${size}`, data.download_url);
    } else {
      showError(data.error || 'Download failed. Try a different quality or URL.');
    }
  } catch (err) {
    showError('Request failed: ' + (err.message || err));
  } finally {
    setDownloadLoading(false);
  }
});
