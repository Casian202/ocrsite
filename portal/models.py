import importlib.util
import logging
import uuid
from functools import lru_cache
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.db import DatabaseError, models

from .constants import FOLDER_COLOR_CHOICES, LANGUAGE_LOOKUP, MENU_CHOICES, OCR_ENGINE_CHOICES


log = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _docling_ready() -> bool:
    """Best-effort probe to determine if Docling can be used."""

    if importlib.util.find_spec('docling') is None:
        return False

    try:  # pragma: no cover - runtime environment probe
        from docling.document_converter import DocumentConverter
    except Exception:  # noqa: BLE001 - import-time issues mean Docling is unusable
        log.debug('Docling import failed.', exc_info=True)
        return False

    try:
        # Instantiate lazily to surface dependency issues (opencv, rapidocr, etc.).
        converter = DocumentConverter()  # type: ignore[call-arg]
    except TypeError:
        # Signature changes shouldn't mark the engine as unavailable.
        return True
    except Exception:  # noqa: BLE001 - we want to swallow any startup issue
        log.debug('Docling is installed but failed to initialize.', exc_info=True)
        return False
    else:
        del converter

    return True


class PortalSettings(models.Model):
    class OcrEngine(models.TextChoices):
        OCRMYPDF = 'ocrmypdf', 'OCRmyPDF'
        DOCLING = 'docling', 'Docling'

    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    ocr_engine = models.CharField(
        max_length=32,
        choices=OCR_ENGINE_CHOICES,
        default=OcrEngine.OCRMYPDF,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Portal settings'

    def __str__(self) -> str:
        return 'Portal settings'

    @classmethod
    def load(cls) -> 'PortalSettings':
        try:
            settings, _ = cls.objects.get_or_create(
                pk=1,
                defaults={'ocr_engine': cls.OcrEngine.OCRMYPDF},
            )
            return settings
        except DatabaseError:
            # The table is not ready yet (e.g., during initial migration).
            return cls(ocr_engine=cls.OcrEngine.OCRMYPDF)

    @staticmethod
    def docling_available() -> bool:
        return _docling_ready()


class PortalAccess(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending Approval'
        APPROVED = 'approved', 'Approved'
        REVOKED = 'revoked', 'Revoked'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(
        get_user_model(), on_delete=models.CASCADE, related_name='portal_access'
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )
    allowed_menus = models.JSONField(default=list, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['user__username']

    def __str__(self) -> str:
        return f"Portal access for {self.user}"

    def has_menu(self, menu_key: str) -> bool:
        if self.status != self.Status.APPROVED:
            return False
        return menu_key in self.allowed_menus

    def grant_defaults(self) -> None:
        if not self.allowed_menus:
            # provide access to home and OCR by default upon approval
            self.allowed_menus = ['home', 'ocr']

    @property
    def menu_labels(self) -> list[str]:
        mapping = dict(MENU_CHOICES)
        return [mapping.get(menu, menu) for menu in self.allowed_menus]


class LibraryFolder(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name='library_folders'
    )
    name = models.CharField(max_length=120)
    color = models.CharField(max_length=24, choices=FOLDER_COLOR_CHOICES, default='mint')
    parent = models.ForeignKey(
        'self', blank=True, null=True, on_delete=models.CASCADE, related_name='children'
    )
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        unique_together = ('user', 'name', 'parent')

    def __str__(self) -> str:
        return self.name

    def color_token(self) -> str:
        return self.color or 'mint'


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
    language = models.CharField(max_length=64, blank=True)
    detected_languages = models.CharField(max_length=128, blank=True)
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )
    source_file = models.FileField(upload_to='uploads/')
    processed_file = models.FileField(upload_to='processed/', blank=True, null=True)
    sidecar_file = models.FileField(upload_to='sidecars/', blank=True, null=True)
    destination_folder = models.ForeignKey(
        LibraryFolder,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='ocr_jobs',
    )
    options = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{Path(self.source_file.name).name} ({self.get_status_display()})"

    def processed_filename(self) -> str:
        if not self.processed_file:
            return ''
        return Path(self.processed_file.name).name

    def sidecar_filename(self) -> str:
        if not self.sidecar_file:
            return ''
        return Path(self.sidecar_file.name).name

    def ensure_directories(self) -> None:
        """
        Ensure the default storage has placeholders for upload/processed folders when
        using a local filesystem backend. On other storages this is a no-op.
        """
        if not hasattr(default_storage, 'path'):
            return

        for folder in ('uploads', 'processed', 'libraries', 'sidecars'):
            storage_path = Path(default_storage.path(folder))
            storage_path.mkdir(parents=True, exist_ok=True)

    def language_labels(self) -> str:
        if self.options.get('auto_language'):
            if self.detected_languages:
                return self.detected_languages
            return 'Detectare automată'
        codes = self.language.split('+') if self.language else []
        return ', '.join(LANGUAGE_LOOKUP.get(code, code).strip() for code in codes)


class StoredDocument(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    folder = models.ForeignKey(
        LibraryFolder, on_delete=models.CASCADE, related_name='documents'
    )
    ocr_job = models.ForeignKey(
        OcrJob, on_delete=models.SET_NULL, blank=True, null=True, related_name='documents'
    )
    title = models.CharField(max_length=150)
    description = models.CharField(max_length=255, blank=True)
    original_file = models.FileField(upload_to='libraries/originals/')
    processed_file = models.FileField(upload_to='libraries/processed/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']

    def __str__(self) -> str:
        return self.title

    def original_filename(self) -> str:
        return Path(self.original_file.name).name

    def processed_filename(self) -> str:
        if not self.processed_file:
            return ''
        return Path(self.processed_file.name).name


class WordDocument(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name='word_documents'
    )
    title = models.CharField(max_length=150)
    source_pdf = models.FileField(upload_to='word/source/', blank=True, null=True)
    document_file = models.FileField(upload_to='word/documents/')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return self.title
