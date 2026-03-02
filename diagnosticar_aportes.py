#!/usr/bin/env python3
"""
Herramienta de diagnóstico para analizar archivos de aportes y entender
qué está detectando el sistema de clasificación.

Uso:
    python diagnosticar_aportes.py archivo_excel.xlsx
"""

import sys
import os
import pandas as pd
import numpy as np

# Agregar el path del proyecto para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from afiliados.services.excel_import.aportes_import import AportesImport

def analizar_archivo(ruta_archivo):
    """
    Analiza un archivo de Excel y muestra información detallada sobre la detección.
    """
    print(f"🔍 Analizando archivo: {ruta_archivo}")
    print("=" * 60)
    
    try:
        # Leer el archivo
        df = pd.read_excel(ruta_archivo)
        print(f"📊 Archivo leído: {len(df)} filas × {len(df.columns)} columnas")
        print(f"   Columnas: {list(df.columns)}")
        
        # Crear instancia del importador
        importer = AportesImport()
        
        # Detectar columnas de valores
        columnas_numericas = []
        for col in df.columns:
            try:
                valores = pd.to_numeric(
                    df[col].astype(str).str.replace(r'[^\d.]', '', regex=True), 
                    errors='coerce'
                )
                valores_validos = valores.dropna()
                if len(valores_validos) > 5:
                    columnas_numericas.append(col)
                    print(f"   Columna numérica encontrada: {col}")
                    print(f"     Rango: ${valores_validos.min():,.0f} - ${valores_validos.max():,.0f}")
                    print(f"     Promedio: ${valores_validos.mean():,.0f}")
                    print(f"     Valores únicos: {len(valores_validos.unique())}")
            except:
                continue
        
        if not columnas_numericas:
            print("❌ No se encontraron columnas numéricas válidas")
            return
        
        # Analizar cada columna numérica
        for col in columnas_numericas:
            print(f"\n🎯 Analizando columna: {col}")
            print("-" * 40)
            
            valores = pd.to_numeric(
                df[col].astype(str).str.replace(r'[^\d.]', '', regex=True), 
                errors='coerce'
            )
            valores_validos = valores.dropna()
            
            # Filtrar valores de aporte válidos
            valores_filtrados = valores_validos[
                (valores_validos >= importer.MIN_APORTE_VALOR) & 
                (valores_validos <= importer.MAX_APORTE_VALOR)
            ]
            
            print(f"   Valores válidos: {len(valores_filtrados)}")
            
            if len(valores_filtrados) > 10:
                # Ejecutar detección mejorada
                tipo_detectado = importer._detectar_tipo_aporte_mejorado(df)
                print(f"✅ Tipo detectado: {tipo_detectado}")
                
                # Mostrar análisis detallado
                print("\n📈 Análisis de distribución:")
                valores_unicos = sorted(valores_filtrados.unique())
                print(f"   Valores únicos: {len(valores_unicos)}")
                print(f"   Primeros 10 valores: {valores_unicos[:10]}")
                
                # Contar frecuencia de valores
                frecuencia = valores_filtrados.value_counts().sort_index()
                print(f"\n📊 Frecuencia de valores:")
                for valor, count in frecuencia.head(20).items():
                    print(f"   ${valor:,.0f}: {count} registros")
                
                if len(frecuencia) > 20:
                    print(f"   ... y {len(frecuencia) - 20} valores más")
            
        print(f"\n🎯 Conclusión:")
        print(f"   El archivo debería ser clasificado como: {importer.tipo_aporte or 'No detectado'}")
        
    except Exception as e:
        print(f"❌ Error al analizar archivo: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """
    Función principal.
    """
    if len(sys.argv) != 2:
        print("Uso: python diagnosticar_aportes.py <archivo_excel.xlsx>")
        print("Ejemplo: python diagnosticar_aportes.py aportaciones.xlsx")
        return
    
    ruta_archivo = sys.argv[1]
    
    if not os.path.exists(ruta_archivo):
        print(f"❌ El archivo no existe: {ruta_archivo}")
        return
    
    if not ruta_archivo.lower().endswith(('.xlsx', '.xls')):
        print(f"❌ El archivo debe ser de Excel (.xlsx o .xls)")
        return
    
    analizar_archivo(ruta_archivo)

if __name__ == "__main__":
    main()
