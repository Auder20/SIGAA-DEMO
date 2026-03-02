from django.contrib import admin
from .models import Afiliado

@admin.register(Afiliado)
class AfiliadoAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo Afiliado.
    
    Proporciona una interfaz administrativa completa para gestionar afiliados
    con búsqueda, filtros y organización optimizada de campos.
    """
    
    # Campos mostrados en la lista principal
    list_display = [
        'cedula', 
        'nombre_completo', 
        'grado_escalafon', 
        'cargo_desempenado',
        'anos_servicio',
        'activo',
        'fecha_creacion'
    ]
    
    # Campos por los que se puede buscar
    search_fields = [
        'cedula', 
        'nombre_completo', 
        'email',
        'municipio'
    ]
    
    # Filtros laterales
    list_filter = [
        'activo',
        'grado_escalafon',
        'cargo_desempenado',
        'municipio',
        'estado_civil',
        'fecha_creacion'
    ]
    
    # Campos editables directamente en la lista
    list_editable = ['activo']
    
    # Organización de campos en el formulario de edición
    fieldsets = (
        ('Información de Identificación', {
            'fields': ('cedula', 'nombre_completo')
        }),
        ('Información Personal', {
            'fields': (
                'fecha_nacimiento', 'edad', 'estado_civil',
                'nombre_conyuge', 'nombre_hijos'
            ),
            'classes': ('collapse',)
        }),
        ('Información Geográfica y Contacto', {
            'fields': (
                'municipio', 'ciudad_de_nacimiento',
                'direccion', 'telefono', 'email'
            ),
            'classes': ('collapse',)
        }),
        ('Información Profesional', {
            'fields': (
                'grado_escalafon', 'cargo_desempenado',
                'fecha_ingreso', 'anos_servicio'
            ),
            'description': 'Información crítica para el cálculo de sueldos'
        }),
        ('Información Académica', {
            'fields': (
                'titulo_pregrado', 'titulo_posgrado',
                'estudios_posgrado', 'otros_titulos'
            ),
            'classes': ('collapse',),
            'description': 'Títulos y estudios que afectan bonificaciones por educación'
        }),
        ('Control del Sistema', {
            'fields': ('activo',),
            'classes': ('collapse',)
        })
    )
    
    # Campos de solo lectura
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    
    # Ordenamiento por defecto
    ordering = ['nombre_completo']
    
    # Número de elementos por página
    list_per_page = 25
    
    # Acciones personalizadas
    actions = ['activar_afiliados', 'desactivar_afiliados', 'calcular_sueldos']
    
    def activar_afiliados(self, request, queryset):
        """
        Acción para activar múltiples afiliados seleccionados.
        """
        updated = queryset.update(activo=True)
        self.message_user(
            request,
            f'{updated} afiliado(s) activado(s) exitosamente.'
        )
    activar_afiliados.short_description = "Activar afiliados seleccionados"
    
    def desactivar_afiliados(self, request, queryset):
        """
        Acción para desactivar múltiples afiliados seleccionados.
        """
        updated = queryset.update(activo=False)
        self.message_user(
            request,
            f'{updated} afiliado(s) desactivado(s) exitosamente.'
        )
    desactivar_afiliados.short_description = "Desactivar afiliados seleccionados"
    
    def calcular_sueldos(self, request, queryset):
        """
        Acción para calcular sueldos de los afiliados seleccionados.
        """
        calculados = 0
        errores = 0
        
        for afiliado in queryset:
            try:
                afiliado.crear_o_actualizar_sueldo()
                calculados += 1
            except Exception as e:
                errores += 1
        
        if calculados > 0:
            self.message_user(
                request,
                f'{calculados} sueldo(s) calculado(s) exitosamente.'
            )
        if errores > 0:
            self.message_user(
                request,
                f'{errores} error(es) al calcular sueldos.',
                level='ERROR'
            )
    calcular_sueldos.short_description = "Calcular sueldos de afiliados seleccionados"
