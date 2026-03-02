from django.contrib import admin
from django import forms
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import path
from django.http import HttpResponseRedirect
from django.urls import reverse
from decimal import Decimal

from .models import TablaSalarial, Bonificacion, Sueldo, Aporte, BonificacionPago, ParametroLiquidacion

@admin.register(TablaSalarial)
class TablaSalarialAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo TablaSalarial.

    Permite gestionar las tablas salariales por año y grado con
    cálculo automático de sueldos con bonificación.
    """
    list_display = ['anio', 'grado', 'salario_base', 'sueldo_con_bonificacion']
    list_filter = ['anio']
    search_fields = ['grado']
    ordering = ['anio', 'grado']
    list_per_page = 20

    fieldsets = (
        ('Información Básica', {
            'fields': ('anio', 'grado', 'salario_base')
        }),
        ('Cálculo Automático', {
            'fields': ('sueldo_con_bonificacion',),
            'classes': ('collapse',),
            'description': 'Este campo se calcula automáticamente al guardar'
        })
    )

    readonly_fields = ['sueldo_con_bonificacion']

@admin.register(Bonificacion)
class BonificacionAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo Bonificacion.

    Gestiona bonificaciones adicionales por año.
    """
    list_display = ['descripcion', 'anio', 'porcentaje']
    list_filter = ['anio']
    search_fields = ['descripcion']
    ordering = ['anio', 'descripcion']
    list_per_page = 20

@admin.register(Sueldo)
class SueldoAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo Sueldo.

    Muestra los sueldos calculados por afiliado y año con
    enlaces a la tabla salarial utilizada.
    """
    list_display = ['afiliado', 'anio', 'sueldo_neto', 'tabla_salarial']
    list_filter = ['anio', 'tabla_salarial__grado']
    search_fields = ['afiliado__nombre_completo', 'afiliado__cedula']
    ordering = ['-anio', 'afiliado__nombre_completo']
    list_per_page = 25

    fieldsets = (
        ('Información del Sueldo', {
            'fields': ('afiliado', 'anio', 'sueldo_neto')
        }),
        ('Referencia', {
            'fields': ('tabla_salarial',),
            'classes': ('collapse',)
        })
    )

    actions = ['recalcular_aportes']

    def recalcular_aportes(self, request, queryset):
        """
        Acción para recalcular aportes de los sueldos seleccionados.
        """
        recalculados = 0
        for sueldo in queryset:
            sueldo.recalculate_aportes()
            recalculados += 1

        self.message_user(
            request,
            f'Aportes recalculados para {recalculados} sueldo(s).'
        )
    recalcular_aportes.short_description = "Recalcular aportes de sueldos seleccionados"

@admin.register(Aporte)
class AporteAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo Aporte.

    Muestra los aportes calculados por sueldo.
    """
    list_display = ['sueldo', 'nombre', 'porcentaje', 'valor']
    list_filter = ['nombre', 'sueldo__anio']
    search_fields = ['sueldo__afiliado__nombre_completo', 'nombre']
    ordering = ['sueldo', 'nombre']
    list_per_page = 30

    readonly_fields = ['valor']  # El valor se calcula automáticamente

@admin.register(BonificacionPago)
class BonificacionPagoAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo BonificacionPago.

    Muestra el historial de bonificaciones aplicadas a cada sueldo.
    """
    list_display = ['sueldo', 'descripcion', 'porcentaje', 'monto', 'anio']
    list_filter = ['anio', 'descripcion']
    search_fields = ['sueldo__afiliado__nombre_completo', 'descripcion']
    ordering = ['sueldo', 'descripcion']
    list_per_page = 30

    fieldsets = (
        ('Información de la Bonificación', {
            'fields': ('sueldo', 'anio', 'descripcion')
        }),
        ('Cálculo', {
            'fields': ('porcentaje', 'monto')
        })
    )

@admin.register(ParametroLiquidacion)
class ParametroLiquidacionAdmin(admin.ModelAdmin):
    """
    Configuración del admin para el modelo ParametroLiquidacion.

    Permite gestionar los parámetros utilizados en el cálculo de sueldos.
    """
    list_display = ['codigo', 'nombre', 'tipo', 'valor_numerico', 'valor_texto', 'anio_vigencia', 'activo']
    list_filter = ['tipo', 'activo', 'anio_vigencia']
    search_fields = ['codigo', 'nombre', 'valor_texto']
    ordering = ['tipo', 'codigo']
    list_per_page = 20

    fieldsets = (
        ('Información del Parámetro', {
            'fields': ('codigo', 'nombre', 'tipo')
        }),
        ('Valores', {
            'fields': ('valor_numerico', 'valor_texto')
        }),
        ('Vigencia y Estado', {
            'fields': ('anio_vigencia', 'activo')
        }),
        ('Información de Auditoría', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        })
    )

    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
