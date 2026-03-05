# liquidacion/urls.py
from django.urls import path, include
from . import views
from . import admin_tablas_salariales

urlpatterns = [
    path('', views.liquidacion_main, name='liquidacion_main'),
    # CAMBIO: Vista basada en clases para sueldos con paginación
    path('sueldos/', views.SueldoListView.as_view(), name='sueldo_list'),
    path('sueldos/nuevo/', views.sueldo_create, name='sueldo_create'),
    path('sueldos/<int:pk>/', views.sueldo_detail, name='sueldo_detail'),
    path('sueldos/<int:pk>/editar/', views.sueldo_update, name='sueldo_update'),
    path('sueldos/<int:pk>/eliminar/', views.sueldo_delete, name='sueldo_delete'),

    # CAMBIO: Vista basada en clases para aportes con paginación
    path('aportes/', views.AporteListView.as_view(), name='aporte_list'),
    path('aportes/nuevo/', views.aporte_create, name='aporte_create'),
    path('aportes/totales/', views.aporte_totales, name='aporte_totales'),
    path('aportes/<int:pk>/', views.aporte_detail, name='aporte_detail'),
    path('aportes/<int:pk>/editar/', views.aporte_update, name='aporte_update'),
    path('aportes/<int:pk>/eliminar/', views.aporte_delete, name='aporte_delete'),
    path('aportes/eliminar-masivo/', views.AporteBulkDeleteView.as_view(), name='aporte_bulk_delete'),

    # Tablas Salariales URLs
    path('tablas-salariales/', admin_tablas_salariales.ListaTablasSalarialesView.as_view(), name='tablasalarial_list'),
    path('tablas-salariales/crear-anual/', admin_tablas_salariales.crear_tabla_anual, name='tablasalarial_crear_anual'),
    path('tablas-salariales/editar/<int:anio>/', admin_tablas_salariales.editar_tabla_anual, name='tablasalarial_editar_anual'),
    path('tablas-salariales/eliminar/<int:anio>/', admin_tablas_salariales.EliminarTablaSalarialView.as_view(), name='tablasalarial_eliminar_anual'),
    path('tablas-salariales/editar-registro/<int:pk>/', admin_tablas_salariales.EditarTablaSalarialView.as_view(), name='tablasalarial_editar_registro'),

    # URLs para Organización Externa
    path('organizacion/', include('liquidacion.urls_organizacion')),
]
