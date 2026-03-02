"""
Backup of tablas.views before consolidation.
"""
from django.shortcuts import render, get_object_or_404, redirect
from .models import TablaSalarial, Bonificacion

def tablas_main(request):
    return render(request, 'tablas/main.html')

def tabla_list(request):
    tablas = TablaSalarial.objects.all()
    return render(request, 'tablas/tabla_list.html', {'tablas': tablas})

def tabla_detail(request, pk):
    tabla = get_object_or_404(TablaSalarial, pk=pk)
    return render(request, 'tablas/tabla_detail.html', {'tabla': tabla})

def tabla_create(request):
    if request.method == 'POST':
        return redirect('tabla_list')
    return render(request, 'tablas/tabla_form.html')

def tabla_update(request, pk):
    tabla = get_object_or_404(TablaSalarial, pk=pk)
    if request.method == 'POST':
        return redirect('tabla_detail', pk=tabla.pk)
    return render(request, 'tablas/tabla_form.html', {'tabla': tabla})

def tabla_delete(request, pk):
    tabla = get_object_or_404(TablaSalarial, pk=pk)
    if request.method == 'POST':
        tabla.delete()
        return redirect('tabla_list')
    return render(request, 'tablas/tabla_confirm_delete.html', {'tabla': tabla})

def bonificacion_list(request):
    bonificaciones = Bonificacion.objects.all()
    return render(request, 'tablas/bonificacion_list.html', {'bonificaciones': bonificaciones})

def bonificacion_detail(request, pk):
    bonificacion = get_object_or_404(Bonificacion, pk=pk)
    return render(request, 'tablas/bonificacion_detail.html', {'bonificacion': bonificacion})

def bonificacion_create(request):
    if request.method == 'POST':
        return redirect('bonificacion_list')
    return render(request, 'tablas/bonificacion_form.html')

def bonificacion_update(request, pk):
    bonificacion = get_object_or_404(Bonificacion, pk=pk)
    if request.method == 'POST':
        return redirect('bonificacion_detail', pk=bonificacion.pk)
    return render(request, 'tablas/bonificacion_form.html', {'bonificacion': bonificacion})

def bonificacion_delete(request, pk):
    bonificacion = get_object_or_404(Bonificacion, pk=pk)
    if request.method == 'POST':
        bonificacion.delete()
        return redirect('bonificacion_list')
    return render(request, 'tablas/bonificacion_confirm_delete.html', {'bonificacion': bonificacion})
