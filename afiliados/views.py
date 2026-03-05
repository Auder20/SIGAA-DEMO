"""
Vistas para la gestión de afiliados en el sistema SIGAA.

Este módulo contiene todas las vistas relacionadas con la gestión de afiliados,
incluyendo operaciones CRUD, importación desde Excel y visualización de datos.

Autor: Sistema SIGAA
Fecha: 2025
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.urls import reverse
import os
import tempfile
from .models import Afiliado, DatosOrganizacion
from .services.excel_import import importar_afiliados_desde_excel, importar_organizacion_desde_excel
from .services.excel_import.aportes_import import importar_aportes_desde_excel
from afiliados.services.export import DynamicExportService
import logging
from django.views.decorators.cache import cache_page
from django.contrib.auth.decorators import login_required
from datetime import datetime

# Configurar logger para esta vista
logger = logging.getLogger(__name__)


@cache_page(300)
def afiliados_main(request):
    """
    Vista principal del módulo de afiliados.

    Muestra la página principal con enlaces a las diferentes funcionalidades
    disponibles para la gestión de afiliados como listado, creación e importación.

    Args:
        request: HttpRequest object

    Returns:
        HttpResponse: Página principal de afiliados
    """
    from liquidacion.models import Sueldo

    # Calcular estadísticas
    total_afiliados = Afiliado.objects.count()
    afiliados_activos = Afiliado.objects.filter(activo=True).count()
    afiliados_inactivos = Afiliado.objects.filter(activo=False).count()

    # Contar afiliados con sueldo calculado
    afiliados_con_sueldo = Afiliado.objects.filter(
        cedula__in=Sueldo.objects.values_list('afiliado__cedula', flat=True)
    ).distinct().count()

    # Obtener afiliados recientes (últimos 5)
    afiliados_recientes = Afiliado.objects.order_by('-id')[:5]

    context = {
        'total_afiliados': total_afiliados,
        'afiliados_activos': afiliados_activos,
        'afiliados_inactivos': afiliados_inactivos,
        'con_sueldo': afiliados_con_sueldo,
        'afiliados_recientes': afiliados_recientes,
    }

    return render(request, 'afiliados/main.html', context)


def importar_aportes_excel_view(request):
    """
    Vista para importar datos de aportes desde múltiples archivos Excel.
    """
    if request.method == 'POST' and request.FILES.getlist('archivo_excel'):
        archivos = request.FILES.getlist('archivo_excel')
        anio = request.POST.get('anio')

        # Variables para acumular resultados
        total_procesados = 0
        total_errores = 0
        mensajes_error = []
        archivos_procesados = 0

        for archivo in archivos:
            try:
                # Guardar el archivo temporalmente
                with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                    for chunk in archivo.chunks():
                        tmp_file.write(chunk)
                    tmp_file_path = tmp_file.name

                # Procesar el archivo
                resultado = importar_aportes_desde_excel(tmp_file_path, int(anio) if anio else None)

                # Limpiar archivo temporal
                try:
                    os.unlink(tmp_file_path)
                except Exception as e:
                    logger.error(f"Error al eliminar archivo temporal: {str(e)}")

                # Acumular resultados
                if resultado.get('estado') == 'completado':
                    total_procesados += resultado.get('total_registros', 0)
                    archivos_procesados += 1
                    logger.info(f"Archivo {archivo.name} procesado: {resultado.get('total_registros', 0)} registros")
                else:
                    total_errores += 1
                    mensajes_error.append(f"Error en {archivo.name}: {resultado.get('mensaje', 'Error desconocido')}")

            except Exception as e:
                total_errores += 1
                logger.error(f"Error al importar archivo {archivo.name}: {str(e)}", exc_info=True)
                mensajes_error.append(f"Error en {archivo.name}: {str(e)}")

        # Generar mensaje de resultado
        if archivos_procesados > 0 and total_errores == 0:
            messages.success(
                request,
                f'Se importaron exitosamente {total_procesados} registros de {archivos_procesados} archivos.'
            )
        elif archivos_procesados > 0 and total_errores > 0:
            messages.warning(
                request,
                f'Se importaron {total_procesados} registros de {archivos_procesados} archivos, '
                f'pero {total_errores} archivos tuvieron errores.'
            )
            for error in mensajes_error:
                messages.error(request, error)
        else:
            messages.error(request, f'No se pudo procesar ninguno de los {len(archivos)} archivos.')
            for error in mensajes_error:
                messages.error(request, error)

        return redirect('afiliados:importar_excel')

    return render(request, 'afiliados/importar_aportes.html', {
        'anio_actual': datetime.now().year
    })


def importar_excel_view(request):
    """
    Vista para importar datos desde un archivo Excel.

    Maneja diferentes tipos de importación:
    - afiliados: Información completa de afiliados
    - sistema_externo: Datos básicos de sistema externo (antes secretaría)
    - organizacion: Datos básicos de organización externa (antes ADEMACOR)

    Soporta tanto solicitudes AJAX como formularios regulares.

    Args:
        request: HttpRequest object con posible archivo Excel en FILES

    Returns:
        JsonResponse o HttpResponse: Dependiendo si es AJAX o no
    """
    if request.method == 'POST' and request.FILES.get('archivo_excel'):
        archivo = request.FILES['archivo_excel']
        import_type = request.POST.get('import_type', 'afiliados')
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        # Verificar que el archivo tenga una extensión permitida
        if not archivo.name.endswith(('.xlsx', '.xls')):
            error_msg = 'Formato de archivo no soportado. Por favor, suba un archivo Excel (.xlsx o .xls)'
            if is_ajax:
                return JsonResponse({'success': False, 'error': error_msg}, status=400)
            messages.error(request, error_msg)
            return redirect('afiliados:importar_excel')

        try:
            # Procesar según el tipo de importación
            if import_type == 'sistema_externo':
                summary = importar_sistema_externo_desde_excel(archivo)
                model_name = 'Datos de Sistema Externo'
            elif import_type == 'organizacion':
                summary = importar_organizacion_desde_excel(archivo)
                model_name = 'Datos de Organización Externa'
            else:  # afiliados por defecto
                summary = importar_afiliados_desde_excel(archivo)
                model_name = 'Afiliados'

            # Mostrar retroalimentación al usuario
            rows = summary.get('rows_processed', 0)
            created = summary.get('created', 0)
            updated = summary.get('updated', 0)
            ignored = summary.get('ignored', 0)
            missing = summary.get('missing_columns', [])
            errors = summary.get('errors', [])

            success_msg = f'Importación de {model_name} finalizada. Procesados: {rows}, Creados: {created}, Actualizados: {updated}, Ignorados: {ignored}.'

            if is_ajax:
                response_data = {
                    'success': True,
                    'message': success_msg,
                    'redirect_url': reverse('afiliados:afiliado_list'),
                    'stats': {
                        'processed': rows,
                        'created': created,
                        'updated': updated,
                        'ignored': ignored
                    }
                }

                if missing:
                    response_data['warning'] = f'Columnas críticas faltantes: {", ".join(missing)}'

                if errors:
                    response_data['errors'] = [f"Fila {err.get('row')}: {err.get('error')}" for err in errors[:5]]
                    if len(errors) > 5:
                        response_data['warning'] = f"{response_data.get('warning', '')} Se omitieron {len(errors)-5} errores adicionales."

                return JsonResponse(response_data)

            # Para solicitudes regulares
            messages.success(request, success_msg)
            if missing:
                messages.warning(request, f'Columnas críticas faltantes: {", ".join(missing)}')
            if errors:
                for err in errors[:5]:
                    messages.error(request, f"Fila {err.get('row')}: {err.get('error')}")
                if len(errors) > 5:
                    messages.warning(request, f"Se omitieron {len(errors)-5} errores adicionales. Revisa logs.")

        except Exception as e:
            error_msg = f'Error al importar {import_type}: {str(e)}'
            logger.exception(f"Error al procesar el archivo Excel para {import_type}")

            if is_ajax:
                return JsonResponse({'success': False, 'error': error_msg}, status=500)

            messages.error(request, error_msg)
            return redirect('afiliados:importar_excel')

        return redirect('afiliados:afiliado_list')

    # GET request o sin archivo
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'error': 'No se proporcionó ningún archivo'}, status=400)

    return render(request, 'afiliados/importar_excel.html')


def importar_sistema_externo_desde_excel(excel_file):
    """
    Importa datos de sistema externo desde archivo Excel usando importador ORIGINAL.

    Usa el importador complejo que funcionaba correctamente.

    Args:
        excel_file: Archivo Excel a procesar

    Returns:
        dict: Resumen de la importación con estadísticas
    """
    from .services.excel_import.secretaria_complex_import import importar_secretaria_desde_excel as sistema_externo_importer
    return sistema_externo_importer(excel_file)


def importar_organizacion_desde_excel(excel_file):
    """
    Importa datos de organización externa desde archivo Excel usando importador ORIGINAL.

    Usa el importador complejo que funcionaba correctamente.

    Args:
        excel_file: Archivo Excel a procesar

    Returns:
        dict: Resumen de la importación con estadísticas
    """
    from .services.excel_import.ademacor_complex_import import importar_organizacion_desde_excel as organizacion_importer
    return organizacion_importer(excel_file)


from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def afiliado_list(request):
    """
    Lista y búsqueda de afiliados con paginación, optimizada para lectura.

    - Limita columnas con .only() para reducir I/O y memoria.
    - Evita conteos adicionales usando paginator.count.
    - No usa caché para asegurar datos actualizados.
    """
    search_query = request.GET.get('search', '').strip()

    # Guardar término para exportaciones
    request.session['search_query'] = search_query

    # Query base: solo campos usados en el listado
    qs = Afiliado.objects.only('id', 'cedula', 'nombre_completo', 'email', 'municipio', 'activo')

    if search_query:
        qs = qs.filter(
            Q(cedula__icontains=search_query) |
            Q(nombre_completo__icontains=search_query) |
            Q(municipio__icontains=search_query)
        )

    qs = qs.order_by('nombre_completo')

    # Paginación
    paginator = Paginator(qs, 20)
    page = request.GET.get('page', 1)
    try:
        afiliados_page = paginator.page(page)
    except PageNotAnInteger:
        afiliados_page = paginator.page(1)
    except EmptyPage:
        afiliados_page = paginator.page(paginator.num_pages)

    context = {
        'afiliados': afiliados_page,
        'search_query': search_query,
        'total_afiliados': paginator.count,
        'is_paginated': paginator.num_pages > 1,
        'page_obj': afiliados_page,
    }
    return render(request, 'afiliados/afiliado_list.html', context)


def exportar_afiliados_excel(request):
    """
    Vista para exportar afiliados a Excel con servicio completamente dinámico.

    Solo exporta las columnas que realmente están disponibles en la tabla,
    permitiendo máxima flexibilidad según los datos disponibles.

    Args:
        request: HttpRequest object

    Returns:
        HttpResponse: Archivo Excel para descarga
    """
    try:
        # Obtener parámetros de la solicitud
        include_inactive = request.GET.get('include_inactive', 'false').lower() == 'true'

        # Obtener término de búsqueda de la sesión (mantenido del listado)
        search_query = request.session.get('search_query', '')

        # Crear servicio de exportación dinámico
        # Preparar datos exactamente como queremos exportarlos
        data = preparar_datos_afiliados_exportacion(include_inactive, search_query)

        if not data:
            messages.warning(request, 'No hay afiliados para exportar.')
            return redirect('afiliados:afiliado_list')

        # Crear servicio dinámico con los datos preparados
        export_service = DynamicExportService(data, "Afiliados")

        # Obtener estadísticas
        stats = export_service.get_export_stats()

        # Generar nombre del archivo con fecha y hora
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"afiliados_export_{timestamp}"

        # Exportar a Excel
        response = export_service.export_excel(filename)

        # Log de la exportación
        logger.info(f"Exportación Excel realizada: {stats['total_registros']} registros, "
                   f"Columnas: {stats['columnas_exportadas']}")

        # Mensaje de éxito
        messages.success(
            request,
            f'Exportación Excel generada exitosamente: {stats["total_registros"]} registros, '
            f'{stats["columnas_exportadas"]} columnas exportadas.'
        )

        return response

    except Exception as e:
        logger.exception("Error al exportar afiliados a Excel")
        messages.error(request, f'Error al generar la exportación: {str(e)}')
        return redirect('afiliados:afiliado_list')


def exportar_afiliados_pdf(request):
    """
    Vista para exportar afiliados a PDF con formato profesional.

    Genera un documento PDF con información estadística del municipio,
    cantidad de datos y tabla organizada profesionalmente.

    Args:
        request: HttpRequest object

    Returns:
        HttpResponse: Archivo PDF para descarga
    """
    try:
        # Obtener parámetros de la solicitud
        include_inactive = request.GET.get('include_inactive', 'false').lower() == 'true'

        # Obtener término de búsqueda de la sesión (mantenido del listado)
        search_query = request.session.get('search_query', '')

        # Preparar datos para PDF con información adicional
        data = preparar_datos_afiliados_pdf(include_inactive, search_query)

        if not data:
            messages.warning(request, 'No hay afiliados para exportar.')
            return redirect('afiliados:afiliado_list')

        # Crear servicio dinámico con los datos preparados
        from afiliados.services.export import DynamicExportService
        export_service = DynamicExportService(data, "Afiliados - SIGAA")

        # Obtener estadísticas
        stats = export_service.get_export_stats()

        # Generar nombre del archivo con fecha y hora
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"afiliados_report_{timestamp}"

        # Exportar a PDF con información adicional
        response = export_service.export_pdf(filename)

        # Log de la exportación
        logger.info(f"Exportación PDF realizada: {stats['total_registros']} registros, "
                   f"Columnas: {stats['columnas_exportadas']}")

        # Mensaje de éxito
        messages.success(
            request,
            f'Exportación PDF generada exitosamente: {stats["total_registros"]} registros, '
            f'{stats["columnas_exportadas"]} columnas exportadas.'
        )

        return response

    except Exception as e:
        logger.exception("Error al exportar afiliados a PDF")
        messages.error(request, f'Error al generar la exportación: {str(e)}')
        return redirect('afiliados:afiliado_list')


def preparar_datos_afiliados_pdf(include_inactive: bool = True, search_query: str = None) -> list:
    """
    Prepara los datos de afiliados para exportación PDF con información adicional.

    Incluye estadísticas por municipio y datos formateados para presentación profesional.

    Args:
        include_inactive: Si incluir afiliados inactivos
        search_query: Término de búsqueda para filtrar afiliados

    Returns:
        Lista de diccionarios con datos formateados para PDF
    """
    # Obtener afiliados según filtro
    if include_inactive:
        afiliados = Afiliado.objects.all()
    else:
        afiliados = Afiliado.objects.filter(activo=True)

    # Aplicar filtros de búsqueda si se proporcionaron
    if search_query:
        afiliados = afiliados.filter(
            Q(cedula__icontains=search_query) |
            Q(nombre_completo__icontains=search_query) |
            Q(municipio__icontains=search_query)
        )

    data = []

    for afiliado in afiliados.select_related():
        afiliado_data = {}

        # Información básica
        if afiliado.cedula:
            afiliado_data['cedula'] = afiliado.cedula
        if afiliado.nombre_completo:
            afiliado_data['nombre_completo'] = afiliado.nombre_completo
        if afiliado.email:
            afiliado_data['email'] = afiliado.email
        if afiliado.telefono:
            afiliado_data['telefono'] = afiliado.telefono
        if afiliado.municipio:
            afiliado_data['municipio'] = afiliado.municipio

        # Estado
        afiliado_data['estado'] = 'Activo' if afiliado.activo else 'Inactivo'

        # Fechas
        if afiliado.fecha_nacimiento:
            afiliado_data['fecha_nacimiento'] = afiliado.fecha_nacimiento.strftime('%d/%m/%Y')
        if afiliado.fecha_ingreso:
            afiliado_data['fecha_ingreso'] = afiliado.fecha_ingreso.strftime('%d/%m/%Y')

        # Información profesional
        if afiliado.cargo_desempenado:
            afiliado_data['cargo_desempenado'] = afiliado.cargo_desempenado
        if afiliado.grado_escalafon:
            afiliado_data['grado_escalafon'] = afiliado.grado_escalafon
        if afiliado.anos_servicio:
            afiliado_data['anos_servicio'] = f"{afiliado.anos_servicio} años"

        # Información académica
        if afiliado.titulo_pregrado:
            afiliado_data['titulo_pregrado'] = afiliado.titulo_pregrado
        if afiliado.titulo_posgrado:
            afiliado_data['titulo_posgrado'] = afiliado.titulo_posgrado
        if afiliado.estudios_posgrado:
            afiliado_data['estudios_posgrado'] = afiliado.estudios_posgrado
        if afiliado.otros_titulos:
            afiliado_data['otros_titulos'] = afiliado.otros_titulos

        # Información personal
        if afiliado.ciudad_de_nacimiento:
            afiliado_data['ciudad_de_nacimiento'] = afiliado.ciudad_de_nacimiento
        if afiliado.estado_civil:
            afiliado_data['estado_civil'] = afiliado.estado_civil
        if afiliado.nombre_conyuge:
            afiliado_data['nombre_conyuge'] = afiliado.nombre_conyuge
        if afiliado.nombre_hijos:
            afiliado_data['nombre_hijos'] = afiliado.nombre_hijos
        if afiliado.direccion:
            afiliado_data['direccion'] = afiliado.direccion

        # Solo agregar si tiene al menos algún dato
        if afiliado_data:
            data.append(afiliado_data)

    return data


def preparar_datos_afiliados_exportacion(include_inactive: bool = True, search_query: str = None) -> list:
    """
    Prepara los datos de afiliados para exportación de forma completamente dinámica.

    Solo incluye las columnas que realmente están disponibles y tienen datos.

    Args:
        include_inactive: Si incluir afiliados inactivos
        search_query: Término de búsqueda para filtrar afiliados

    Returns:
        Lista de diccionarios con datos formateados para exportación
    """
    # Obtener afiliados según filtro
    if include_inactive:
        afiliados = Afiliado.objects.all()
    else:
        afiliados = Afiliado.objects.filter(activo=True)

    # Aplicar filtros de búsqueda si se proporcionaron
    if search_query:
        afiliados = afiliados.filter(
            Q(cedula__icontains=search_query) |
            Q(nombre_completo__icontains=search_query) |
            Q(municipio__icontains=search_query)
        )

    data = []

    for afiliado in afiliados.select_related():
        afiliado_data = {}

        # Campos básicos siempre disponibles
        if afiliado.cedula:
            afiliado_data['cedula'] = afiliado.cedula
        if afiliado.nombre_completo:
            afiliado_data['nombre_completo'] = afiliado.nombre_completo
        if afiliado.email:
            afiliado_data['email'] = afiliado.email
        if afiliado.telefono:
            afiliado_data['telefono'] = afiliado.telefono
        if afiliado.municipio:
            afiliado_data['municipio'] = afiliado.municipio

        # Estado siempre disponible
        afiliado_data['estado'] = 'Activo' if afiliado.activo else 'Inactivo'

        # Campos de fechas si están disponibles
        if afiliado.fecha_nacimiento:
            afiliado_data['fecha_nacimiento'] = afiliado.fecha_nacimiento.strftime('%Y-%m-%d')
        if afiliado.fecha_ingreso:
            afiliado_data['fecha_ingreso'] = afiliado.fecha_ingreso.strftime('%Y-%m-%d')

        # Información personal si está disponible (simplificada para evitar errores)
        # Nota: Los métodos get_sexo_display() y get_nivel_educativo_display()
        # pueden no estar disponibles en todos los casos

        # Información profesional si está disponible
        if afiliado.cargo_desempenado:
            afiliado_data['cargo_desempenado'] = afiliado.cargo_desempenado
        if afiliado.grado_escalafon:
            afiliado_data['grado_escalafon'] = afiliado.grado_escalafon
        if afiliado.anos_servicio:
            afiliado_data['anos_servicio'] = afiliado.anos_servicio

        # Información académica si está disponible
        if afiliado.titulo_pregrado:
            afiliado_data['titulo_pregrado'] = afiliado.titulo_pregrado
        if afiliado.titulo_posgrado:
            afiliado_data['titulo_posgrado'] = afiliado.titulo_posgrado
        if afiliado.estudios_posgrado:
            afiliado_data['estudios_posgrado'] = afiliado.estudios_posgrado
        if afiliado.otros_titulos:
            afiliado_data['otros_titulos'] = afiliado.otros_titulos

        # Información adicional si está disponible
        if afiliado.ciudad_de_nacimiento:
            afiliado_data['ciudad_de_nacimiento'] = afiliado.ciudad_de_nacimiento
        if afiliado.estado_civil:
            afiliado_data['estado_civil'] = afiliado.estado_civil
        if afiliado.nombre_conyuge:
            afiliado_data['nombre_conyuge'] = afiliado.nombre_conyuge
        if afiliado.nombre_hijos:
            afiliado_data['nombre_hijos'] = afiliado.nombre_hijos
        if afiliado.direccion:
            afiliado_data['direccion'] = afiliado.direccion

        # Solo agregar si tiene al menos algún dato
        if afiliado_data:
            data.append(afiliado_data)

    return data


def afiliado_detail(request, pk):
    """
    Vista para mostrar los detalles de un afiliado específico.

    Muestra toda la información disponible de un afiliado incluyendo
    datos personales, profesionales y académicos.

    Args:
        request: HttpRequest object
        pk: Primary key del afiliado a mostrar

    Returns:
        HttpResponse: Página de detalles del afiliado

    Raises:
        Http404: Si el afiliado no existe
    """
    afiliado = get_object_or_404(Afiliado, pk=pk)
    return render(request, 'afiliados/afiliado_detail.html', {'afiliado': afiliado})


def afiliado_create(request):
    """
    Vista para crear un nuevo afiliado.

    Maneja tanto la presentación del formulario de creación como
    el procesamiento de los datos enviados para crear un nuevo afiliado.

    Args:
        request: HttpRequest object con posibles datos POST

    Returns:
        HttpResponse: Formulario de creación o redirección tras crear
    """
    if request.method == 'POST':
        try:
            # Función auxiliar para convertir strings vacíos a None
            def safe_value(field_name, default=None):
                """Obtiene un valor del POST, convirtiendo strings vacíos a None"""
                value = request.POST.get(field_name, '').strip()
                return value if value else default

            def safe_date(field_name):
                """Convierte una fecha string a formato válido o None"""
                value = safe_value(field_name)
                if not value:
                    return None
                try:
                    from datetime import datetime
                    datetime.strptime(value, '%Y-%m-%d')
                    return value
                except ValueError:
                    return None

            def safe_int(field_name, default=None):
                """Convierte un valor a entero o devuelve None"""
                value = safe_value(field_name)
                if not value:
                    return default
                try:
                    return int(value)
                except (ValueError, TypeError):
                    return default

            # Validar campos requeridos
            cedula = safe_value('cedula')
            nombre_completo = safe_value('nombre_completo')

            if not cedula or not nombre_completo:
                messages.error(request, 'La cédula y el nombre completo son obligatorios.')
                return render(request, 'afiliados/afiliado_form.html')

            # Crear afiliado con valores seguros
            afiliado = Afiliado.objects.create(
                cedula=cedula,
                nombre_completo=nombre_completo,
                municipio=safe_value('municipio'),
                ciudad_de_nacimiento=safe_value('ciudad_de_nacimiento'),
                fecha_nacimiento=safe_date('fecha_nacimiento'),
                edad=safe_int('edad'),
                estado_civil=safe_value('estado_civil'),
                nombre_conyuge=safe_value('nombre_conyuge'),
                nombre_hijos=safe_value('nombre_hijos'),
                direccion=safe_value('direccion'),
                telefono=safe_value('telefono'),
                email=safe_value('email'),
                grado_escalafon=safe_value('grado_escalafon'),
                cargo_desempenado=safe_value('cargo_desempenado'),
                fecha_ingreso=safe_date('fecha_ingreso'),
                anos_servicio=safe_int('anos_servicio'),
                titulo_pregrado=safe_value('titulo_pregrado'),
                titulo_posgrado=safe_value('titulo_posgrado'),
                estudios_posgrado=safe_value('estudios_posgrado'),
                otros_titulos=safe_value('otros_titulos'),
                activo=request.POST.get('activo') == 'on'
            )

            messages.success(
                request,
                f'✅ Afiliado {afiliado.nombre_completo} creado exitosamente.'
            )
            return redirect('afiliados:afiliado_detail', pk=afiliado.pk)

        except Exception as e:
            logger.exception("Error al crear afiliado")
            messages.error(
                request,
                f'❌ Error al crear el afiliado: {str(e)}'
            )
            return render(request, 'afiliados/afiliado_form.html')

    # GET request - mostrar formulario vacío
    return render(request, 'afiliados/afiliado_form.html')

def afiliado_delete(request, pk):
    """
    Vista para eliminar un afiliado.

    Args:
        request: HttpRequest object
        pk: Primary key del afiliado a eliminar

    Returns:
        HttpResponse: Página de confirmación o redirección tras eliminar
    """
    afiliado = get_object_or_404(Afiliado, pk=pk)

    if request.method == 'POST':
        nombre = afiliado.nombre_completo
        afiliado.delete()
        messages.success(request, f'✅ Afiliado {nombre} eliminado exitosamente.')
        return redirect('afiliados:afiliado_list')

    return render(request, 'afiliados/afiliado_confirm_delete.html', {'afiliado': afiliado})

def afiliado_update(request, pk):
    """
    Vista para actualizar un afiliado existente.

    Permite editar la información de un afiliado existente,
    mostrando el formulario prellenado con los datos actuales.
    Recalcula automáticamente el sueldo si cambian parámetros relevantes.

    Args:
        request: HttpRequest object con posibles datos POST
        pk: Primary key del afiliado a actualizar

    Returns:
        HttpResponse: Formulario de edición o redirección tras actualizar

    Raises:
        Http404: Si el afiliado no existe
    """
    afiliado = get_object_or_404(Afiliado, pk=pk)

    if request.method == 'POST':
        try:
            # Función auxiliar para convertir strings vacíos a None
            def safe_value(field_name, default=None):
                """Obtiene un valor del POST, convirtiendo strings vacíos a None"""
                value = request.POST.get(field_name, '').strip()
                return value if value else default

            def safe_date(field_name):
                """Convierte una fecha string a formato válido o None"""
                value = safe_value(field_name)
                if not value:
                    return None
                try:
                    # Validar que tenga formato correcto
                    from datetime import datetime
                    datetime.strptime(value, '%Y-%m-%d')
                    return value
                except ValueError:
                    return None

            def safe_int(field_name, default=None):
                """Convierte un valor a entero o devuelve None"""
                value = safe_value(field_name)
                if not value:
                    return default
                try:
                    return int(value)
                except (ValueError, TypeError):
                    return default

            # Guardar valores originales para comparar
            campos_sueldo = ['grado_escalafon', 'cargo_desempenado', 'anos_servicio', 'titulo_posgrado', 'estudios_posgrado']
            valores_originales = {campo: getattr(afiliado, campo) for campo in campos_sueldo}

            # Actualizar campos básicos
            afiliado.cedula = safe_value('cedula') or afiliado.cedula
            afiliado.nombre_completo = safe_value('nombre_completo') or afiliado.nombre_completo

            # Información geográfica y personal
            afiliado.municipio = safe_value('municipio')
            afiliado.ciudad_de_nacimiento = safe_value('ciudad_de_nacimiento')
            afiliado.fecha_nacimiento = safe_date('fecha_nacimiento')
            afiliado.edad = safe_int('edad')
            afiliado.estado_civil = safe_value('estado_civil')
            afiliado.nombre_conyuge = safe_value('nombre_conyuge')
            afiliado.nombre_hijos = safe_value('nombre_hijos')

            # Información de contacto
            afiliado.direccion = safe_value('direccion')
            afiliado.telefono = safe_value('telefono')
            afiliado.email = safe_value('email')

            # Información profesional (campos que afectan el sueldo)
            afiliado.grado_escalafon = safe_value('grado_escalafon')
            afiliado.cargo_desempenado = safe_value('cargo_desempenado')
            afiliado.fecha_ingreso = safe_date('fecha_ingreso')
            afiliado.anos_servicio = safe_int('anos_servicio')

            # Información académica (campos que afectan el sueldo)
            afiliado.titulo_pregrado = safe_value('titulo_pregrado')
            afiliado.titulo_posgrado = safe_value('titulo_posgrado')
            afiliado.estudios_posgrado = safe_value('estudios_posgrado')
            afiliado.otros_titulos = safe_value('otros_titulos')

            # Estado (checkbox)
            afiliado.activo = request.POST.get('activo') == 'on'

            # Verificar si cambiaron campos que afectan el sueldo
            campos_cambiaron = any(
                getattr(afiliado, campo) != valor_original
                for campo, valor_original in valores_originales.items()
            )

            # Guardar cambios en el afiliado
            afiliado.save()

            # Recalcular sueldo si cambiaron parámetros relevantes
            if campos_cambiaron:
                try:
                    from liquidacion.services.calculo_sueldo import CalculadorSueldo

                    # Obtener el año actual para el cálculo
                    anio_actual = datetime.now().year

                    # Crear calculadora y recalcular
                    calculadora = CalculadorSueldo(afiliado, anio_actual)
                    sueldo, created, calculo = calculadora.crear_o_actualizar_sueldo()

                    if sueldo and 'error' not in calculo:
                        messages.success(
                            request,
                            f'✅ Afiliado {afiliado.nombre_completo} actualizado exitosamente. ' +
                            f'Sueldo {"creado" if created else "actualizado"}: ${calculo["sueldo_neto"]:,.2f}'
                        )
                        logger.info(f'Sueldo recalculado para {afiliado.cedula}: ${calculo["sueldo_neto"]:,.2f}')
                    else:
                        error_msg = calculo.get('error', 'Error desconocido')
                        messages.warning(
                            request,
                            f'✅ Afiliado actualizado, pero no se pudo recalcular el sueldo: {error_msg}'
                        )
                        logger.error(f'Error recalculando sueldo para {afiliado.cedula}: {error_msg}')

                except Exception as e:
                    messages.warning(
                        request,
                        f'✅ Afiliado actualizado, pero ocurrió un error al recalcular el sueldo: {str(e)}'
                    )
                    logger.exception(f'Excepción al recalcular sueldo para {afiliado.cedula}')
            else:
                messages.success(
                    request,
                    f'✅ Afiliado {afiliado.nombre_completo} actualizado exitosamente.'
                )

            return redirect('afiliados:afiliado_detail', pk=afiliado.pk)

        except Exception as e:
            logger.exception(f"Error al actualizar afiliado {pk}")
            messages.error(
                request,
                f'❌ Error al actualizar el afiliado: {str(e)}'
            )

    # GET request - mostrar formulario
    return render(request, 'afiliados/afiliado_form.html', {'afiliado': afiliado})

@login_required
def recalcular_sueldo(request, pk):
    """
    Vista para recalcular manualmente el sueldo de un afiliado.

    Args:
        request: HttpRequest object
        pk: Primary key del afiliado

    Returns:
        HttpResponseRedirect: Redirige al detalle del afiliado con mensaje de resultado
    """
    if request.method == 'POST':
        try:
            afiliado = get_object_or_404(Afiliado, pk=pk)

            # Obtener el año actual para el cálculo
            anio_actual = datetime.now().year

            # Importar aquí para evitar importación circular
            from liquidacion.services.calculo_sueldo import CalculadorSueldo

            # Crear calculadora y recalcular
            calculadora = CalculadorSueldo(afiliado, anio_actual)
            sueldo, created, calculo = calculadora.crear_o_actualizar_sueldo()

            if sueldo and 'error' not in calculo:
                messages.success(
                    request,
                    f'✅ Sueldo recalculado exitosamente: ${calculo["sueldo_neto"]:,.2f} '
                    f'({afiliado.nombre_completo})'
                )
                logger.info(f'Sueldo recalculado manualmente para {afiliado.cedula}: ${calculo["sueldo_neto"]:,.2f}')
            else:
                error_msg = calculo.get('error', 'Error desconocido')
                messages.error(
                    request,
                    f'❌ No se pudo recalcular el sueldo: {error_msg}'
                )
                logger.error(f'Error recalculando sueldo manualmente para {afiliado.cedula}: {error_msg}')

        except Exception as e:
            logger.exception(f'Error al recalcular sueldo manualmente para afiliado {pk}')
            messages.error(
                request,
                f'❌ Error inesperado al recalcular sueldo: {str(e)}'
            )

    # Redirigir al detalle del afiliado
    return redirect('afiliados:afiliado_detail', pk=pk)


@cache_page(300)
def datos_secretaria_list(request):
    """
    Vista para mostrar y buscar datos de secretaría.

    Permite buscar registros de secretaría por cédula, nombre o municipio
    y muestra los resultados en una tabla paginada.

    Args:
        request: HttpRequest object

    Returns:
        HttpResponse: Página de lista de datos de secretaría
    """
    # Obtener parámetros de búsqueda
    search_query = request.GET.get('search', '').strip()

    # Filtrar datos de secretaría
    datos_secretaria = DatosSecretaria.objects.only('id', 'cedula', 'nombre_completo', 'municipio', 'fecha_creacion')

    if search_query:
        datos_secretaria = datos_secretaria.filter(
            Q(cedula__icontains=search_query) |
            Q(nombre_completo__icontains=search_query) |
            Q(municipio__icontains=search_query)
        )

    # Configurar paginación
    page_number = request.GET.get('page', 1)
    items_per_page = 20

    paginator = Paginator(datos_secretaria, items_per_page)

    try:
        datos_secretaria_page = paginator.page(page_number)
    except PageNotAnInteger:
        datos_secretaria_page = paginator.page(1)
    except EmptyPage:
        datos_secretaria_page = paginator.page(paginator.num_pages)

    # Almacenar búsqueda en sesión para mantener filtros en exportaciones
    request.session['search_query_secretaria'] = search_query

    return render(request, 'afiliados/datos_secretaria_list.html', {
        'datos_secretaria': datos_secretaria_page,
        'search_query': search_query,
        'total_secretaria': paginator.count,
        'is_paginated': paginator.num_pages > 1,
        'page_obj': datos_secretaria_page,
    })


@cache_page(300)
def datos_organizacion_list(request):
    """
    Vista para mostrar y buscar datos de ADEMACOR.

    Permite buscar registros de ADEMACOR por cédula, nombre o municipio
    y muestra los resultados en una tabla paginada.

    Args:
        request: HttpRequest object

    Returns:
        HttpResponse: Página de lista de datos de ADEMACOR
    """
    # Obtener parámetros de búsqueda
    search_query = request.GET.get('search', '').strip()

    # Filtrar datos de ADEMACOR
    datos_ademacor = DatosAdemacor.objects.only('id', 'cedula', 'nombre_completo', 'municipio', 'fecha_creacion')

    if search_query:
        datos_ademacor = datos_ademacor.filter(
            Q(cedula__icontains=search_query) |
            Q(nombre_completo__icontains=search_query) |
            Q(municipio__icontains=search_query)
        )

    # Configurar paginación
    page_number = request.GET.get('page', 1)
    items_per_page = 20

    paginator = Paginator(datos_ademacor, items_per_page)

    try:
        datos_ademacor_page = paginator.page(page_number)
    except PageNotAnInteger:
        datos_ademacor_page = paginator.page(1)
    except EmptyPage:
        datos_ademacor_page = paginator.page(paginator.num_pages)

    # Almacenar búsqueda en sesión para mantener filtros en exportaciones
    request.session['search_query_ademacor'] = search_query

    return render(request, 'afiliados/datos_ademacor_list.html', {
        'datos_ademacor': datos_ademacor_page,
        'search_query': search_query,
        'total_ademacor': paginator.count,
        'is_paginated': paginator.num_pages > 1,
        'page_obj': datos_ademacor_page,
    })



def datos_organizacion_detail(request, pk):
    """
    Vista para mostrar los detalles de un registro de ADEMACOR.

    Args:
        request: HttpRequest object
        pk: Primary key del registro de ADEMACOR

    Returns:
        HttpResponse: Página de detalles del registro de ADEMACOR
    """
    registro = get_object_or_404(DatosAdemacor, pk=pk)
    return render(request, 'afiliados/datos_ademacor_detail.html', {'registro': registro})


def datos_organizacion_edit(request, pk):
    """
    Vista para editar un registro de ADEMACOR.

    Args:
        request: HttpRequest object
        pk: Primary key del registro de ADEMACOR a editar

    Returns:
        HttpResponse: Formulario de edición o redirección tras actualizar
    """
    registro = get_object_or_404(DatosAdemacor, pk=pk)

    if request.method == 'POST':
        registro.cedula = request.POST.get('cedula')
        registro.nombre_completo = request.POST.get('nombre_completo')
        registro.municipio = request.POST.get('municipio')
        registro.save()

        messages.success(request, f'Registro de ADEMACOR actualizado exitosamente.')
        return redirect('afiliados:datos_ademacor_detail', pk=registro.pk)

    return render(request, 'afiliados/datos_ademacor_form.html', {'registro': registro})


def datos_organizacion_delete(request, pk):
    """
    Vista para eliminar un registro de ADEMACOR.

    Args:
        request: HttpRequest object
        pk: Primary key del registro de ADEMACOR a eliminar

    Returns:
        HttpResponse: Página de confirmación o redirección tras eliminar
    """
    registro = get_object_or_404(DatosAdemacor, pk=pk)

    if request.method == 'POST':
        registro.delete()
        messages.success(request, f'Registro de ADEMACOR eliminado exitosamente.')
        return redirect('afiliados:datos_ademacor_list')

    return render(request, 'afiliados/datos_ademacor_confirm_delete.html', {'registro': registro})


@cache_page(300)
def datos_organizacion_list(request):
    """
    Vista para mostrar y buscar datos de organización externa.

    Args:
        request: HttpRequest object

    Returns:
        HttpResponse: Página de lista de datos de organización externa
    """
    try:
        # Obtener término de búsqueda de la sesión
        search_query = request.session.get('search_query_ademacor', '')

        # Obtener datos de organización externa según filtros
        datos_organizacion = DatosOrganizacion.objects.all()
        datos_ademacor = DatosAdemacor.objects.all()

        if search_query:
            datos_ademacor = datos_ademacor.filter(
                Q(cedula__icontains=search_query) |
                Q(nombre_completo__icontains=search_query) |
                Q(municipio__icontains=search_query)
            )

        # Preparar datos para exportación
        data = []
        for registro in datos_ademacor:
            data.append({
                'cedula': registro.cedula,
                'nombre_completo': registro.nombre_completo,
                'municipio': registro.municipio or '',
                'descripcion': registro.descripcion,
            })

        if not data:
            messages.warning(request, 'No hay datos de ADEMACOR para exportar.')
            return redirect('afiliados:datos_ademacor_list')

        # Crear servicio dinámico con los datos preparados
        from afiliados.services.export import DynamicExportService
        export_service = DynamicExportService(data, "Datos ADEMACOR - SIGAA")

        # Obtener estadísticas
        stats = export_service.get_export_stats()

        # Generar nombre del archivo con fecha y hora
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"datos_ademacor_{timestamp}"

        # Exportar a Excel
        response = export_service.export_excel(filename)

        # Log de la exportación
        logger.info(f"Exportación Excel de ADEMACOR realizada: {stats['total_registros']} registros, "
                   f"Columnas: {stats['columnas_exportadas']}")

        # Mensaje de éxito
        messages.success(
            request,
            f'Exportación Excel generada exitosamente: {stats["total_registros"]} registros, '
            f'{stats["columnas_exportadas"]} columnas exportadas.'
        )

        return response

    except Exception as e:
        logger.exception("Error al exportar datos de ADEMACOR a Excel")
        messages.error(request, f'Error al generar la exportación: {str(e)}')
        return redirect('afiliados:datos_ademacor_list')







def datos_organizacion_export(request):
    """
    Vista para exportar datos de organización externa a Excel.

    Args:
        request: HttpRequest object

    Returns:
        HttpResponse: Archivo Excel para descarga
    """
    try:
        # Obtener término de búsqueda de la sesión
        search_query = request.session.get('search_query_organizacion', '')

        # Obtener datos de organización externa según filtros
        datos_organizacion = DatosOrganizacion.objects.all()

        if search_query:
            datos_organizacion = datos_organizacion.filter(
                Q(cedula__icontains=search_query) |
                Q(nombre_completo__icontains=search_query) |
                Q(municipio__icontains=search_query)
            )

        # Preparar datos para exportación
        data = []
        for registro in datos_organizacion:
            data.append({
                'cedula': registro.cedula,
                'nombre_completo': registro.nombre_completo,
                'municipio': registro.municipio or '',
                'descripcion': registro.descripcion,
            })

        if not data:
            messages.warning(request, 'No hay datos de organización externa para exportar.')
            return redirect('afiliados:datos_organizacion_list')

        # Crear servicio dinámico con los datos preparados
        from afiliados.services.export import DynamicExportService
        export_service = DynamicExportService(data, "Datos de Organización - SIGAA")

        # Obtener estadísticas
        stats = export_service.get_export_stats()

        # Generar nombre del archivo con fecha y hora
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"datos_organizacion_{timestamp}"

        # Exportar a Excel
        response = export_service.export_excel(filename)

        # Log de la exportación
        logger.info(f"Exportación Excel de organización realizada: {stats['total_registros']} registros, "
                   f"Columnas: {stats['columnas_exportadas']}")

        # Mensaje de éxito
        messages.success(request, f'Se exportaron exitosamente {stats["total_registros"]} registros.')

        return response

    except Exception as e:
        logger.exception("Error al exportar datos de organización a Excel")
        messages.error(request, f'Error al generar la exportación: {str(e)}')
        return redirect('afiliados:datos_organizacion_list')


def datos_organizacion_export_pdf(request):
    """
    Vista para exportar datos de ADEMACOR a PDF.

    Args:
        request: HttpRequest object

    Returns:
        HttpResponse: Archivo PDF para descarga
    """
    try:
        # Obtener término de búsqueda de la sesión
        search_query = request.session.get('search_query_ademacor', '')

        # Obtener datos de ADEMACOR según filtros
        datos_ademacor = DatosAdemacor.objects.all()

        if search_query:
            datos_ademacor = datos_ademacor.filter(
                Q(cedula__icontains=search_query) |
                Q(nombre_completo__icontains=search_query) |
                Q(municipio__icontains=search_query)
            )

        # Preparar datos para exportación
        data = []
        for registro in datos_ademacor:
            data.append({
                'cedula': registro.cedula,
                'nombre_completo': registro.nombre_completo,
                'municipio': registro.municipio or '',
                'descripcion': registro.descripcion,
            })

        if not data:
            messages.warning(request, 'No hay datos de ADEMACOR para exportar.')
            return redirect('afiliados:datos_ademacor_list')

        # Crear servicio dinámico con los datos preparados
        from afiliados.services.export import DynamicExportService
        export_service = DynamicExportService(data, "Datos ADEMACOR - SIGAA")

        # Obtener estadísticas
        stats = export_service.get_export_stats()

        # Generar nombre del archivo con fecha y hora
        from datetime import datetime
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"datos_ademacor_{timestamp}"

        # Exportar a PDF con logotipo
        logo_path = "img/logotipo1.png"
        response = export_service.export_pdf(filename, logo_path)

        # Log de la exportación
        logger.info(f"Exportación PDF de ADEMACOR realizada: {stats['total_registros']} registros, "
                   f"Columnas: {stats['columnas_exportadas']}")

        # Mensaje de éxito
        messages.success(
            request,
            f'Exportación PDF generada exitosamente: {stats["total_registros"]} registros, '
            f'{stats["columnas_exportadas"]} columnas exportadas.'
        )

        return response

    except Exception as e:
        logger.exception("Error al exportar datos de ADEMACOR a PDF")
        messages.error(request, f'Error al generar la exportación: {str(e)}')
        return redirect('afiliados:datos_ademacor_list')


def comparacion_afiliados_organizacion(request):
    """
    Vista para comparar datos entre Afiliados (General) y ADEMACOR.
    """
    from afiliados.services.ademacor_comparison import comparar_afiliados_ademacor

    municipio_filtro = request.GET.get('municipio', '').strip()
    if not municipio_filtro:
        municipio_filtro = None

    resultados = comparar_afiliados_ademacor(municipio_filtro)

    # Obtener lista de municipios para el filtro
    from afiliados.models import Afiliado, DatosAdemacor
    municipios_gral = Afiliado.objects.values_list('municipio', flat=True).distinct()
    municipios_adem = DatosAdemacor.objects.values_list('municipio', flat=True).distinct()
    municipios = sorted(list(set(list(municipios_gral) + list(municipios_adem))))
    municipios = [m for m in municipios if m] # Filtrar vacíos

    return render(request, 'afiliados/comparacion_afiliados_ademacor.html', {
        'resultados': resultados,
        'municipios': municipios,
        'municipio_actual': municipio_filtro
    })

