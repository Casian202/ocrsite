from __future__ import annotations

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from .constants import MENU_CHOICES
from .models import PortalAccess


@receiver(post_save, sender=get_user_model())
def ensure_portal_access(sender, instance, created, **kwargs):
    if created:
        access, _ = PortalAccess.objects.get_or_create(user=instance)
        if instance.is_staff:
            access.status = PortalAccess.Status.APPROVED
            access.allowed_menus = [key for key, _ in MENU_CHOICES]
            access.save(update_fields=['status', 'allowed_menus', 'updated_at'])
