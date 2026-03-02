from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from decimal import Decimal
import re

from .models import TablaSalarial

class TablaSalarialForm(forms.ModelForm):
    """Formulario para editar un registro de la tabla salarial."""
    class Meta:
        model = TablaSalarial
        fields = ['grado', 'salario_base']
        widgets = {
            'salario_base': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
            }),
            'grado': forms.TextInput(attrs={
                'class': 'form-control',
                'readonly': True,
            }),
        }
    
    def clean_salario_base(self):
        salario_base = self.cleaned_data.get('salario_base')
        if salario_base and salario_base < 0:
            raise ValidationError(_('El salario base no puede ser negativo.'))
        return salario_base

class TablaSalarialAnualForm(forms.Form):
    """Formulario para crear una nueva tabla salarial anual."""
    anio = forms.IntegerField(
        label='Año de la nueva tabla',
        min_value=2000,
        max_value=2100,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: 2024',
        })
    )
    
    porcentaje_aumento = forms.DecimalField(
        label='Porcentaje de aumento (opcional)',
        required=False,
        min_value=0,
        max_value=100,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'placeholder': 'Ej: 5.50',
        }),
        help_text='Aplicar un aumento porcentual general a todos los salarios.'
    )
    
    def clean_anio(self):
        anio = self.cleaned_data.get('anio')
        if TablaSalarial.objects.filter(anio=anio).exists():
            raise ValidationError(_(f'Ya existe una tabla salarial para el año {anio}.'))
        return anio
    
    def clean_porcentaje_aumento(self):
        porcentaje = self.cleaned_data.get('porcentaje_aumento')
        if porcentaje is not None and porcentaje < 0:
            raise ValidationError(_('El porcentaje no puede ser negativo.'))
        return porcentaje
