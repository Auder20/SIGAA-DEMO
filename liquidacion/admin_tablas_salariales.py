from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.generic import ListView, UpdateView, CreateView, DeleteView
from django.urls import reverse_lazy
from django.db import transaction
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.forms import modelformset_factory

from .models import TablaSalarial
from .forms import TablaSalarialForm, TablaSalarialAnualForm

class StaffRequiredMixin:
    """Mixin para verificar que el usuario sea miembro del staff."""
    @method_decorator(staff_member_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

class ListaTablasSalarialesView(LoginRequiredMixin, StaffRequiredMixin, ListView):
    """Vista para listar todas las tablas salariales agrupadas por año."""
    model = TablaSalarial
    template_name = 'admin/liquidacion/tablasalarial_list.html'
    context_object_name = 'tablas_por_anio'
    
    def get_queryset(self):
        # Agrupar por año
        return TablaSalarial.objects.values('anio').order_by('-anio').distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Obtener todos los años únicos
        anios = self.get_queryset()
        
        # Para cada año, obtener los registros correspondientes
        tablas_por_anio = []
        for anio in anios:
            tablas = TablaSalarial.objects.filter(anio=anio['anio']).order_by(
                'grado'
            )
            if tablas.exists():
                tablas_por_anio.append({
                    'anio': anio['anio'],
                    'tablas': tablas,
                    'es_ultimo_anio': anio['anio'] == TablaSalarial.objects.latest('anio').anio
                })
        
        context['tablas_por_anio'] = tablas_por_anio
        return context

@staff_member_required
def crear_tabla_anual(request):
    """Vista para crear una nueva tabla salarial anual basada en el año anterior."""
    if request.method == 'POST':
        form = TablaSalarialAnualForm(request.POST)
        if form.is_valid():
            anio = form.cleaned_data['anio']
            porcentaje_aumento = form.cleaned_data.get('porcentaje_aumento', 0)
            
            # Obtener la tabla del año anterior
            anio_anterior = anio - 1
            tablas_anio_anterior = TablaSalarial.objects.filter(anio=anio_anterior)
            
            if not tablas_anio_anterior.exists():
                messages.error(
                    request, 
                    f'No existe una tabla salarial para el año {anio_anterior}.'
                )
                return redirect('liquidacion:tablasalarial_list')
            
            # Crear nuevas entradas basadas en el año anterior
            try:
                with transaction.atomic():
                    for tabla_anterior in tablas_anio_anterior:
                        nuevo_salario = tabla_anterior.salario_base
                        
                        # Aplicar aumento porcentual si se especificó
                        if porcentaje_aumento and porcentaje_aumento > 0:
                            aumento = (tabla_anterior.salario_base * Decimal(porcentaje_aumento)) / 100
                            nuevo_salario += aumento
                        
                        TablaSalarial.objects.create(
                            anio=anio,
                            grado=tabla_anterior.grado,
                            salario_base=nuevo_salario
                        )
                
                messages.success(
                    request, 
                    f'Se creó exitosamente la tabla salarial para el año {anio}.'
                )
                return redirect('liquidacion:tablasalarial_list')
                
            except Exception as e:
                messages.error(
                    request, 
                    f'Error al crear la tabla salarial: {str(e)}'
                )
    else:
        form = TablaSalarialAnualForm()
    
    return render(request, 'admin/liquidacion/tablasalarial_crear_anual.html', {
        'form': form,
        'title': 'Crear nueva tabla salarial anual',
    })

@staff_member_required
def editar_tabla_anual(request, anio):
    """Vista para editar todos los registros de una tabla salarial de un año específico."""
    TablaSalarialFormSet = modelformset_factory(
        TablaSalarial, 
        form=TablaSalarialForm,
        extra=0
    )
    
    if request.method == 'POST':
        formset = TablaSalarialFormSet(
            request.POST,
            queryset=TablaSalarial.objects.filter(anio=anio).order_by('grado')
        )
        
        if formset.is_valid():
            formset.save()
            messages.success(request, 'Los cambios se han guardado correctamente.')
            return redirect('liquidacion:tablasalarial_list')
    else:
        formset = TablaSalarialFormSet(
            queryset=TablaSalarial.objects.filter(anio=anio).order_by('grado')
        )
    
    return render(request, 'admin/liquidacion/tablasalarial_editar_anual.html', {
        'formset': formset,
        'anio': anio,
        'title': f'Editar tabla salarial {anio}',
    })

class EditarTablaSalarialView(LoginRequiredMixin, StaffRequiredMixin, UpdateView):
    """Vista para editar un registro individual de la tabla salarial."""
    model = TablaSalarial
    form_class = TablaSalarialForm
    template_name = 'admin/liquidacion/tablasalarial_form.html'
    success_url = reverse_lazy('liquidacion:tablasalarial_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Editar registro de grado {self.object.grado} ({self.object.anio})'
        return context

class EliminarTablaSalarialView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    """Vista para eliminar un registro individual de la tabla salarial."""
    model = TablaSalarial
    template_name = 'admin/liquidacion/tablasalarial_confirm_delete.html'
    success_url = reverse_lazy('liquidacion:tablasalarial_list')
    
    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(request, 'El registro ha sido eliminado correctamente.')
        return response
