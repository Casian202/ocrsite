from __future__ import annotations

from .constants import MENU_CHOICES
from .models import PortalAccess


def portal_navigation(request):
    access = None
    if request.user.is_authenticated:
        access = getattr(request.user, 'portal_access', None)
        if access is None:
            access, _ = PortalAccess.objects.get_or_create(user=request.user)
        if access and request.user.is_staff and access.status != PortalAccess.Status.APPROVED:
            access.status = PortalAccess.Status.APPROVED
            access.allowed_menus = [key for key, _ in MENU_CHOICES]
            access.save(update_fields=['status', 'allowed_menus', 'updated_at'])
    menu_mapping = dict(MENU_CHOICES)
    available_menus = []
    if access and access.status == PortalAccess.Status.APPROVED:
        available_menus = [
            {
                'key': key,
                'label': menu_mapping.get(key, key.title()),
            }
            for key in access.allowed_menus
        ]
    return {
        'portal_access': access,
        'portal_menu_items': available_menus,
    }
