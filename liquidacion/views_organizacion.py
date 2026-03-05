from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from liquidacion.models import SueldoOrganizacion, AporteOrganizacion, BonificacionPagoOrganizacion
from afiliados.models import DatosOrganizacion
from liquidacion.services.calculo_sueldo_organizacion import CalculadorSueldoOrganizacion
import logging

logger = logging.getLogger(__name__)


def sueldo_organizacion_list(request):
    """
    Lista de sueldos de Organización Externa con búsqueda y filtros.
    """
    search_query = request.GET.get('search', '').strip()
    anio = request.GET.get('anio', '')
    mes = request.GET.get('mes', '')

    sueldos = SueldoOrganizacion.objects.select_related('afiliado_organizacion').all().order_by('-anio', 'afiliado_organizacion__nombre_completo')

    if search_query:
        sueldos = sueldos.filter(
            Q(afiliado_organizacion__cedula__icontains=search_query) |
            Q(afiliado_organizacion__nombre_completo__icontains=search_query)
        )

    if anio:
        sueldos = sueldos.filter(anio=anio)

    paginator = Paginator(sueldos, 20)
    page = request.GET.get('page')

    try:
        sueldos_page = paginator.page(page)
    except PageNotAnInteger:
        sueldos_page = paginator.page(1)
    except EmptyPage:
        sueldos_page = paginator.page(paginator.num_pages)

    # Obtener años disponibles para filtro
    anios_disponibles = SueldoOrganizacion.objects.values_list('anio', flat=True).distinct().order_by('-anio')

    return render(request, 'liquidacion/organizacion/sueldo_list.html', {
        'sueldos': sueldos_page,
        'search_query': search_query,
        'anio_actual': anio,
        'mes_actual': mes,
        'anios': anios_disponibles
    })


def sueldo_organizacion_detail(request, pk):
    """
    Detalle de un sueldo de Organización Externa con sus bonificaciones y aportes.
    """
    sueldo = get_object_or_404(SueldoOrganizacion, pk=pk)
    bonificaciones = BonificacionPagoOrganizacion.objects.filter(sueldo_organizacion=sueldo)
    aportes = AporteOrganizacion.objects.filter(sueldo_organizacion=sueldo)

    return render(request, 'liquidacion/organizacion/sueldo_detail.html', {
        'sueldo': sueldo,
        'bonificaciones': bonificaciones,
        'aportes': aportes
    })


def sueldo_organizacion_recalcular(request, pk):
    """
    Recalcula un sueldo específico de Organización Externa.
    """
    sueldo = get_object_or_404(SueldoOrganizacion, pk=pk)

    try:
        calculador = CalculadorSueldoOrganizacion(sueldo.afiliado_organizacion, sueldo.anio)
        calculador.crear_o_actualizar_sueldo()
        messages.success(request, f'Sueldo de {sueldo.afiliado_organizacion.nombre_completo} recalculado exitosamente.')
    except Exception as e:
        messages.error(request, f'Error al recalcular sueldo: {str(e)}')

    return redirect('liquidacion:sueldo_organizacion_detail', pk=pk)


def aporte_organizacion_list(request):
    """
    Lista de aportes de Organización Externa.
    """
    search_query = request.GET.get('search', '').strip()

    aportes = AporteOrganizacion.objects.select_related('sueldo_organizacion', 'sueldo_organizacion__afiliado_organizacion').all().order_by('-sueldo_organizacion__anio')

    if search_query:
        aportes = aportes.filter(
            Q(nombre__icontains=search_query) |
            Q(sueldo_organizacion__afiliado_organizacion__nombre_completo__icontains=search_query)
        )

    paginator = Paginator(aportes, 20)
    page = request.GET.get('page')
    aportes_page = paginator.get_page(page)

    return render(request, 'liquidacion/organizacion/aporte_list.html', {
        'aportes': aportes_page,
        'search_query': search_query
    })


def calcular_sueldos_organizacion_masivo(request):
    """
    Vista para calcular sueldos de todos los afiliados de Organización Externa masivamente.
    """
    from liquidacion.services.calculo_sueldo_organizacion import recalcular_sueldos_ademacor_masivo
    from datetime import date

    if request.method == 'POST':
        anio = request.POST.get('anio', date.today().year)
        grado = request.POST.get('grado', '')

        filtros = {}
        if grado:
            filtros['grado_escalafon'] = grado

        try:
            anio = int(anio)
            resultados = recalcular_sueldos_ademacor_masivo(anio, filtros if filtros else None)

            messages.success(
                request,
                f'Cálculo masivo completado: {resultados["procesados"]} procesados, '
                f'{resultados["creados"]} creados, {resultados["actualizados"]} actualizados, '
                f'{len(resultados["errores"])} errores.'
            )

            if resultados['errores']:
                for error in resultados['errores'][:5]:
                    messages.warning(request, f"Error en {error['cedula']}: {error['error']}")
                if len(resultados['errores']) > 5:
                    messages.warning(request, f"... y {len(resultados['errores']) - 5} errores más.")

        except Exception as e:
            messages.error(request, f'Error al calcular sueldos: {str(e)}')

        return redirect('liquidacion:sueldo_organizacion_list')

    # GET: Mostrar formulario
    from afiliados.models import DatosOrganizacion
    from datetime import date

    # Obtener años disponibles
    anios_disponibles = range(2020, date.today().year + 2)

    # Obtener grados disponibles
    grados_disponibles = DatosOrganizacion.objects.filter(activo=True).values_list('grado_escalafon', flat=True).distinct().order_by('grado_escalafon')

    # Contar afiliados activos
    total_afiliados = DatosOrganizacion.objects.filter(activo=True).count()

    return render(request, 'liquidacion/organizacion/calcular_sueldos_masivo.html', {
        'anios': anios_disponibles,
        'grados': grados_disponibles,
        'total_afiliados': total_afiliados
    })


def importar_aportes_organizacion(request):
    """
    Vista para importar aportes de Organización Externa desde un archivo Excel usando servicio optimizado.
    """
    import os
    import tempfile
    from liquidacion.services.aportes_ademacor_import import importar_aporte_ademacor

    if request.method == 'POST' and request.FILES.get('archivo'):
        archivo = request.FILES['archivo']
        anio = request.POST.get('anio')
        tipo_aporte = request.POST.get('tipo_aporte', None)  # Opcional: ORGANIZACIÓN, FONDO o auto-detectar

        try:
            # Guardar archivo temporalmente
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(archivo.name)[1]) as tmp_file:
                for chunk in archivo.chunks():
                    tmp_file.write(chunk)
                tmp_file_path = tmp_file.name

            # Procesar archivo con servicio optimizado
            resultado = importar_aporte_ademacor(
                tmp_file_path,
                int(anio) if anio else None,
                tipo_aporte,
                batch_size=1000
            )

            # Limpiar archivo temporal
            try:
                os.unlink(tmp_file_path)
            except Exception as e:
                logger.error(f"Error al eliminar archivo temporal: {str(e)}")

            # Procesar resultado
            if resultado.get('estado') == 'completado':
                stats = resultado.get('estadisticas', {})
                messages.success(
                    request,
                    f'✅ Importación completada: {stats.get("registros_procesados", 0)} aportes procesados '
                    f'({stats.get("aportes_creados", 0)} creados, {stats.get("aportes_actualizados", 0)} actualizados). '
                    f'Tipo: {stats.get("tipo_aporte", "N/A")}. '
                    f'Tiempo: {stats.get("tiempo_total", 0):.2f}s'
                )

                # Mostrar advertencias si hay registros omitidos
                if stats.get('registros_omitidos', 0) > 0:
                    messages.warning(
                        request,
                        f'⚠ {stats.get("registros_omitidos")} registros omitidos '
                        f'({stats.get("afiliados_no_encontrados", 0)} afiliados no encontrados)'
                    )

                # Mostrar si se crearon sueldos
                if stats.get('sueldos_creados', 0) > 0:
                    messages.info(
                        request,
                        f'ℹ Se crearon {stats.get("sueldos_creados")} sueldos automáticamente (con valor $0)'
                    )

                # Mostrar errores si los hay
                errores = resultado.get('errores')
                if errores:
                    for error in errores[:5]:
                        messages.error(request, f'❌ {error}')
                    if len(errores) > 5:
                        messages.warning(request, f'... y {len(errores) - 5} errores más')

            else:
                # Error en el procesamiento
                mensaje_error = resultado.get('mensaje', 'Error desconocido')
                messages.error(request, f'❌ Error al procesar archivo: {mensaje_error}')

                # Mostrar estadísticas parciales si existen
                stats = resultado.get('estadisticas', {})
                if stats.get('registros_procesados', 0) > 0:
                    messages.info(
                        request,
                        f'Se procesaron {stats.get("registros_procesados")} registros antes del error'
                    )

        except Exception as e:
            messages.error(request, f'❌ Error al importar aportes: {str(e)}')
            logger.exception("Error en importación de aportes de Organización Externa")

        return redirect('liquidacion:aporte_organizacion_list')

    # GET: Mostrar formulario
    from datetime import date
    return render(request, 'liquidacion/organizacion/importar_aportes.html', {
        'anio_actual': date.today().year
    })
