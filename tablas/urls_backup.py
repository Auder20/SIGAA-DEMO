"""
Backup of tablas.urls
"""
from django.urls import path
from . import views

urlpatterns = [
    path('', views.tablas_main, name='tablas_main'),
    path('tablas/', views.tabla_list, name='tabla_list'),
    path('tablas/nuevo/', views.tabla_create, name='tabla_create'),
    path('tablas/<int:pk>/', views.tabla_detail, name='tabla_detail'),
    path('tablas/<int:pk>/editar/', views.tabla_update, name='tabla_update'),
    path('tablas/<int:pk>/eliminar/', views.tabla_delete, name='tabla_delete'),
    path('bonificaciones/', views.bonificacion_list, name='bonificacion_list'),
    path('bonificaciones/nuevo/', views.bonificacion_create, name='bonificacion_create'),
    path('bonificaciones/<int:pk>/', views.bonificacion_detail, name='bonificacion_detail'),
    path('bonificaciones/<int:pk>/editar/', views.bonificacion_update, name='bonificacion_update'),
    path('bonificaciones/<int:pk>/eliminar/', views.bonificacion_delete, name='bonificacion_delete'),
]
