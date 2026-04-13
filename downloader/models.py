from django.db import models


class DownloadHistory(models.Model):
    PLATFORM_CHOICES = [
        ('youtube', 'YouTube'),
        ('instagram', 'Instagram'),
        ('facebook', 'Facebook'),
        ('unknown', 'Unknown'),
    ]
    TYPE_CHOICES = [
        ('video', 'Video'),
        ('image', 'Image'),
        ('reel', 'Reel'),
        ('audio', 'Audio'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
    ]

    url = models.URLField(max_length=2048)
    platform = models.CharField(max_length=20, choices=PLATFORM_CHOICES, default='unknown')
    media_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='video')
    title = models.CharField(max_length=500, blank=True)
    thumbnail = models.URLField(max_length=2048, blank=True)
    file_path = models.CharField(max_length=1000, blank=True)
    file_size = models.BigIntegerField(default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    duration = models.CharField(max_length=20, blank=True)
    quality = models.CharField(max_length=20, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.platform} - {self.title or self.url[:50]}"

    @property
    def file_size_mb(self):
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return 0
