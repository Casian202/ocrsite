from django.contrib import admin

from .models import OcrJob, PortalSettings


@admin.register(OcrJob)
class OcrJobAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'language', 'status', 'created_at', 'updated_at')
    list_filter = ('status', 'language', 'created_at')
    search_fields = ('user__username', 'source_file', 'processed_file')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(PortalSettings)
class PortalSettingsAdmin(admin.ModelAdmin):
    list_display = ('ocr_engine', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
