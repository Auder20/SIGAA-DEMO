#!/usr/bin/env python3
"""
Herramienta de depuración para analizar los valores exactos de un archivo de aportes
y entender por qué el sistema está clasificándolo de una manera específica.

Uso:
    python debug_aportes.py archivo_excel.xlsx
"""

import sys
import os
import pandas as pd
import numpy as np

# Agregar el path del proyecto para importar módulos
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def analizar_valores(ruta_archivo):
    """
    Analiza los valores exactos de un archivo de aportes.
    """
    print(f"🔍 Analizando archivo: {ruta_archivo}")
    print("=" * 60)
    
    try:
        # Leer el archivo
        df = pd.read_excel(ruta_archivo)
        print(f"📊 Archivo leído: {len(df)} filas × {len(df.columns)} columnas")
        print(f"   Columnas: {list(df.columns)}")
        
        # Buscar columnas con valores numéricos
        for col in df.columns:
            try:
                valores = pd.to_numeric(
                    df[col].astype(str).str.replace(r'[^\d.]', '', regex=True), 
                    errors='coerce'
                )
                valores_validos = valores.dropna()
                
                if len(valores_validos) > 10:
                    print(f"\n🎯 Columna: {col}")
                    print("-" * 40)
                    
                    # Filtrar valores que parecen aportes (entre 10k y 200k)
                    aportes = valores_validos[
                        (valores_validos >= 10000) & 
                        (valores_validos <= 200000)
                    ]
                    
                    if len(aportes) > 0:
                        print(f"   Posibles aportes: {len(aportes)} registros")
                        print(f"   Rango: ${aportes.min():,.0f} - ${aportes.max():,.0f}")
                        print(f"   Promedio: ${aportes.mean():,.0f}")
                        print(f"   Mediana: ${aportes.median():,.0f}")
                        
                        # Mostrar valores únicos y su frecuencia
                        valores_unicos = aportes.value_counts().sort_index()
                        print(f"\n   Valores únicos ({len(valores_unicos)}):")
                        
                        for valor, count in valores_unicos.head(20).items():
                            porcentaje = (count / len(aportes)) * 100
                            print(f"     ${valor:,.0f}: {count} registros ({porcentaje:.1f}%)")
                        
                        if len(valores_unicos) > 20:
                            print(f"     ... y {len(valores_unicos) - 20} valores más")
                        
                        # Análisis específico para dos grupos
                        if len(valores_unicos) <= 10:
                            print(f"\n📈 Análisis de posibles grupos:")
                            
                            # Buscar valores alrededor de 30k y 60k
                            grupo_30k = aportes[(aportes >= 25000) & (aportes <= 35000)]
                            grupo_60k = aportes[(aportes >= 55000) & (aportes <= 65000)]
                            
                            if len(grupo_30k) > 0:
                                print(f"   Grupo ~30k: {len(grupo_30k)} registros")
                                print(f"     Valores: {sorted(grupo_30k.unique())}")
                            
                            if len(grupo_60k) > 0:
                                print(f"   Grupo ~60k: {len(grupo_60k)} registros")
                                print(f"     Valores: {sorted(grupo_60k.unique())}")
                            
                            # Determinar cuál grupo es mayor
                            if len(grupo_30k) > len(grupo_60k):
                                print(f"   ✅ Mayoría: Grupo ~30k (probablemente FAMECOR)")
                            elif len(grupo_60k) > len(grupo_30k):
                                print(f"   ✅ Mayoría: Grupo ~60k (probablemente ADEMACOR)")
                            else:
                                print(f"   ⚖️ Grupos similares en tamaño")
                        
                        # Buscar patrones de texto en el DataFrame
                        ademacor_texto = df.astype(str).apply(
                            lambda x: x.str.contains('ADEMACOR', case=False, na=False).any()
                        ).any()
                        famecor_texto = df.astype(str).apply(
                            lambda x: x.str.contains('FAMECOR|FAMICOR', case=False, na=False).any()
                        ).any()
                        
                        print(f"\n🔍 Búsqueda de texto:")
                        print(f"   Contiene 'ADEMACOR': {'Sí' if ademacor_texto else 'No'}")
                        print(f"   Contiene 'FAMECOR'/'FAMICOR': {'Sí' if famecor_texto else 'No'}")
                        
                        # Recomendación - REGLA CORRECTA: el menor promedio siempre es FAMECOR
                        if len(grupo_30k) > 0 and len(grupo_60k) > 0:
                            if grupo_30k.mean() < grupo_60k.mean():
                                recomendacion = "FAMECOR"
                                print(f"   ✅ Grupo ~30k es menor: FAMECOR")
                            else:
                                recomendacion = "FAMECOR"
                                print(f"   ✅ Grupo ~60k es menor: FAMECOR")
                        elif len(grupo_30k) > 0:
                            recomendacion = "FAMECOR"
                            print(f"   ✅ Solo grupo ~30k detectado: FAMECOR")
                        elif len(grupo_60k) > 0:
                            recomendacion = "ADEMACOR"
                            print(f"   ✅ Solo grupo ~60k detectado: ADEMACOR")
                        else:
                            recomendacion = "FAMECOR" if aportes.mean() <= 30000 else "ADEMACOR"
                            print(f"   ✅ Basado en promedio general: {recomendacion}")
                        
                        print(f"\n🎯 Recomendación final: {recomendacion}")
                        
            except Exception as e:
                continue
        
    except Exception as e:
        print(f"❌ Error al analizar archivo: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """
    Función principal.
    """
    if len(sys.argv) != 2:
        print("Uso: python debug_aportes.py <archivo_excel.xlsx>")
        print("Ejemplo: python debug_aportes.py aportaciones.xlsx")
        return
    
    ruta_archivo = sys.argv[1]
    
    if not os.path.exists(ruta_archivo):
        print(f"❌ El archivo no existe: {ruta_archivo}")
        return
    
    if not ruta_archivo.lower().endswith(('.xlsx', '.xls')):
        print(f"❌ El archivo debe ser de Excel (.xlsx o .xls)")
        return
    
    analizar_valores(ruta_archivo)

if __name__ == "__main__":
    main()
