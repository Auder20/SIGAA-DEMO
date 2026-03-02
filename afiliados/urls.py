
from django.urls import path
from . import views
from .views import importar_aportes_excel_view
from .views_desafiliados import (
    desafiliado_list, desafiliado_detail,
    desafiliar_afiliado, reafiliar_desafiliado
)

urlpatterns = [
	path('main/', views.afiliados_main, name='afiliados_main'),
	path('importar/', views.importar_excel_view, name='importar_excel'),
	path('importar-aportes/', importar_aportes_excel_view, name='importar_aportes'),
	path('exportar/', views.exportar_afiliados_excel, name='exportar_excel'),
	path('exportar-pdf/', views.exportar_afiliados_pdf, name='exportar_pdf'),

	# URLs para afiliados
	path('', views.afiliado_list, name='afiliado_list'),
	path('<int:pk>/', views.afiliado_detail, name='afiliado_detail'),
	path('nuevo/', views.afiliado_create, name='afiliado_create'),
	path('<int:pk>/editar/', views.afiliado_update, name='afiliado_update'),
	path('<int:pk>/recalcular-sueldo/', views.recalcular_sueldo, name='recalcular_sueldo'),
	path('<int:pk>/eliminar/', views.afiliado_delete, name='afiliado_delete'),



	# URLs para datos de ADEMACOR
	path('ademacor/', views.datos_ademacor_list, name='datos_ademacor_list'),
	path('ademacor/<int:pk>/', views.datos_ademacor_detail, name='datos_ademacor_detail'),
	path('ademacor/<int:pk>/editar/', views.datos_ademacor_edit, name='datos_ademacor_edit'),
	path('ademacor/<int:pk>/eliminar/', views.datos_ademacor_delete, name='datos_ademacor_delete'),
	path('ademacor/exportar/', views.datos_ademacor_export, name='datos_ademacor_export'),
	path('ademacor/exportar-pdf/', views.datos_ademacor_export_pdf, name='datos_ademacor_export_pdf'),
	path('ademacor/comparacion/', views.comparacion_afiliados_ademacor, name='comparacion_afiliados_ademacor'),

	# URLs para gestión de desafiliados
	path('desafiliados/', desafiliado_list, name='desafiliado_list'),
	path('desafiliados/<int:pk>/', desafiliado_detail, name='desafiliado_detail'),
	path('<int:pk>/desafiliar/', desafiliar_afiliado, name='desafiliar_afiliado'),
	path('desafiliados/<int:pk>/reafiliar/', reafiliar_desafiliado, name='reafiliar_desafiliado'),
]
