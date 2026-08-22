import os
import uuid
from datetime import timedelta
from django.db import models
from django.utils import timezone
from django.conf import settings

class ResultSession(models.Model):
    """
    Represents an ephemeral result analysis session.
    All data is temporary and automatically purged upon TTL expiration.
    """
    STATUS_CHOICES = [
        ('PENDING', 'Pending Processing'),
        ('PROCESSING', 'Processing Document'),
        ('PENDING_VERIFICATION', 'Pending Human Verification'),
        ('VERIFIED', 'Verified by User'),
        ('COMPLETED', 'Analysis Completed'),
        ('FAILED', 'Processing Failed'),
        ('EXPIRED', 'Session Expired'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    original_filename = models.CharField(max_length=255)
    file_path = models.CharField(max_length=512, blank=True)
    file_type = models.CharField(max_length=50)
    file_size_bytes = models.BigIntegerField(default=0)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    error_message = models.TextField(blank=True, default="")
    
    # JSON payloads storing parsed results and calculated statistics
    meta_info = models.JSONField(default=dict, blank=True)
    parsed_dataset = models.JSONField(default=dict, blank=True)
    analytics_data = models.JSONField(default=dict, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['status']),
        ]

    def save(self, *args, **kwargs):
        if not self.expires_at:
            ttl_minutes = getattr(settings, 'SESSION_TTL_MINUTES', 60)
            self.expires_at = timezone.now() + timedelta(minutes=ttl_minutes)
        super().save(*args, **kwargs)

    @property
    def is_expired(self) -> bool:
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at

    def purge_file(self):
        """Safely removes the underlying uploaded file and session directory from ephemeral disk storage."""
        if self.file_path and os.path.exists(self.file_path):
            try:
                parent_dir = os.path.dirname(self.file_path)
                os.remove(self.file_path)
                if os.path.exists(parent_dir) and not os.listdir(parent_dir):
                    os.rmdir(parent_dir)
            except OSError:
                pass
        self.file_path = ""
        self.save(update_fields=['file_path'])

    def __str__(self):
        return f"ResultSession({self.id}) - {self.original_filename} [{self.status}]"
