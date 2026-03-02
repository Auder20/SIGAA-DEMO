"""
Servicio para calcular y mostrar los aportes de ADEMACOR y FAMICOR para cada sueldo.

Este servicio utiliza parámetros dinámicos almacenados en la base de datos
para permitir la configuración flexible de los porcentajes de aportes.

Uso:
    from liquidacion.services.calculo_aportes import calcular_aportes
    aportes = calcular_aportes(sueldo)
    print(aportes['ademacor'], aportes['famicor'])
"""

from decimal import Decimal, ROUND_HALF_UP
from ..models import ParametroLiquidacion


def calcular_aportes(sueldo):
    """
    Calcula los aportes de ADEMACOR y FAMICOR para un sueldo dado.
    
    Los porcentajes se obtienen de la tabla ParametroLiquidacion y pueden variar
    según el año del sueldo.
    
    Args:
        sueldo: Instancia del modelo Sueldo para la cual calcular los aportes
        
    Returns:
        dict: Diccionario con los valores de los aportes
    """
    # Obtener los porcentajes desde la base de datos
    anio = getattr(sueldo, 'anio', None)
    
    # Obtener porcentajes de ADEMACOR (código: APORTE_ADEMACOR)
    porcentaje_ademacor = obtener_porcentaje_aporte('APORTE_ADEMACOR', anio=anio, default=1.0)
    
    # Obtener porcentajes de FAMICOR (código: APORTE_FAMICOR)
    porcentaje_famicor = obtener_porcentaje_aporte('APORTE_FAMICOR', anio=anio, default=0.2)
    
    # Calcular los valores de los aportes con redondeo a 2 decimales
    valor_ademacor = (sueldo.sueldo_neto * porcentaje_ademacor).quantize(
        Decimal('0.01'), 
        rounding=ROUND_HALF_UP
    )
    
    valor_famicor = (sueldo.sueldo_neto * porcentaje_famicor).quantize(
        Decimal('0.01'),
        rounding=ROUND_HALF_UP
    )
    
    return {
        'ademacor': valor_ademacor,
        'famicor': valor_famicor,
        'porcentaje_ademacor': porcentaje_ademacor * 100,  # Devolver como porcentaje
        'porcentaje_famicor': porcentaje_famicor * 100,    # Devolver como porcentaje
    }


def obtener_porcentaje_aporte(codigo, anio=None, default=0):
    """
    Obtiene un porcentaje de aporte desde la base de datos.
    
    Args:
        codigo (str): Código del parámetro a buscar (ej: 'APORTE_ADEMACOR')
        anio (int, optional): Año de vigencia. Si es None, busca parámetros sin año.
        default (float, optional): Valor por defecto si no se encuentra el parámetro.
        
    Returns:
        Decimal: Porcentaje como decimal (ej: 0.01 para 1%)
    """
    valor = ParametroLiquidacion.obtener_valor(codigo, anio=anio, default=default)
    return Decimal(str(valor)) / 100  # Convertir de porcentaje a decimal