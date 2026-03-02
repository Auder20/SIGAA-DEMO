from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Sueldo


@receiver(post_save, sender=Sueldo)
def sueldo_post_save(sender, instance, created, **kwargs):
    """Al crear/actualizar un Sueldo, recalcular aportes asociados."""
    try:
        instance.recalculate_aportes()
    except Exception:
        # no levantamos para no romper flujos de importación; loggear si se desea
        pass
