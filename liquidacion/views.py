# liquidacion/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.cache import cache_page
from django.views.generic import ListView, View
from django.utils.decorators import method_decorator
from django.db.models import Q, Sum, Count, F, Avg
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
import json
from .models import Sueldo, Aporte

@cache_page(300)
def liquidacion_main(request):
	"""
	Vista principal de liquidación. Muestra estadísticas y enlaces a sueldos y aportes.
	"""
	# Estadísticas de sueldos
	sueldos_stats = Sueldo.objects.aggregate(
		total_sueldos=Count('id'),
		total_nomina=Sum('sueldo_neto'),
		promedio=Avg('sueldo_neto')
	)

	# Estadísticas de aportes
	aportes_stats = Aporte.objects.aggregate(
		total_aportes=Count('id'),
		valor_total=Sum('valor')
	)

	# Totales por tipo de aporte
	aportes_por_tipo = Aporte.objects.values('nombre').annotate(
		total=Sum('valor')
	)

	# Organizar aportes por tipo
	ademacor_total = 0
	famecor_total = 0

	for aporte in aportes_por_tipo:
		if 'ADEMACOR' in aporte['nombre'].upper():
			ademacor_total += aporte['total'] or 0
		elif 'FAMECOR' in aporte['nombre'].upper():
			famecor_total += aporte['total'] or 0

	context = {
		'sueldos_calculados': sueldos_stats['total_sueldos'] or 0,
		'aportes_registrados': aportes_stats['total_aportes'] or 0,
		'total_bonificaciones': 0,  # Calcular si tienes bonificaciones
		'total_descuentos': 0,      # Calcular si tienes descuentos
		'total_nomina': sueldos_stats['total_nomina'] or 0,
		'promedio': sueldos_stats['promedio'] or 0,
		'ademacor_total': ademacor_total,
		'famecor_total': famecor_total,
		'valor_total_aportes': aportes_stats['valor_total'] or 0,
	}

	return render(request, 'liquidacion/main.html', context)

@method_decorator(cache_page(300), name='dispatch')
class SueldoListView(ListView):
	"""
	Vista para listar sueldos con paginación, búsqueda y filtros.
	Muestra 25 sueldos por página con estadísticas en tiempo real.
	"""
	model = Sueldo
	template_name = 'liquidacion/sueldo_list.html'
	context_object_name = 'sueldos'
	paginate_by = 25  # CONFIGURABLE: Cambia este número para mostrar más o menos sueldos por página

	def get_queryset(self):
		"""
		Filtra los sueldos según los parámetros de búsqueda en la URL.
		Optimiza las consultas con select_related para evitar N+1 queries.
		"""
		# Base queryset con relaciones precargadas para mejor performance
		queryset = Sueldo.objects.select_related(
			'afiliado',
			'tabla_salarial'
		).prefetch_related('bonificaciones').order_by('-id')

		# FILTRO 1: Búsqueda por nombre o cédula del afiliado
		search = self.request.GET.get('search', '').strip()
		if search:
			queryset = queryset.filter(
				Q(afiliado__nombre__icontains=search) |
				Q(afiliado__apellido__icontains=search) |
				Q(afiliado__cedula__icontains=search)
			)

		# FILTRO 2: Año del sueldo
		anio = self.request.GET.get('anio', '').strip()
		if anio:
			try:
				queryset = queryset.filter(anio=int(anio))
			except ValueError:
				pass  # Ignorar valores no numéricos

		# FILTRO 3: Mes del sueldo
		mes = self.request.GET.get('mes', '').strip()
		if mes:
			try:
				queryset = queryset.filter(mes=int(mes))
			except ValueError:
				pass  # Ignorar valores no numéricos

		return queryset

	def get_context_data(self, **kwargs):
		"""
		Agrega datos adicionales al contexto del template:
		- Estadísticas totales (calculadas sobre los resultados filtrados)
		- Años y meses disponibles para los filtros
		"""
		context = super().get_context_data(**kwargs)

		# Obtener el queryset filtrado (sin paginar) para calcular estadísticas
		queryset = self.get_queryset()

		# ESTADÍSTICAS: Calcular totales solo de los sueldos filtrados
		stats = queryset.aggregate(
			total_sueldos=Count('id'),
			total_nomina=Sum('sueldo_neto'),
			promedio=Avg('sueldo_neto'),
			bonificaciones=Sum('bonificaciones__monto')
		)

		context['total_sueldos'] = stats['total_sueldos'] or 0
		context['total_nomina'] = stats['total_nomina'] or 0
		context['promedio'] = stats['promedio'] or 0
		context['bonificaciones'] = stats['bonificaciones'] or 0

		# OPCIONES DE FILTROS: Años disponibles (CONFIGURABLE)
		import datetime
		current_year = datetime.datetime.now().year
		context['years_available'] = range(2020, current_year + 2)  # Del 2020 hasta el año siguiente

		# OPCIONES DE FILTROS: Meses disponibles
		context['months_available'] = [
			(1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'),
			(4, 'Abril'), (5, 'Mayo'), (6, 'Junio'),
			(7, 'Julio'), (8, 'Agosto'), (9, 'Septiembre'),
			(10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
		]

		return context


# ============================================
# MANTENER LA VISTA ANTIGUA COMENTADA (BACKUP)
# ============================================
"""
# Vista antigua antes de la paginación (BACKUP)
@cache_page(300)
def sueldo_list(request):
	sueldos = Sueldo.objects.select_related('afiliado', 'tabla_salarial').all()

	# Calcular estadísticas (incluye suma de montos de bonificaciones asociadas)
	stats = sueldos.aggregate(
		total_sueldos=Count('id'),
		total_nomina=Sum('sueldo_neto'),
		promedio=Avg('sueldo_neto'),
		bonificaciones=Sum('bonificaciones__monto')
	)

	context = {
		'sueldos': sueldos,
		'total_sueldos': stats['total_sueldos'] or 0,
		'total_nomina': stats['total_nomina'] or 0,
		'bonificaciones': stats['bonificaciones'] or 0,
	}

	return render(request, 'liquidacion/sueldo_list.html', context)
"""


# ============================================
# NUEVA VISTA BASADA EN CLASES CON PAGINACIÓN
# ============================================
@method_decorator(cache_page(300), name='dispatch')
class AporteListView(ListView):
	"""
	Vista para listar aportes con paginación, búsqueda y filtros.
	Muestra 25 aportes por página con estadísticas en tiempo real.
	"""
	model = Aporte
	template_name = 'liquidacion/aporte_list.html'
	context_object_name = 'aportes'
	paginate_by = 25  # CONFIGURABLE: Cambia este número para mostrar más o menos aportes por página

	def get_queryset(self):
		"""
		Filtra los aportes según los parámetros de búsqueda en la URL.
		Optimiza las consultas con select_related para evitar N+1 queries.
		"""
		# Base queryset con relaciones precargadas para mejor performance
		queryset = Aporte.objects.select_related(
			'sueldo',
			'sueldo__afiliado'
		).order_by('-id')  # Ordenar por ID (que es autoincremental, similar a fecha de creación)

		# FILTRO 1: Búsqueda por nombre o cédula del afiliado
		search = self.request.GET.get('search', '').strip()
		if search:
			queryset = queryset.filter(
				Q(sueldo__afiliado__nombre__icontains=search) |
				Q(sueldo__afiliado__apellido__icontains=search) |
				Q(sueldo__afiliado__cedula__icontains=search)
			)

		# FILTRO 2: Tipo de aporte (ADEMACOR, FAMECOR, OTROS)
		tipo_aporte = self.request.GET.get('tipo_aporte', '').strip()
		if tipo_aporte:
			queryset = queryset.filter(nombre=tipo_aporte)

		# FILTRO 3: Año del sueldo asociado
		anio = self.request.GET.get('anio', '').strip()
		if anio:
			try:
				queryset = queryset.filter(sueldo__anio=int(anio))
			except ValueError:
				pass  # Ignorar valores no numéricos

		# FILTRO 4: Mes del sueldo asociado
		mes = self.request.GET.get('mes', '').strip()
		if mes:
			try:
				queryset = queryset.filter(sueldo__mes=int(mes))
			except ValueError:
				pass  # Ignorar valores no numéricos

		return queryset

	def get_context_data(self, **kwargs):
		"""
		Agrega datos adicionales al contexto del template:
		- Estadísticas totales (calculadas sobre los resultados filtrados)
		- Años y meses disponibles para los filtros
		"""
		context = super().get_context_data(**kwargs)

		# Obtener el queryset filtrado (sin paginar) para calcular estadísticas
		queryset = self.get_queryset()

		# ESTADÍSTICAS: Calcular totales solo de los aportes filtrados
		stats = queryset.aggregate(
			total_aportes=Count('id'),
			valor_total=Sum('valor')
		)

		context['total_aportes'] = stats['total_aportes'] or 0
		context['valor_total'] = stats['valor_total'] or 0

		# ESTADÍSTICAS POR TIPO: Totales de ADEMACOR y FAMECOR
		aportes_por_tipo = queryset.values('nombre').annotate(
			total=Sum('valor')
		)

		ademacor_total = 0
		famecor_total = 0

		for aporte in aportes_por_tipo:
			nombre_upper = aporte['nombre'].upper()
			if 'ADEMACOR' in nombre_upper:
				ademacor_total += aporte['total'] or 0
			elif 'FAMECOR' in nombre_upper:
				famecor_total += aporte['total'] or 0

		context['ademacor_total'] = ademacor_total
		context['famecor_total'] = famecor_total

		# OPCIONES DE FILTROS: Años disponibles (CONFIGURABLE)
		import datetime
		current_year = datetime.datetime.now().year
		context['years_available'] = range(2020, current_year + 2)  # Del 2020 hasta el año siguiente

		# OPCIONES DE FILTROS: Meses disponibles
		context['months_available'] = [
			(1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'),
			(4, 'Abril'), (5, 'Mayo'), (6, 'Junio'),
			(7, 'Julio'), (8, 'Agosto'), (9, 'Septiembre'),
			(10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
		]

		return context


# ============================================
# MANTENER LA VISTA ANTIGUA COMENTADA (BACKUP)
# ============================================
"""
# Vista antigua antes de la paginación (BACKUP)
@cache_page(300)
def aporte_list(request):
	aportes = Aporte.objects.select_related('sueldo', 'sueldo__afiliado').all()

	# Calcular estadísticas
	stats = aportes.aggregate(
		total_aportes=Count('id'),
		valor_total=Sum('valor')
	)
	# Totales por tipo de aporte
	aportes_por_tipo = aportes.values('nombre').annotate(
		total=Sum('valor')
	)

	# Organizar aportes por tipo
	ademacor_total = 0
	FAMECOR_total = 0

	for aporte in aportes_por_tipo:
		if 'ADEMACOR' in aporte['nombre'].upper():
			ademacor_total += aporte['total'] or 0
		elif 'FAMECOR' in aporte['nombre'].upper():
			FAMECOR_total += aporte['total'] or 0

	context = {
		'aportes': aportes,
		'total_aportes': stats['total_aportes'] or 0,
		'valor_total': stats['valor_total'] or 0,
		'ademacor_total': ademacor_total,
		'FAMECOR_total': FAMECOR_total,
	}

	return render(request, 'liquidacion/aporte_list.html', context)
"""


@cache_page(300)
def aporte_totales(request):
	# Sumar valores por nombre de aporte
	totals = Aporte.objects.values('nombre').annotate(total=Sum('valor'))
	# Normalizar salida para ADEMACOR y FAMECOR (si no existen, suman 0)
	resumen = {'ADEMACOR': 0, 'FAMECOR': 0}
	for t in totals:
		nombre = t['nombre']
		valor = t['total'] or 0
		resumen[nombre] = valor
	return render(request, 'liquidacion/aporte_totales.html', {'resumen': resumen})

def sueldo_detail(request, pk):
	sueldo = get_object_or_404(Sueldo, pk=pk)
	from .services.calculo_aportes import calcular_aportes
	aportes = calcular_aportes(sueldo)
	return render(request, 'liquidacion/sueldo_detail.html', {'sueldo': sueldo, 'aportes': aportes})

def sueldo_create(request):
	if request.method == 'POST':
		# Aquí deberías procesar el formulario
		# ...
		return redirect('sueldo_list')
	return render(request, 'liquidacion/sueldo_form.html')

def sueldo_update(request, pk):
	sueldo = get_object_or_404(Sueldo, pk=pk)
	if request.method == 'POST':
		# Aquí deberías procesar el formulario
		# ...
		return redirect('sueldo_detail', pk=sueldo.pk)
	return render(request, 'liquidacion/sueldo_form.html', {'sueldo': sueldo})

def sueldo_delete(request, pk):
	sueldo = get_object_or_404(Sueldo, pk=pk)
	if request.method == 'POST':
		sueldo.delete()
		return redirect('sueldo_list')
	return render(request, 'liquidacion/sueldo_confirm_delete.html', {'sueldo': sueldo})

def aporte_create(request):
	if request.method == 'POST':
		# Procesar formulario
		# ...
		return redirect('aporte_list')
	return render(request, 'liquidacion/aporte_form.html')

def aporte_detail(request, pk):
	aporte = get_object_or_404(Aporte, pk=pk)
	return render(request, 'liquidacion/aporte_detail.html', {'aporte': aporte})

def aporte_update(request, pk):
	aporte = get_object_or_404(Aporte, pk=pk)
	if request.method == 'POST':
		# Procesar formulario
		# ...
		return redirect('aporte_detail', pk=aporte.pk)
	return render(request, 'liquidacion/aporte_form.html', {'aporte': aporte})

def aporte_delete(request, pk):
	aporte = get_object_or_404(Aporte, pk=pk)
	if request.method == 'POST':
		aporte.delete()
		return redirect('aporte_list')
	return render(request, 'liquidacion/aporte_confirm_delete.html', {'aporte': aporte})

class AporteBulkDeleteView(View):
    """
    Vista para eliminar múltiples aportes de manera eficiente usando transacciones.
    Soporta eliminación por lotes para manejar grandes volúmenes de datos.
    """

    @method_decorator(csrf_exempt)
    @method_decorator(require_POST)
    @method_decorator(transaction.atomic)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            aporte_ids = data.get('aporte_ids', [])

            if not aporte_ids:
                return JsonResponse(
                    {'status': 'error', 'message': 'No se proporcionaron IDs de aportes'},
                    status=400
                )

            # Eliminar en lotes para mejor rendimiento
            batch_size = 1000
            deleted_count = 0

            for i in range(0, len(aporte_ids), batch_size):
                batch = aporte_ids[i:i + batch_size]
                deleted, _ = Aporte.objects.filter(id__in=batch).delete()
                deleted_count += deleted

            return JsonResponse({
                'status': 'success',
                'message': f'Se eliminaron {deleted_count} aportes correctamente.',
                'deleted_count': deleted_count
            })

        except Exception as e:
            return JsonResponse(
                {'status': 'error', 'message': str(e)},
                status=500
            )
