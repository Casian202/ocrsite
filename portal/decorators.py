from __future__ import annotations

from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import reverse

from .models import PortalAccess


def portal_menu_required(menu_key: str | None = None):
    def decorator(view_func):
        @login_required
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            access = getattr(request.user, 'portal_access', None)
            if access is None:
                access, _ = PortalAccess.objects.get_or_create(user=request.user)
            home_url = reverse('portal:home')
            if access is None:
                messages.error(
                    request,
                    'Contul tău nu este încă înregistrat în portal. Trimite o solicitare de acces.',
                )
                return redirect(home_url)
            if access.status != PortalAccess.Status.APPROVED and not request.user.is_staff:
                messages.warning(
                    request,
                    'Solicitarea ta este în așteptare sau a fost revocată. Contactează administratorul.',
                )
                return redirect(home_url)
            if menu_key and menu_key not in access.allowed_menus and not request.user.is_staff:
                messages.error(
                    request,
                    'Nu ai permisiunea de a accesa acest modul. Te rugăm să contactezi administratorul.',
                )
                return redirect(home_url)
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator
