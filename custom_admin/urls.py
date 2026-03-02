from django.urls import path
from . import views

app_name = 'custom_admin'

urlpatterns = [
    path('', views.custom_admin_home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    # Add more admin URLs as needed
]
