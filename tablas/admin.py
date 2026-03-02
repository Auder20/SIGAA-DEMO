from django.contrib import admin
from .models import TablaSalarial, Bonificacion

@admin.register(TablaSalarial)
class TablaSalarialAdmin(admin.ModelAdmin):
    """
    Configuración del admin para TablaSalarial en el app 'tablas'.
    
    NOTA: Este admin gestiona un modelo que parece duplicar funcionalidad
    del modelo TablaSalarial en liquidacion. Se recomienda revisar la
    arquitectura para evitar confusión.
    """
    list_display = ['anio', 'grado', 'salario_base']
    list_filter = ['anio']
    search_fields = ['grado']
    ordering = ['anio', 'grado']
    list_per_page = 20

@admin.register(Bonificacion)
class BonificacionAdmin(admin.ModelAdmin):
    """
    Configuración del admin para Bonificacion en el app 'tablas'.
    
    NOTA: Este admin gestiona un modelo que parece duplicar funcionalidad
    del modelo Bonificacion en liquidacion. Se recomienda revisar la
    arquitectura para evitar confusión.
    """
    list_display = ['descripcion', 'anio', 'porcentaje']
    list_filter = ['anio']
    search_fields = ['descripcion']
    ordering = ['anio', 'descripcion']
    list_per_page = 20
