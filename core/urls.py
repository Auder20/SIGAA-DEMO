from django.urls import path
from . import views

urlpatterns = [
    path('main/', views.core_main, name='core_main'),
    # Agrega aquí las rutas para los modelos definidos en core/models.py
]
