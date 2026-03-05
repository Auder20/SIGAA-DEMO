from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.cache import cache_page
from django.contrib import messages
from .models import Reporte, ReporteAportesTotales
from django.http import HttpResponse
from django.core.files.base import ContentFile
# import pandas as pd  # Temporalmente comentado para migraciones
from afiliados.models import Afiliado
from liquidacion.models import Sueldo, TablaSalarial, Bonificacion, Aporte
import io
from datetime import datetime
from decimal import Decimal
from decimal import Decimal


@cache_page(300)
def reportes_main(request):
	"""
	Vista principal de reportes. Muestra enlaces a lista y creación de reportes.
	"""
	# Calcular estadísticas
	total_reportes = Reporte.objects.count()
	total_afiliados = Afiliado.objects.count()
	total_sueldos = Sueldo.objects.count()
	total_aportes = Aporte.objects.count()

	context = {
		'total_reportes': total_reportes,
		'total_afiliados': total_afiliados,
		'total_sueldos': total_sueldos,
		'total_aportes': total_aportes,
	}

	return render(request, 'reportes/main.html', context)

# @cache_page(300)
def reporte_list(request):
    """
    Vista para listar reportes con filtros avanzados:
    - Búsqueda por texto (tipo, descripción, generado_por)
    - Filtro por fecha exacta
    - Filtro por mes
    - Filtro por tipo
    """
    from django.db.models import Q
    from datetime import datetime

    # Obtener parámetros de filtro
    search = request.GET.get('search', '').strip()
    tipo = request.GET.get('tipo', '').strip()
    fecha_exacta = request.GET.get('fecha_exacta', '').strip()
    mes = request.GET.get('mes', '').strip()
    ano = request.GET.get('ano', '').strip()

    # Construir consulta base
    reportes = Reporte.objects.all().order_by('-fecha_generado')

    # Aplicar filtros
    if search:
        reportes = reportes.filter(
            Q(tipo__icontains=search) |
            Q(descripcion__icontains=search) |
            Q(generado_por__username__icontains=search) |
            Q(generado_por__first_name__icontains=search) |
            Q(generado_por__last_name__icontains=search)
        )

    if tipo:
        reportes = reportes.filter(tipo=tipo)

    if fecha_exacta:
        try:
            fecha_obj = datetime.strptime(fecha_exacta, '%Y-%m-%d').date()
            reportes = reportes.filter(fecha_generado__date=fecha_obj)
        except ValueError:
            pass  # Si la fecha no es válida, ignorar el filtro

    if mes and ano:
        try:
            mes_int = int(mes)
            ano_int = int(ano)
            reportes = reportes.filter(
                fecha_generado__year=ano_int,
                fecha_generado__month=mes_int
            )
        except (ValueError, TypeError):
            pass  # Si los valores no son válidos, ignorar el filtro

    # Paginación
    from django.core.paginator import Paginator
    paginator = Paginator(reportes, 20)  # 20 reportes por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Preparar opciones para los filtros de mes/año
    meses = [
        ('1', 'Enero'), ('2', 'Febrero'), ('3', 'Marzo'), ('4', 'Abril'),
        ('5', 'Mayo'), ('6', 'Junio'), ('7', 'Julio'), ('8', 'Agosto'),
        ('9', 'Septiembre'), ('10', 'Octubre'), ('11', 'Noviembre'), ('12', 'Diciembre')
    ]

    anos = []
    ano_actual = datetime.now().year
    for i in range(ano_actual, ano_actual - 5, -1):  # Últimos 5 años
        anos.append((str(i), str(i)))

    context = {
        'reportes': page_obj,
        'is_paginated': True,
        'total_reportes': paginator.count,  # Conteo total de reportes
        'meses': meses,
        'anos': anos,
        'request': request,
    }

    return render(request, 'reportes/reporte_list.html', context)

@cache_page(300)
def reporte_detail(request, pk):
	reporte = get_object_or_404(Reporte, pk=pk)
	return render(request, 'reportes/reporte_detail.html', {'reporte': reporte})

def reporte_create(request):
	if request.method == 'POST':
		# Procesar formulario
		# ...
		return redirect('reporte_list')
	return render(request, 'reportes/reporte_form.html')

def reporte_update(request, pk):
	reporte = get_object_or_404(Reporte, pk=pk)
	if request.method == 'POST':
		# Procesar formulario
		# ...
		return redirect('reporte_detail', pk=reporte.pk)
	return render(request, 'reportes/reporte_form.html', {'reporte': reporte})

def reporte_delete(request, pk):
	reporte = get_object_or_404(Reporte, pk=pk)
	if request.method == 'POST':
		return redirect('reporte_list')
	return render(request, 'reportes/reporte_confirm_delete.html', {'reporte': reporte})


def generar_reporte_diferencias(request):
    """
    Vista para generar reporte de diferencias entre Secretaría y ADEMACOR
    Ahora genera reporte consolidado sin filtro previo de municipio
    """
    if request.method == 'POST':
        from .services.diferencias_service import generar_datos_diferencias
        formato = request.POST.get('formato', 'pantalla')

        # Generar datos de diferencias sin filtro de municipio (reporte consolidado)
        diferencias = generar_datos_diferencias()

        if formato == 'pantalla':
            # Generar y registrar en BD (Excel y PDF), luego mostrar en pantalla
            _ = _generar_y_registrar_diferencias(diferencias, request)
            return render(request, 'reportes/diferencias_secretaria_ademacor.html', {
                'diferencias': diferencias
            })
        elif formato == 'excel':
            # Exportar a Excel y registrar en BD (guardar también PDF)
            excel_resp, pdf_resp = _generar_y_registrar_diferencias(diferencias, request)
            return excel_resp
        elif formato == 'pdf':
            # Exportar a PDF y registrar en BD (guardar también Excel)
            excel_resp, pdf_resp = _generar_y_registrar_diferencias(diferencias, request)
            return pdf_resp

    return render(request, 'reportes/generar_diferencias.html')


def _generar_y_registrar_diferencias(diferencias, request):
    """Genera Excel, crea un Reporte con el archivo y devuelve (excel_resp, None)."""
    from .services.diferencias_service import exportar_diferencias_excel_multipage
    excel_response = exportar_diferencias_excel_multipage(diferencias)
    pdf_response = None # PDF generation temporarily disabled

    def _get_filename(resp, fallback):
        if resp is None:
            return fallback
        cd = resp.get('Content-Disposition', '') or ''
        if 'filename=' in cd:
            return cd.split('filename=')[-1].strip('"')
        return fallback

    excel_filename = _get_filename(excel_response, 'diferencias_secretaria_ademacor.xlsx')

    descripcion = (
        f"Diferencias Secretaría vs ADEMACOR. "
        f"Totales - Secretaría: {diferencias['estadisticas']['total_general']}, "
        f"ADEMACOR: {diferencias['estadisticas']['total_ademacor']}, "
        f"Solo Secretaría: {diferencias['estadisticas']['solo_general']}, "
        f"Solo ADEMACOR: {diferencias['estadisticas']['solo_ademacor']}, "
        f"En ambos: {diferencias['estadisticas']['ambos']}. "
        f"Generado: {diferencias['estadisticas']['fecha_generacion']}"
        f"{' | Filtro municipio: ' + diferencias['estadisticas']['municipio_filtro'] if diferencias['estadisticas']['municipio_filtro'] != 'Todos' else ''}"
    )

    reporte = Reporte(
        tipo='diferencias_secretaria_ademacor',
        generado_por=request.user if request.user.is_authenticated else None,
        descripcion=descripcion,
    )
    # Guardar archivos solo si las respuestas no son None
    if excel_response:
        reporte.archivo_excel.save(excel_filename, ContentFile(excel_response.content), save=False)

    reporte.save()

    return excel_response, pdf_response

def _generar_y_registrar_diferencias_filtrado(diferencias_data, filtro_aplicado, request):
    """Genera Excel con datos filtrados, crea un Reporte con el archivo y devuelve (excel_resp, None)."""
    from .services.diferencias_service import exportar_diferencias_excel_multipage_filtrado
    excel_response = exportar_diferencias_excel_multipage_filtrado(diferencias_data)
    pdf_response = None # PDF generation temporarily disabled

    def _get_filename(resp, fallback):
        if resp is None:
            return fallback
        cd = resp.get('Content-Disposition', '') or ''
        if 'filename=' in cd:
            return cd.split('filename=')[-1].strip('"')
        return fallback

    excel_filename = _get_filename(excel_response, 'diferencias_secretaria_ademacor_filtrado.xlsx')

    descripcion = (
        f"Diferencias Secretaría vs ADEMACOR (Filtrado). "
        f"Totales - Secretaría: {diferencias_data['estadisticas']['total_general']}, "
        f"ADEMACOR: {diferencias_data['estadisticas']['total_ademacor']}, "
        f"Solo Secretaría: {diferencias_data['estadisticas']['solo_general']}, "
        f"Solo ADEMACOR: {diferencias_data['estadisticas']['solo_ademacor']}, "
        f"En ambos: {diferencias_data['estadisticas']['ambos']}. "
        f"Generado: {diferencias_data['estadisticas']['fecha_generacion']}"
        f" | Filtro aplicado: {filtro_aplicado if filtro_aplicado else 'Todos'}"
    )

    reporte = Reporte(
        tipo='diferencias_secretaria_ademacor_filtrado',
        generado_por=request.user if request.user.is_authenticated else None,
        descripcion=descripcion,
    )
    # Guardar archivos solo si las respuestas no son None
    if excel_response:
        reporte.archivo_excel.save(excel_filename, ContentFile(excel_response.content), save=False)

    reporte.save()

    return excel_response, pdf_response

def exportar_diferencias_excel_view(request):
    """
    Vista para exportar diferencias directamente a Excel con múltiples hojas
    """
    from .services.diferencias_service import generar_datos_diferencias
    diferencias = generar_datos_diferencias()
    excel_resp, _ = _generar_y_registrar_diferencias(diferencias, request)
    return excel_resp


def exportar_diferencias_pdf_view(request):
    """
    Vista para exportar diferencias directamente a PDF con múltiples hojas
    """
    from .services.diferencias_service import generar_datos_diferencias
    diferencias = generar_datos_diferencias()
    _, pdf_resp = _generar_y_registrar_diferencias(diferencias, request)
    return pdf_resp


def exportar_diferencias_excel_filtrado(request):
    """
    Vista para exportar diferencias a Excel con filtro aplicado
    """
    if request.method == 'POST':
        try:
            import json
            diferencias_data = json.loads(request.POST.get('diferencias_data', '{}'))
            filtro_aplicado = request.POST.get('filtro_aplicado', '')

            # Generar archivos y registrar en BD
            excel_response, pdf_response = _generar_y_registrar_diferencias_filtrado(diferencias_data, filtro_aplicado, request)
            return excel_response
        except (json.JSONDecodeError, KeyError):
            # Si hay error, volver a generar reporte completo
            from .services.diferencias_service import generar_datos_diferencias
            diferencias = generar_datos_diferencias()
            excel_response, pdf_response = _generar_y_registrar_diferencias(diferencias, request)
            return excel_response

    return redirect('reportes:generar_reporte_diferencias')


def exportar_diferencias_pdf_filtrado(request):
    """
    Vista para exportar diferencias a PDF con filtro aplicado
    """
    if request.method == 'POST':
        try:
            import json
            diferencias_data = json.loads(request.POST.get('diferencias_data', '{}'))
            filtro_aplicado = request.POST.get('filtro_aplicado', '')

            # Generar archivos y registrar en BD
            excel_response, pdf_response = _generar_y_registrar_diferencias_filtrado(diferencias_data, filtro_aplicado, request)
            return pdf_response
        except (json.JSONDecodeError, KeyError):
            # Si hay error, volver a generar reporte completo
            from .services.diferencias_service import generar_datos_diferencias
            diferencias = generar_datos_diferencias()
            excel_response, pdf_response = _generar_y_registrar_diferencias(diferencias, request)
            return pdf_response

    return redirect('reportes:generar_reporte_diferencias')


# ==================== VISTAS PARA REPORTES DE TOTALES DE APORTES ====================

def reportes_aportes_totales_main(request):
    """
    Vista principal para reportes de totales de aportes.
    Muestra el formulario para generar reportes y el historial.
    """
    # Obtener reportes existentes
    reportes = ReporteAportesTotales.objects.all().order_by('-anio', '-mes')

    # Preparar opciones de meses y años
    meses = [
        (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
        (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
        (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
    ]

    año_actual = datetime.now().year
    años = [(anio, str(anio)) for anio in range(año_actual, año_actual - 3, -1)]

    context = {
        'reportes': reportes,
        'meses': meses,
        'años': años,
        'mes_actual': datetime.now().month,
        'año_actual': año_actual,
    }

    return render(request, 'reportes/aportes_totales_main.html', context)


def generar_reporte_aportes_totales(request):
    """
    Vista para generar reporte de totales de aportes.
    Calcula los totales y muestra en pantalla o exporta a Excel/PDF.
    """
    if request.method == 'POST':
        mes = request.POST.get('mes')
        año = request.POST.get('anio')
        formato = request.POST.get('formato', 'pantalla')

        # Validar que los datos no sean nulos
        if not mes or not año:
            messages.error(request, 'Debe seleccionar mes y año para generar el reporte.')
            return redirect('reportes:reportes_aportes_totales_main')

        try:
            mes = int(mes)
            año = int(año)
        except ValueError:
            messages.error(request, 'Los valores de mes y año deben ser válidos.')
            return redirect('reportes:reportes_aportes_totales_main')

        # Obtener o crear el reporte
        reporte, creado = ReporteAportesTotales.objects.get_or_create(
            mes=mes,
            anio=año,
            defaults={
                'calculado_por': request.user if request.user.is_authenticated else None
            }
        )

        # Calcular totales
        reporte.calcular_totales()

        if formato == 'pantalla':
            # Generar archivos y mostrar en pantalla
            _generar_archivos_reporte_aportes(reporte, request)
            return render(request, 'reportes/aportes_totales_detalle.html', {
                'reporte': reporte
            })
        elif formato == 'excel':
            # Exportar a Excel
            excel_response = _exportar_aportes_totales_excel(reporte, request)
            return excel_response
        elif formato == 'pdf':
            # Exportar a PDF
            pdf_response = _exportar_aportes_totales_pdf(reporte, request)
            return pdf_response

    return redirect('reportes:reportes_aportes_totales_main')


def detalle_reporte_aportes_totales(request, pk):
    """
    Vista para mostrar el detalle de un reporte de totales de aportes.
    """
    reporte = get_object_or_404(ReporteAportesTotales, pk=pk)

    # Obtener detalles de aportes para el período
    detalles_aportes = _obtener_detalles_aportes_periodo(reporte.anio, reporte.mes)

    # Calcular conteos para evitar usar selectattr
    detalles_ademacor = [d for d in detalles_aportes if d['aporte_nombre'].upper() == 'ADEMACOR']
    detalles_famecor = [d for d in detalles_aportes if d['aporte_nombre'].upper() == 'FAMECOR']

    context = {
        'reporte': reporte,
        'detalles_aportes': detalles_aportes,
        'detalles_ademacor': detalles_ademacor,
        'detalles_famecor': detalles_famecor,
    }

    return render(request, 'reportes/aportes_totales_detalle.html', context)


def exportar_aportes_totales_excel(request, pk):
    """
    Vista para exportar reporte de totales de aportes a Excel.
    """
    reporte = get_object_or_404(ReporteAportesTotales, pk=pk)
    result = _exportar_aportes_totales_excel(reporte, request)

    if result is None:
        # Si hay error, mostrar mensaje
        messages.error(request, 'No se pudo generar el archivo Excel. Por favor, intente nuevamente.')
        return redirect('reportes:detalle_reporte_aportes_totales', pk=pk)

    return result


def exportar_aportes_totales_pdf(request, pk):
    """
    Vista para exportar reporte de totales de aportes a PDF.
    """
    reporte = get_object_or_404(ReporteAportesTotales, pk=pk)
    result = _exportar_aportes_totales_pdf(reporte, request)

    if result is None:
        # Si hay error (probablemente weasyprint no instalado), mostrar mensaje
        messages.error(request, 'No se puede generar PDF. La librería WeasyPrint no está instalada. Por favor, instálea con: pip install weasyprint')
        return redirect('reportes:detalle_reporte_aportes_totales', pk=pk)

    return result


def recalcular_reporte_aportes_totales(request, pk):
    """
    Vista para recalcular un reporte de totales de aportes.
    """
    if request.method == 'POST':
        reporte = get_object_or_404(ReporteAportesTotales, pk=pk)

        # Recalcular totales
        reporte.calcular_totales()

        # Regenerar archivos
        _generar_archivos_reporte_aportes(reporte, request)

        return redirect('reportes:detalle_reporte_aportes_totales', pk=reporte.pk)

    return redirect('reportes:reportes_aportes_totales_main')


def actualizar_sueldos_desde_aportes(request, pk):
    """
    Vista para actualizar sueldos basados en los aportes del reporte.
    """
    if request.method == 'POST':
        reporte = get_object_or_404(ReporteAportesTotales, pk=pk)

        try:
            # Actualizar sueldos desde aportes
            resultado = reporte.actualizar_sueldos_desde_aportes()

            # Mostrar mensaje de éxito
            if resultado['sueldos_actualizados'] > 0:
                messages.success(
                    request,
                    f"Se actualizaron {resultado['sueldos_actualizados']} sueldos exitosamente. "
                    f"No se pudieron actualizar {resultado['sueldos_no_actualizables']} sueldos "
                    f"(sin datos de aportes válidos)."
                )
            else:
                messages.warning(
                    request,
                    "No se encontraron sueldos para actualizar. "
                    "Todos los sueldos ya tienen valor o no hay datos de aportes válidos."
                )

            # Recalcular totales del reporte después de actualizar sueldos
            reporte.calcular_totales()

        except Exception as e:
            messages.error(
                request,
                f"Error al actualizar sueldos: {str(e)}"
            )

        return redirect('reportes:detalle_reporte_aportes_totales', pk=reporte.pk)

    return redirect('reportes:reportes_aportes_totales_main')


# ==================== FUNCIONES AUXILIARES ====================

def _obtener_detalles_aportes_periodo(anio, mes):
    """
    Obtiene los detalles de todos los aportes para un período específico.

    Returns:
        list: Lista de diccionarios con detalles de cada aporte
    """
    detalles = []

    # Obtener sueldos del período
    sueldos = Sueldo.objects.filter(
        anio=anio
    ).select_related('afiliado').prefetch_related('aportes')

    for sueldo in sueldos:
        for aporte in sueldo.aportes.all():
            detalles.append({
                'afiliado': sueldo.afiliado,
                'cedula': sueldo.afiliado.cedula,
                'nombre_completo': sueldo.afiliado.nombre_completo,
                'cargo': sueldo.afiliado.cargo_desempenado,
                'sueldo_neto': sueldo.sueldo_neto,
                'aporte_nombre': aporte.nombre,
                'aporte_valor': aporte.valor,
                'aporte_porcentaje': aporte.porcentaje,
            })

    return detalles


def _generar_archivos_reporte_aportes(reporte, request):
    """
    Genera y guarda los archivos Excel y PDF para un reporte de aportes.
    """
    try:
        # Generar Excel
        excel_response = _exportar_aportes_totales_excel(reporte, request, save_to_db=False)
        if excel_response:
            filename_excel = f"reporte_aportes_totales_{reporte.anio}_{reporte.mes:02d}.xlsx"
            reporte.archivo_excel.save(filename_excel, ContentFile(excel_response.content))

        # Generar PDF
        pdf_response = _exportar_aportes_totales_pdf(reporte, request, save_to_db=False)
        if pdf_response:
            filename_pdf = f"reporte_aportes_totales_{reporte.anio}_{reporte.mes:02d}.pdf"
            reporte.archivo_pdf.save(filename_pdf, ContentFile(pdf_response.content))

        reporte.save()

    except Exception as e:
        # Si hay error generando archivos, continuar sin ellos
        pass


def _exportar_aportes_totales_excel(reporte, request, save_to_db=True):
    """
    Exporta reporte de totales de aportes a Excel.
    """
    try:
        # Crear DataFrame con datos resumidos
        datos_resumen = {
            'Concepto': ['ADEMACOR', 'FAMECOR', 'TOTAL GENERAL'],
            'Valor Total': [
                float(reporte.total_ademacor or 0),
                float(reporte.total_famecor or 0),
                float(reporte.total_general or 0)
            ],
            'Cantidad de Aportes': [
                reporte.cantidad_aportes_ademacor or 0,
                reporte.cantidad_aportes_famecor or 0,
                (reporte.cantidad_aportes_ademacor or 0) + (reporte.cantidad_aportes_famecor or 0)
            ],
            'Porcentaje': [
                float(reporte.get_porcentaje_ademacor() or 0),
                float(reporte.get_porcentaje_famecor() or 0),
                100.0
            ]
        }

        df_resumen = pd.DataFrame(datos_resumen)

        # Obtener detalles
        detalles = _obtener_detalles_aportes_periodo(reporte.anio, reporte.mes)

        # Crear DataFrame con detalles
        if detalles:
            df_detalles = pd.DataFrame(detalles)
            df_detalles = df_detalles[[
                'cedula', 'nombre_completo', 'cargo', 'sueldo_neto',
                'aporte_nombre', 'aporte_valor', 'aporte_porcentaje'
            ]]
            df_detalles.columns = [
                'Cédula', 'Nombre Completo', 'Cargo', 'Sueldo Neto',
                'Tipo Aporte', 'Valor Aporte', 'Porcentaje'
            ]
        else:
            df_detalles = pd.DataFrame(columns=[
                'Cédula', 'Nombre Completo', 'Cargo', 'Sueldo Neto',
                'Tipo Aporte', 'Valor Aporte', 'Porcentaje'
            ])

        # Crear archivo Excel con múltiples hojas
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Hoja de resumen
            df_resumen.to_excel(
                writer,
                sheet_name='Resumen',
                index=False,
                float_format="%.2f"
            )

            # Hoja de detalles
            df_detalles.to_excel(
                writer,
                sheet_name='Detalles',
                index=False,
                float_format="%.2f"
            )

            # Hoja de metadatos
            metadatos = {
                'Período': [f"{reporte.get_nombre_mes()} {reporte.anio}"],
                'Fecha de Generación': [reporte.fecha_calculo.strftime('%Y-%m-%d %H:%M:%S')],
                'Generado por': [str(reporte.calculado_por) if reporte.calculado_por else 'Sistema'],
                'Cantidad de Afiliados': [reporte.cantidad_afiliados],
                'Total ADEMACOR': [f"${reporte.total_ademacor:,.2f}"],
                'Total FAMECOR': [f"${reporte.total_famecor:,.2f}"],
                'Total General': [f"${reporte.total_general:,.2f}"]
            }
            df_metadatos = pd.DataFrame(metadatos)
            df_metadatos.to_excel(writer, sheet_name='Metadatos', index=False)

        output.seek(0)

        # Crear respuesta HTTP
        response = HttpResponse(
            output.read(),
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

        filename = f"reporte_aportes_totales_{reporte.anio}_{reporte.mes:02d}.xlsx"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        return response

    except Exception as e:
        # Si hay error, devolver None
        print(f"Error en exportación Excel: {e}")  # Debug
        return None


def _exportar_aportes_totales_pdf(reporte, request, save_to_db=True):
    """
    Exporta reporte de totales de aportes a PDF usando ReportLab.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        print(f"DEBUG: Iniciando exportación PDF para reporte {reporte.id}")
        print(f"DEBUG: Tipo de reporte: {type(reporte)}")

        # Obtener detalles
        detalles = _obtener_detalles_aportes_periodo(reporte.anio, reporte.mes)
        print(f"DEBUG: Tipo de detalles: {type(detalles)}")
        print(f"DEBUG: Cantidad de detalles: {len(detalles) if detalles else 'None'}")

        if detalles:
            print(f"DEBUG: Primer detalle: {detalles[0] if detalles else 'None'}")
            print(f"DEBUG: Tipo primer detalle: {type(detalles[0]) if detalles else 'None'}")

        # Crear el documento PDF
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        content = []

        # Estilos
        styles = getSampleStyleSheet()

        print("DEBUG: Creando título...")
        # Título
        title_style = styles['Title']
        title_style.textColor = colors.HexColor('#FF6B35')  # Naranja ADEMACOR
        content.append(Paragraph("REPORTE DE TOTALES DE APORTES", title_style))
        content.append(Spacer(1, 12))

        print("DEBUG: Creando información del reporte...")
        # Información del reporte
        info_style = styles['Normal']
        fecha_str = reporte.fecha_calculo.strftime('%d/%m/%Y %H:%M') if reporte.fecha_calculo else 'No calculado'
        content.append(Paragraph(f"<b>Período:</b> {reporte.get_nombre_mes()} {reporte.anio}", info_style))
        content.append(Paragraph(f"<b>Fecha de cálculo:</b> {fecha_str}", info_style))
        content.append(Spacer(1, 12))

        print("DEBUG: Creando tabla de resumen...")
        # Tabla de resumen
        resumen_data = [
            ['CONCEPTO', 'VALOR TOTAL', 'CANTIDAD', 'PORCENTAJE'],
            ['ADEMACOR', f"${float(reporte.total_ademacor or 0):,.2f}", str(reporte.cantidad_aportes_ademacor or 0), f"{float(reporte.get_porcentaje_ademacor() or 0):.2f}%"],
            ['FAMECOR', f"${float(reporte.total_famecor or 0):,.2f}", str(reporte.cantidad_aportes_famecor or 0), f"{float(reporte.get_porcentaje_famecor() or 0):.2f}%"],
            ['TOTAL GENERAL', f"${float(reporte.total_general or 0):,.2f}", str((reporte.cantidad_aportes_ademacor or 0) + (reporte.cantidad_aportes_famecor or 0)), "100.00%"]
        ]

        resumen_table = Table(resumen_data, colWidths=[2*inch, 1.5*inch, 1*inch, 1.2*inch])
        resumen_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF6B35')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#FFF5F0')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#FF6B35')),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
        ]))

        content.append(resumen_table)
        content.append(Spacer(1, 20))

        print("DEBUG: Procesando detalles de ADEMACOR...")
        # Detalles de ADEMACOR
        if detalles:
            detalles_ademacor = [d for d in detalles if d and d.get('aporte_nombre', '').upper() == 'ADEMACOR']
            print(f"DEBUG: Encontrados {len(detalles_ademacor)} detalles ADEMACOR")

            if detalles_ademacor:
                content.append(Paragraph("DETALLES - ADEMACOR", styles['Heading2']))
                content.append(Spacer(1, 6))

                ademacor_data = [['CÉDULA', 'NOMBRE', 'CARGO', 'SUELDO NETO', 'APORTE']]
                for i, d in enumerate(detalles_ademacor):
                    print(f"DEBUG: Procesando detalle ADEMACOR {i}: {d}")
                    ademacor_data.append([
                        d.get('cedula', ''),
                        (d.get('nombre_completo', '') or '')[:30] + '...' if len(d.get('nombre_completo', '') or '') > 30 else (d.get('nombre_completo', '') or ''),
                        (d.get('cargo', '') or '')[:20] + '...' if len(d.get('cargo', '') or '') > 20 else (d.get('cargo', '') or ''),
                        f"${float(d.get('sueldo_neto', 0) or 0):,.2f}",
                        f"${float(d.get('aporte_valor', 0) or 0):,.2f}"
                    ])

                ademacor_table = Table(ademacor_data, colWidths=[1*inch, 2.5*inch, 1.5*inch, 1.2*inch, 1*inch])
                ademacor_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF6B35')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#FFF5F0')),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#FF6B35')),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('ALIGN', (3, 1), (4, -1), 'RIGHT'),
                ]))

                content.append(ademacor_table)
                content.append(Spacer(1, 12))

            print("DEBUG: Procesando detalles de FAMECOR...")
            # Detalles de FAMECOR
            detalles_famecor = [d for d in detalles if d and d.get('aporte_nombre', '').upper() == 'FAMECOR']
            print(f"DEBUG: Encontrados {len(detalles_famecor)} detalles FAMECOR")

            if detalles_famecor:
                content.append(Paragraph("DETALLES - FAMECOR", styles['Heading2']))
                content.append(Spacer(1, 6))

                famecor_data = [['CÉDULA', 'NOMBRE', 'CARGO', 'SUELDO NETO', 'APORTE']]
                for i, d in enumerate(detalles_famecor):
                    print(f"DEBUG: Procesando detalle FAMECOR {i}: {d}")
                    famecor_data.append([
                        d.get('cedula', ''),
                        (d.get('nombre_completo', '') or '')[:30] + '...' if len(d.get('nombre_completo', '') or '') > 30 else (d.get('nombre_completo', '') or ''),
                        (d.get('cargo', '') or '')[:20] + '...' if len(d.get('cargo', '') or '') > 20 else (d.get('cargo', '') or ''),
                        f"${float(d.get('sueldo_neto', 0) or 0):,.2f}",
                        f"${float(d.get('aporte_valor', 0) or 0):,.2f}"
                    ])

                famecor_table = Table(famecor_data, colWidths=[1*inch, 2.5*inch, 1.5*inch, 1.2*inch, 1*inch])
                famecor_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF6B35')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 9),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#FFF5F0')),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#FF6B35')),
                    ('FONTSIZE', (0, 1), (-1, -1), 8),
                    ('ALIGN', (3, 1), (4, -1), 'RIGHT'),
                ]))

                content.append(famecor_table)

        print("DEBUG: Construyendo PDF...")
        # Construir el PDF
        doc.build(content)

        print("DEBUG: PDF construido, preparando respuesta...")
        # Preparar la respuesta
        buffer.seek(0)
        response = HttpResponse(buffer, content_type='application/pdf')
        filename = f"reporte_aportes_totales_{reporte.anio}_{reporte.mes or 'todos'}.pdf"
        response['Content-Disposition'] = f'attachment; filename="{filename}"'

        print("DEBUG: PDF generado exitosamente")
        return response

    except Exception as e:
        print(f"ERROR en exportación PDF con ReportLab: {e}")
        import traceback
        print(f"TRACEBACK: {traceback.format_exc()}")
        return None
