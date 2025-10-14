import uuid
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.db import models

from .constants import LANGUAGE_LOOKUP


class OcrJob(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROCESSING = 'processing', 'Processing'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        related_name='ocr_jobs',
    )
    language = models.CharField(max_length=32)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )
    source_file = models.FileField(upload_to='uploads/')
    processed_file = models.FileField(upload_to='processed/', blank=True, null=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.source_file.name} ({self.get_status_display()})"

    def processed_filename(self) -> str:
        if not self.processed_file:
            return ''
        return Path(self.processed_file.name).name

    def ensure_directories(self) -> None:
        """
        Ensure the default storage has placeholders for upload/processed folders when
        using a local filesystem backend. On other storages this is a no-op.
        """
        if not hasattr(default_storage, 'path'):
            return

        for folder in ('uploads', 'processed'):
            storage_path = Path(default_storage.path(folder))
            storage_path.mkdir(parents=True, exist_ok=True)

    def language_labels(self) -> str:
        codes = self.language.split('+') if self.language else []
        return ', '.join(LANGUAGE_LOOKUP.get(code, code).strip() for code in codes)
