from django.urls import path
from . import views_organizacion

urlpatterns = [
    path('sueldos/', views_organizacion.sueldo_organizacion_list, name='sueldo_organizacion_list'),
    path('sueldos/<int:pk>/', views_organizacion.sueldo_organizacion_detail, name='sueldo_organizacion_detail'),
    path('sueldos/<int:pk>/recalcular/', views_organizacion.sueldo_organizacion_recalcular, name='sueldo_organizacion_recalcular'),
    path('sueldos/calcular-masivo/', views_organizacion.calcular_sueldos_organizacion_masivo, name='calcular_sueldos_organizacion_masivo'),
    path('aportes/', views_organizacion.aporte_organizacion_list, name='aporte_organizacion_list'),
    path('aportes/importar/', views_organizacion.importar_aportes_organizacion, name='importar_aportes_organizacion'),
]
