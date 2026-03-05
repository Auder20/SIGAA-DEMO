
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



	# URLs para datos de organización externa
	path('organizacion/', views.datos_organizacion_list, name='datos_organizacion_list'),
	path('organizacion/<int:pk>/', views.datos_organizacion_detail, name='datos_organizacion_detail'),
	path('organizacion/<int:pk>/editar/', views.datos_organizacion_edit, name='datos_organizacion_edit'),
	path('organizacion/<int:pk>/eliminar/', views.datos_organizacion_delete, name='datos_organizacion_delete'),
	path('organizacion/exportar/', views.datos_organizacion_export, name='datos_organizacion_export'),
	path('organizacion/exportar-pdf/', views.datos_organizacion_export_pdf, name='datos_organizacion_export_pdf'),
	path('organizacion/comparacion/', views.comparacion_afiliados_organizacion, name='comparacion_afiliados_organizacion'),

	# URLs para gestión de desafiliados
	path('desafiliados/', desafiliado_list, name='desafiliado_list'),
	path('desafiliados/<int:pk>/', desafiliado_detail, name='desafiliado_detail'),
	path('<int:pk>/desafiliar/', desafiliar_afiliado, name='desafiliar_afiliado'),
	path('desafiliados/<int:pk>/reafiliar/', reafiliar_desafiliado, name='reafiliar_desafiliado'),
]
