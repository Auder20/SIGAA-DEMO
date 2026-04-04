
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page

@login_required
@cache_page(300)
def core_main(request):
	"""
	Vista principal de core. Muestra enlaces a las funcionalidades centrales.
	"""
	return render(request, 'core/main.html')

from django.conf import settings
from afiliados.models import Afiliado
from liquidacion.models import Sueldo, Aporte
from reportes.models import Reporte

@login_required
def home(request):
    """
    Vista principal del sistema SIGAA. Dashboard con acceso a todos los módulos.
    """
    # Calcular estadísticas
    total_afiliados = Afiliado.objects.count()
    total_sueldos = Sueldo.objects.count()
    total_aportes = Aporte.objects.count()
    total_reportes = Reporte.objects.count()

    context = {
        'DEBUG': settings.DEBUG,
        'total_afiliados': total_afiliados,
        'total_sueldos': total_sueldos,
        'total_aportes': total_aportes,
        'total_reportes': total_reportes,
    }
    return render(request, 'home.html', context)
