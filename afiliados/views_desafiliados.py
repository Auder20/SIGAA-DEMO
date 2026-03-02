"""
Vistas para la gestión de desafiliados en el sistema SIGAA.

Este módulo contiene todas las vistas relacionadas con la gestión de desafiliados,
incluyendo operaciones CRUD y visualización de datos.

Autor: Sistema SIGAA
Fecha: 2025
"""

from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.http import HttpResponse
from django.core.cache import cache
from .models import Desafiliado, Afiliado
from .services.desafiliacion_service import DesafiliacionService
import logging

# Configurar logger para esta vista
logger = logging.getLogger(__name__)

def desafiliado_list(request):
    """
    Lista y búsqueda de desafiliados con paginación.
    
    Permite buscar desafiliados por cédula, nombre o municipio
    y muestra los resultados en una tabla paginada.

    Args:
        request: HttpRequest object

    Returns:
        HttpResponse: Página de lista de desafiliados
    """
    # Obtener parámetros de búsqueda
    search_query = request.GET.get('q', '')
    
    # Filtrar desafiliados según la búsqueda
    if search_query:
        desafiliados = Desafiliado.objects.filter(
            Q(cedula__icontains=search_query) |
            Q(nombre_completo__icontains=search_query) |
            Q(municipio__icontains=search_query) |
            Q(cargo_desempenado__icontains=search_query)
        )
    else:
        desafiliados = Desafiliado.objects.all()
    
    # Ordenar por fecha de desafiliación (más recientes primero)
    desafiliados = desafiliados.order_by('-fecha_desafiliacion')
    
    # Configurar paginación
    paginator = Paginator(desafiliados, 25)  # Mostrar 25 desafiliados por página
    page = request.GET.get('page')
    
    try:
        desafiliados_paginados = paginator.page(page)
    except PageNotAnInteger:
        desafiliados_paginados = paginator.page(1)
    except EmptyPage:
        desafiliados_paginados = paginator.page(paginator.num_pages)
    
    context = {
        'desafiliados': desafiliados_paginados,
        'search_query': search_query,
        'total_desafiliados': desafiliados.count(),
    }
    
    return render(request, 'afiliados/desafiliado_list.html', context)

def desafiliado_detail(request, pk):
    """
    Vista para mostrar los detalles de un desafiliado específico.

    Muestra toda la información disponible de un desafiliado incluyendo
    datos personales, profesionales y el motivo de la desafiliación.

    Args:
        request: HttpRequest object
        pk: Primary key del desafiliado a mostrar

    Returns:
        HttpResponse: Página de detalles del desafiliado
    """
    desafiliado = get_object_or_404(Desafiliado, pk=pk)
    
    context = {
        'desafiliado': desafiliado,
    }
    
    return render(request, 'afiliados/desafiliado_detail.html', context)

def desafiliar_afiliado(request, pk):
    """
    Vista para desafiliar a un afiliado existente.
    
    Muestra un formulario para capturar el motivo de la desafiliación
    y luego procesa la desafiliación.

    Args:
        request: HttpRequest object
        pk: Primary key del afiliado a desafiliar

    Returns:
        HttpResponse: Formulario de desafiliación o redirección tras procesar
    """
    afiliado = get_object_or_404(Afiliado, pk=pk)
    
    if request.method == 'POST':
        motivo = request.POST.get('motivo_desafiliacion', '')
        
        if not motivo:
            messages.error(request, 'Debe especificar el motivo de la desafiliación.')
        else:
            try:
                # Usar el servicio de desafiliación
                desafiliado, success, message = DesafiliacionService.desafiliar_afiliado(afiliado, motivo)
                
                if success:
                    # Limpiar la caché para asegurar que la lista se actualice
                    cache.clear()
                    messages.success(request, message)
                    # Redirigir a la lista de desafiliados después de la desafiliación exitosa
                    return redirect('afiliados:desafiliado_list')
                else:
                    messages.error(request, message)
                    logger.error(f'Error al desafiliar afiliado: {message}')
            except Exception as e:
                error_msg = f'Error al desafiliar afiliado: {str(e)}'
                logger.error(error_msg, exc_info=True)
                messages.error(request, error_msg)
    
    context = {
        'afiliado': afiliado,
    }
    
    return render(request, 'afiliados/desafiliar_afiliado.html', context)

def reafiliar_desafiliado(request, pk):
    """
    Vista para reafiliar a un desafiliado existente.
    
    Muestra una página de confirmación y luego procesa la reafiliación.

    Args:
        request: HttpRequest object
        pk: Primary key del desafiliado a reafiliar

    Returns:
        HttpResponse: Página de confirmación o redirección tras procesar
    """
    desafiliado = get_object_or_404(Desafiliado, pk=pk)
    
    if request.method == 'POST':
        try:
            # Usar el servicio de reafiliación
            afiliado, success, message = DesafiliacionService.reafiliar_desafiliado(desafiliado)
            
            if success:
                # Limpiar la caché para asegurar que las listas se actualicen
                cache.clear()
                messages.success(request, message)
                return redirect('afiliado_detail', pk=afiliado.pk)
            else:
                messages.error(request, f'Error al reafiliar: {message}')
                logger.error(f'Error al reafiliar desafiliado: {message}')
                
        except Exception as e:
            error_msg = f'Error al reafiliar desafiliado: {str(e)}'
            logger.error(error_msg, exc_info=True)
            messages.error(request, error_msg)
    
    context = {
        'desafiliado': desafiliado,
    }
    
    return render(request, 'afiliados/reafiliar_desafiliado.html', context)
