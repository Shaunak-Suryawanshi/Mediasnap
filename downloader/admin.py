from django.contrib import admin
from .models import DownloadHistory

@admin.register(DownloadHistory)
class DownloadHistoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'platform', 'media_type', 'ip_address', 'session_key', 'status', 'created_at')
    list_filter = ('platform', 'media_type', 'status', 'created_at')
    search_fields = ('url', 'title', 'ip_address', 'session_key')
    readonly_fields = ('created_at',)
