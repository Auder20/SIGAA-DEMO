from django.urls import path
from . import admin_tablas_salariales

app_name = 'liquidacion_tablas_salariales'

urlpatterns = [
    # Lista de tablas salariales
    path(
        'tablas-salariales/',
        admin_tablas_salariales.ListaTablasSalarialesView.as_view(),
        name='tablasalarial_list'
    ),
    
    # Crear nueva tabla anual
    path(
        'tablas-salariales/crear-anual/',
        admin_tablas_salariales.crear_tabla_anual,
        name='tablasalarial_crear_anual'
    ),
    
    # Editar tabla anual
    path(
        'tablas-salariales/editar/<int:anio>/',
        admin_tablas_salariales.editar_tabla_anual,
        name='tablasalarial_editar_anual'
    ),
    
    # Eliminar tabla anual (confirmación)
    path(
        'tablas-salariales/eliminar/<int:anio>/',
        admin_tablas_salariales.EliminarTablaSalarialView.as_view(),
        name='tablasalarial_eliminar_anual'
    ),
    
    # Editar registro individual (por si se necesita)
    path(
        'tablas-salariales/editar-registro/<int:pk>/',
        admin_tablas_salariales.EditarTablaSalarialView.as_view(),
        name='tablasalarial_editar_registro'
    ),
]
