from django.apps import AppConfig


class CatalogConfig(AppConfig):
    name = 'catalog'

    def ready(self):
        from . import signals  # noqa: F401 — import registers the @receiver hooks
