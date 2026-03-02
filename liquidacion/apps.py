from django.apps import AppConfig


class LiquidacionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'liquidacion'
    def ready(self):
        # Importar signals para que se registren
        try:
            from . import signals  # noqa: F401
        except Exception:
            pass
