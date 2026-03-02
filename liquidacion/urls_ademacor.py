from django.urls import path
from . import views_ademacor

urlpatterns = [
    path('sueldos/', views_ademacor.sueldo_ademacor_list, name='sueldo_ademacor_list'),
    path('sueldos/<int:pk>/', views_ademacor.sueldo_ademacor_detail, name='sueldo_ademacor_detail'),
    path('sueldos/<int:pk>/recalcular/', views_ademacor.sueldo_ademacor_recalcular, name='sueldo_ademacor_recalcular'),
    path('sueldos/calcular-masivo/', views_ademacor.calcular_sueldos_ademacor_masivo, name='calcular_sueldos_ademacor_masivo'),
    path('aportes/', views_ademacor.aporte_ademacor_list, name='aporte_ademacor_list'),
    path('aportes/importar/', views_ademacor.importar_aportes_ademacor, name='importar_aportes_ademacor'),
]
