#!/usr/bin/env python3
"""
Script de prueba para verificar el nuevo sistema de detección de tipos de aportes.

Este script simula diferentes escenarios de datos para validar que el sistema
detecta correctamente múltiples grupos de aportes con diferentes valores.
"""

import pandas as pd
import numpy as np
import sys
import os

# Agregar el path del proyecto para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from afiliados.services.excel_import.aportes_import import AportesImport

def crear_datos_prueba():
    """
    Crea diferentes escenarios de datos para probar el sistema.
    """
    escenarios = {}
    
    # Escenario 1: Dos grupos claros (30k y 60k)
    datos1 = {
        'cedula': [1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008],
        'valor': [30000, 31000, 29500, 30500, 60000, 59000, 61000, 60500]
    }
    escenarios['dos_grupos'] = pd.DataFrame(datos1)
    
    # Escenario 2: Un solo grupo (solo ADEMACOR)
    datos2 = {
        'cedula': [2001, 2002, 2003, 2004],
        'valor': [58000, 59000, 60000, 61000]
    }
    escenarios['solo_ademacor'] = pd.DataFrame(datos2)
    
    # Escenario 3: Un solo grupo (solo FAMECOR)
    datos3 = {
        'cedula': [3001, 3002, 3003, 3004],
        'valor': [28000, 29000, 30000, 31000]
    }
    escenarios['solo_famecor'] = pd.DataFrame(datos3)
    
    # Escenario 4: Tres grupos (más complejo)
    datos4 = {
        'cedula': list(range(4001, 4013)),
        'valor': [20000, 21000, 22000,  # Grupo bajo (FAMECOR)
                  45000, 46000, 47000,  # Grupo medio (ADEMACOR)
                  80000, 81000, 82000,  # Grupo alto (ADEMACOR especial)
                  25000, 26000, 27000]  # Grupo bajo extendido
    }
    escenarios['tres_grupos'] = pd.DataFrame(datos4)
    
    return escenarios

def probar_deteccion():
    """
    Ejecuta pruebas de detección sobre diferentes escenarios.
    """
    print("🧪 Iniciando pruebas de detección de aportes...")
    print("=" * 60)
    
    escenarios = crear_datos_prueba()
    
    for nombre, df in escenarios.items():
        print(f"\n📊 Probando escenario: {nombre}")
        print(f"   Datos: {len(df)} registros")
        print(f"   Valores: ${df['valor'].min():,.0f} - ${df['valor'].max():,.0f}")
        print(f"   Promedio: ${df['valor'].mean():,.0f}")
        
        # Crear instancia del importador (simulada)
        try:
            importador = AportesImport.__new__(AportesImport)
            importador.UMBRAL_SEPARACION = 20000
            importador.UMBRAL_ALTO = 30000
            
            # Probar análisis de distribución
            tipo_detectado = importador._analizar_distribucion_valores(df['valor'])
            print(f"   ✅ Tipo detectado: {tipo_detectado}")
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    print("\n" + "=" * 60)
    print("🎯 Pruebas completadas")

if __name__ == "__main__":
    probar_deteccion()
