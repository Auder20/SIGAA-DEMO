from django.urls import path
from . import views

urlpatterns = [
    path('main/', views.reportes_main, name='reportes_main'),

    # URLs para reporte de diferencias Secretaría vs ADEMACOR
    path('diferencias-secretaria-ademacor/', views.generar_reporte_diferencias, name='generar_reporte_diferencias'),
    path('diferencias-secretaria-ademacor/excel/', views.exportar_diferencias_excel_view, name='exportar_diferencias_excel_view'),
    path('diferencias-secretaria-ademacor/pdf/', views.exportar_diferencias_pdf_view, name='exportar_diferencias_pdf_view'),

    # URLs para exportación con filtro aplicado
    path('exportar_diferencias_excel_filtrado/', views.exportar_diferencias_excel_filtrado, name='exportar_diferencias_excel_filtrado'),
    path('exportar_diferencias_pdf_filtrado/', views.exportar_diferencias_pdf_filtrado, name='exportar_diferencias_pdf_filtrado'),

    # URLs para reportes de totales de aportes
    path('aportes-totales/', views.reportes_aportes_totales_main, name='reportes_aportes_totales_main'),
    path('aportes-totales/generar/', views.generar_reporte_aportes_totales, name='generar_reporte_aportes_totales'),
    path('aportes-totales/<int:pk>/', views.detalle_reporte_aportes_totales, name='detalle_reporte_aportes_totales'),
    path('aportes-totales/<int:pk>/excel/', views.exportar_aportes_totales_excel, name='exportar_aportes_totales_excel'),
    path('aportes-totales/<int:pk>/pdf/', views.exportar_aportes_totales_pdf, name='exportar_aportes_totales_pdf'),
    path('aportes-totales/<int:pk>/recalcular/', views.recalcular_reporte_aportes_totales, name='recalcular_reporte_aportes_totales'),
    path('aportes-totales/<int:pk>/actualizar-sueldos/', views.actualizar_sueldos_desde_aportes, name='actualizar_sueldos_desde_aportes'),

    path('', views.reporte_list, name='reporte_list'),
    path('nuevo/', views.reporte_create, name='reporte_create'),
    path('<int:pk>/', views.reporte_detail, name='reporte_detail'),
    path('<int:pk>/editar/', views.reporte_update, name='reporte_update'),
    path('<int:pk>/eliminar/', views.reporte_delete, name='reporte_delete'),
]
