from django.apps import AppConfig


class PortalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'portal'

    def ready(self) -> None:  # pragma: no cover - side effect registration
        from . import signals  # noqa: F401
