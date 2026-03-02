from django.contrib import admin
from .models import Reporte

@admin.register(Reporte)
class ReporteAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo Reporte.
    
    Permite gestionar los reportes generados en el sistema con
    filtros por tipo, fecha y usuario generador.
    """
    
    list_display = [
        'tipo', 
        'fecha_generado', 
        'generado_por', 
        'get_nombre_archivo_excel',
        'get_nombre_archivo_pdf',
        'descripcion'
    ]
    
    list_filter = [
        'tipo',
        'fecha_generado',
        'generado_por'
    ]
    
    search_fields = [
        'descripcion',
        'generado_por__username',
        'archivo'
    ]
    
    ordering = ['-fecha_generado']
    
    list_per_page = 25
    
    fieldsets = (
        ('Información del Reporte', {
            'fields': ('tipo', 'descripcion')
        }),
        ('Archivos', {
            'fields': ('archivo_excel', 'archivo_pdf', 'archivo'),
            'description': 'Use archivo_excel y archivo_pdf. El campo archivo se mantiene por compatibilidad.'
        }),
        ('Información del Sistema', {
            'fields': ('generado_por', 'fecha_generado'),
            'classes': ('collapse',)
        })
    )
    
    readonly_fields = ['fecha_generado']
    
    def get_nombre_archivo_excel(self, obj):
        """Muestra el nombre del archivo Excel."""
        return obj.get_nombre_archivo_excel()
    get_nombre_archivo_excel.short_description = 'Archivo Excel'
    get_nombre_archivo_excel.admin_order_field = 'archivo_excel'

    def get_nombre_archivo_pdf(self, obj):
        """Muestra el nombre del archivo PDF."""
        return obj.get_nombre_archivo_pdf()
    get_nombre_archivo_pdf.short_description = 'Archivo PDF'
    get_nombre_archivo_pdf.admin_order_field = 'archivo_pdf'
