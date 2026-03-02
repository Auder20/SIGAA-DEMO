from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """
    Configuración del admin para el modelo User personalizado.
    
    Extiende el UserAdmin de Django para incluir el campo 'rol'
    en los formularios de creación y edición de usuarios.
    """
    
    # Agregar el campo 'rol' a los fieldsets existentes
    fieldsets = UserAdmin.fieldsets + (
        ("Información del Sistema", {
            "fields": ("rol",),
            "description": "Rol que determina los permisos del usuario en el sistema"
        }),
    )
    
    # Agregar el campo 'rol' al formulario de creación de usuarios
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("Información del Sistema", {
            "fields": ("rol",),
            "description": "Seleccione el rol apropiado para el nuevo usuario"
        }),
    )
    
    # Mostrar el rol en la lista de usuarios
    list_display = UserAdmin.list_display + ('rol',)
    
    # Permitir filtrar por rol
    list_filter = UserAdmin.list_filter + ('rol',)
    
    # Permitir buscar por rol
    search_fields = UserAdmin.search_fields + ('rol',)
