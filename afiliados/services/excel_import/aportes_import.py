#!/usr/bin/env python
"""
IMPORTADOR DE APORTES INDIVIDUALES - VERSIÓN OPTIMIZADA v3 (ULTRA RÁPIDO)

Mejoras de rendimiento implementadas:
- ✅ Detección de tipo simplificada (1 paso en lugar de 3)
- ✅ Caché de sueldos existentes (evita consultas N+1)
- ✅ Bulk upsert en lugar de consultas individuales
- ✅ Eliminada validación doble de tipo
- ✅ Procesamiento vectorizado con pandas
- ✅ Reducción de logs innecesarios
- ✅ Batch size optimizado según tamaño de datos

Resultado esperado: 50-70% más rápido
"""

# import pandas as pd  # Temporalmente comentado para migraciones
import logging
import time
from typing import Dict, Any
from decimal import Decimal, InvalidOperation, getcontext
from datetime import datetime

from django.db import connection, OperationalError, transaction, close_old_connections
from afiliados.models import Afiliado
from liquidacion.models import Sueldo, Aporte, ParametroLiquidacion

getcontext().prec = 12
logger = logging.getLogger('aportes_import')


class AporteIndividualImporter:
    """Importador ultra optimizado para aportes"""
    
    # CONFIGURABLES
    BATCH_SIZE = 1000  # Aumentado de 500
    MIN_CEDULA_LENGTH = 6
    MAX_CEDULA_LENGTH = 10
    MIN_APORTE_VALOR = 1000
    MAX_APORTE_VALOR = 500000
    
    DEFAULT_PORCENTAJES = {'ADEMACOR': Decimal('1.0'), 'FAMECOR': Decimal('0.2')}
    CODIGO_PARAM_ADEMACOR = 'APORTE_ADEMACOR'
    CODIGO_PARAM_FAMECOR = 'APORTE_FAMECOR'
    
    UMBRAL_TIPO = 30000  # Simplificado: < 30k = FAMECOR, >= 30k = ADEMACOR
    
    PATRONES_ENCABEZADO = [
        'TERCEROS', 'CARGOTIPO', 'ADEMACOR LEY', 'FONDO DE AYUDA', 
        '756', 'FAMECOR FONDO', 'LEY 60', 'LEY 715', 'SECRETARÍA DE EDUCACION',
        'Total Planta Nomina', 'CodNomina', 'Página', 'SINDICATO', 'Hoja1'
    ]
    
    _cache_porcentajes = {}
    
    def __init__(self, archivo_excel: str = None, anio: int = None, tipo_aporte: str = None, batch_size: int = None):
        if archivo_excel is None:
            raise ValueError("Se requiere la ruta al archivo Excel")
        
        self.archivo_excel = archivo_excel
        self.anio = anio or datetime.now().year
        self.tipo_aporte = tipo_aporte
        self.batch_size = batch_size or self.BATCH_SIZE
        self.cache_afiliados = {}
        self.cache_sueldos = {}  # NUEVO: Caché de sueldos
        self.porcentaje_aporte = Decimal('0')
        self.stats = {
            'registros_totales': 0, 'registros_procesados': 0, 'registros_omitidos': 0,
            'afiliados_no_encontrados': 0, 'sueldos_creados': 0,
            'aportes_creados': 0, 'aportes_actualizados': 0, 'errores': 0,
            'tiempo_total': 0, 'tipo_aporte': None
        }
        self.errors = []
        self._setup_logger()
    
    def _setup_logger(self):
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s | %(levelname)-8s | %(message)s', datefmt='%H:%M:%S')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
    
    def _cargar_cache_afiliados(self):
        """Carga afiliados Y sueldos existentes"""
        logger.info("Cargando cachés...")
        start = time.time()
        
        # Afiliados
        afiliados = Afiliado.objects.filter(activo=True).only('id', 'cedula')
        self.cache_afiliados = {str(a.cedula).strip(): a for a in afiliados}
        
        # NUEVO: Pre-cargar sueldos existentes
        afiliado_ids = [a.id for a in self.cache_afiliados.values()]
        sueldos = Sueldo.objects.filter(
            afiliado__id__in=afiliado_ids,
            anio=self.anio
        ).select_related('afiliado')
        
        self.cache_sueldos = {s.afiliado.id: s for s in sueldos}
        
        logger.info(f"✓ {len(self.cache_afiliados)} afiliados, {len(self.cache_sueldos)} sueldos ({time.time()-start:.2f}s)")
    
    def _detectar_tipo_simple(self, df: pd.DataFrame) -> str:
        """Detección RÁPIDA por mediana de valores"""
        for col in df.columns:
            try:
                valores = pd.to_numeric(
                    df[col].astype(str).str.replace(r'[^\d.]', '', regex=True),
                    errors='coerce'
                )
                valores_validos = valores[
                    (valores >= self.MIN_APORTE_VALOR) & 
                    (valores <= self.MAX_APORTE_VALOR)
                ]
                
                if len(valores_validos) > 10:
                    mediana = valores_validos.median()
                    tipo = 'FAMECOR' if mediana < self.UMBRAL_TIPO else 'ADEMACOR'
                    logger.info(f"✓ Tipo detectado: {tipo} (mediana=${mediana:,.0f})")
                    return tipo
            except:
                continue
        
        raise ValueError("No se pudo detectar el tipo de aporte")
    
    def _cargar_porcentaje(self):
        """Carga porcentaje con caché"""
        cache_key = f"{self.tipo_aporte}_{self.anio}"
        if cache_key in self._cache_porcentajes:
            self.porcentaje_aporte = self._cache_porcentajes[cache_key]
            return
        
        try:
            codigo = self.CODIGO_PARAM_ADEMACOR if self.tipo_aporte == 'ADEMACOR' else self.CODIGO_PARAM_FAMECOR
            porcentaje = ParametroLiquidacion.obtener_valor(codigo, anio=self.anio, default=None)
            self.porcentaje_aporte = Decimal(str(porcentaje)) if porcentaje else self.DEFAULT_PORCENTAJES[self.tipo_aporte]
        except:
            self.porcentaje_aporte = self.DEFAULT_PORCENTAJES[self.tipo_aporte]
        
        self._cache_porcentajes[cache_key] = self.porcentaje_aporte
    
    def _filtrar_mini_encabezados(self, df: pd.DataFrame) -> pd.DataFrame:
        """Filtrado vectorizado"""
        mask = pd.Series([False] * len(df))
        for patron in self.PATRONES_ENCABEZADO:
            mask |= df.apply(lambda row: row.astype(str).str.contains(patron, case=False, na=False).any(), axis=1)
        return df[~mask].copy()
    
    def _detectar_columnas(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detección rápida de columnas"""
        columnas = {'cedula': None, 'valor_aporte': None}
        
        # Cédula: primera columna con patrón numérico
        for col in df.columns:
            if df[col].astype(str).str.match(rf'^\d{{{self.MIN_CEDULA_LENGTH},{self.MAX_CEDULA_LENGTH}}}$').mean() >= 0.5:
                columnas['cedula'] = col
                break
        
        if not columnas['cedula']:
            raise ValueError("❌ No se detectó columna de cédula")
        
        # Valor: columna con valores numéricos en rango
        for col in df.columns:
            if col == columnas['cedula']:
                continue
            try:
                valores = pd.to_numeric(df[col].astype(str).str.replace(r'[^\d.]', '', regex=True), errors='coerce')
                validos = valores[(valores >= self.MIN_APORTE_VALOR) & (valores <= self.MAX_APORTE_VALOR)]
                if len(validos) / len(df) >= 0.5:
                    columnas['valor_aporte'] = col
                    break
            except:
                continue
        
        if not columnas['valor_aporte']:
            raise ValueError("❌ No se detectó columna de valor")
        
        return columnas
    
    def _limpiar_y_estructurar(self, df: pd.DataFrame) -> pd.DataFrame:
        """Limpieza optimizada SIN validación doble"""
        logger.info(f"Limpiando datos ({df.shape})...")
        
        df = df.astype(str).apply(lambda x: x.str.strip())
        df = self._filtrar_mini_encabezados(df)
        
        if df.empty:
            raise ValueError("❌ DataFrame vacío")
        
        # Detectar tipo si no está forzado
        if not self.tipo_aporte:
            self.tipo_aporte = self._detectar_tipo_simple(df)
            self.stats['tipo_aporte'] = self.tipo_aporte
        
        columnas = self._detectar_columnas(df)
        
        # Crear DataFrame limpio VECTORIZADO
        df_limpio = pd.DataFrame()
        df_limpio['cedula'] = df[columnas['cedula']].str.strip()
        
        # Filtrar cédulas válidas
        mask = df_limpio['cedula'].str.match(rf'^\d{{{self.MIN_CEDULA_LENGTH},{self.MAX_CEDULA_LENGTH}}}$')
        df_limpio = df_limpio[mask].copy()
        
        if df_limpio.empty:
            raise ValueError("❌ No hay cédulas válidas")
        
        # Convertir valores
        valores = pd.to_numeric(
            df.loc[df_limpio.index, columnas['valor_aporte']].str.replace(r'[^\d.]', '', regex=True),
            errors='coerce'
        )
        
        df_limpio['valor_aporte'] = valores.where(
            (valores >= self.MIN_APORTE_VALOR) & (valores <= self.MAX_APORTE_VALOR),
            pd.NA
        )
        
        df_limpio = df_limpio.dropna(subset=['valor_aporte'])
        
        # Eliminar duplicados (mantener último)
        df_limpio = df_limpio[~df_limpio['cedula'].duplicated(keep='last')]
        
        logger.info(f"✓ {len(df_limpio)} registros válidos")
        return df_limpio
    
    def _procesar_lote_bulk(self, df_lote: pd.DataFrame) -> Dict[str, int]:
        """Procesamiento ULTRA OPTIMIZADO - CREA SUELDOS SI NO EXISTEN"""
        stats = {'procesados': 0, 'omitidos': 0, 'errores': 0}
        
        # Preparar registros
        registros = []
        for _, fila in df_lote.iterrows():
            cedula = str(fila['cedula']).strip()
            afiliado = self.cache_afiliados.get(cedula)
            
            if not afiliado:
                self.stats['afiliados_no_encontrados'] += 1
                stats['omitidos'] += 1
                continue
            
            try:
                valor = Decimal(str(fila['valor_aporte']))
                if self.MIN_APORTE_VALOR <= valor <= self.MAX_APORTE_VALOR:
                    registros.append({
                        'afiliado': afiliado,
                        'valor': valor
                    })
            except:
                stats['errores'] += 1
        
        if not registros:
            return stats
        
        try:
            with transaction.atomic():
                # 1. IDENTIFICAR Y CREAR SUELDOS FALTANTES (bulk)
                sueldos_crear = []
                afiliados_sin_sueldo = []
                
                for r in registros:
                    afiliado = r['afiliado']
                    if afiliado.id not in self.cache_sueldos:
                        # Marcar para crear
                        afiliados_sin_sueldo.append(afiliado)
                        nuevo_sueldo = Sueldo(
                            afiliado=afiliado,
                            anio=self.anio,
                            sueldo_neto=Decimal('0'),
                            tabla_salarial=None
                        )
                        sueldos_crear.append(nuevo_sueldo)
                
                # Crear sueldos en bulk
                if sueldos_crear:
                    Sueldo.objects.bulk_create(sueldos_crear, batch_size=self.batch_size, ignore_conflicts=True)
                    self.stats['sueldos_creados'] += len(sueldos_crear)
                    
                    # IMPORTANTE: Recargar sueldos recién creados para obtener sus IDs
                    sueldos_nuevos = Sueldo.objects.filter(
                        afiliado__id__in=[a.id for a in afiliados_sin_sueldo],
                        anio=self.anio
                    )
                    
                    # Actualizar caché con los sueldos nuevos
                    for s in sueldos_nuevos:
                        self.cache_sueldos[s.afiliado.id] = s
                
                # 2. VERIFICAR QUE TODOS LOS REGISTROS TENGAN SUELDO
                for r in registros:
                    afiliado_id = r['afiliado'].id
                    if afiliado_id not in self.cache_sueldos:
                        logger.warning(f"⚠ Afiliado {r['afiliado'].cedula} sin sueldo después de creación")
                        stats['omitidos'] += 1
                        continue
                
                # 3. OBTENER APORTES EXISTENTES
                afiliado_ids = [r['afiliado'].id for r in registros if r['afiliado'].id in self.cache_sueldos]
                aportes_existentes = Aporte.objects.filter(
                    sueldo__afiliado__id__in=afiliado_ids,
                    nombre=self.tipo_aporte,
                    sueldo__anio=self.anio
                ).select_related('sueldo__afiliado')
                
                mapa_aportes = {a.sueldo.afiliado.id: a for a in aportes_existentes}
                
                # 4. BULK UPDATE Y CREATE APORTES
                aportes_crear = []
                aportes_actualizar = []
                
                for r in registros:
                    afiliado = r['afiliado']
                    
                    # Verificar que el sueldo existe
                    if afiliado.id not in self.cache_sueldos:
                        continue
                    
                    sueldo = self.cache_sueldos[afiliado.id]
                    aporte_existente = mapa_aportes.get(afiliado.id)
                    valor_aporte = Decimal(str(r['valor']))
                    
                    if aporte_existente:
                        # Actualizar aporte existente
                        aporte_existente.valor = valor_aporte
                        aporte_existente.porcentaje = self.porcentaje_aporte
                        aportes_actualizar.append(aporte_existente)
                    else:
                        # Crear nuevo aporte
                        aportes_crear.append(Aporte(
                            sueldo=sueldo,
                            nombre=self.tipo_aporte,
                            valor=valor_aporte,
                            porcentaje=self.porcentaje_aporte
                        ))
                
                # Guardar cambios en bulk
                if aportes_crear:
                    Aporte.objects.bulk_create(aportes_crear, batch_size=self.batch_size)
                    self.stats['aportes_creados'] += len(aportes_crear)
                
                if aportes_actualizar:
                    Aporte.objects.bulk_update(aportes_actualizar, ['valor', 'porcentaje'], batch_size=self.batch_size)
                    self.stats['aportes_actualizados'] += len(aportes_actualizar)
                
                stats['procesados'] = len(aportes_crear) + len(aportes_actualizar)
        
        except Exception as e:
            logger.error(f"❌ Error en lote: {e}")
            stats['errores'] += len(registros)
            self.errors.append(str(e))
        
        return stats
    
    def procesar_archivo(self) -> Dict[str, Any]:
        """Proceso principal optimizado"""
        inicio = time.time()
        
        logger.info("="*70)
        logger.info(f"INICIANDO IMPORTACIÓN - AÑO {self.anio}")
        logger.info("="*70)
        
        try:
            # 1. Cargar cachés
            self._cargar_cache_afiliados()
            
            # 2. Leer archivo
            logger.info(f"Leyendo: {self.archivo_excel}")
            df = pd.read_excel(self.archivo_excel, header=None, dtype=str, na_values=['', ' '], keep_default_na=False)
            
            # 3. Limpiar
            df_limpio = self._limpiar_y_estructurar(df)
            
            if df_limpio.empty:
                return {'estado': 'error', 'mensaje': 'Sin datos válidos', 'estadisticas': self.stats}
            
            # 4. Cargar porcentaje
            self._cargar_porcentaje()
            
            self.stats['registros_totales'] = len(df_limpio)
            self.stats['tipo_aporte'] = self.tipo_aporte
            
            logger.info(f"PROCESANDO {self.stats['registros_totales']} REGISTROS DE {self.tipo_aporte}")
            
            # 5. Procesar en lotes
            total_lotes = (len(df_limpio) + self.batch_size - 1) // self.batch_size
            
            for i in range(0, len(df_limpio), self.batch_size):
                lote = df_limpio.iloc[i:i + self.batch_size]
                stats_lote = self._procesar_lote_bulk(lote)
                
                self.stats['registros_procesados'] += stats_lote['procesados']
                self.stats['registros_omitidos'] += stats_lote['omitidos']
                self.stats['errores'] += stats_lote['errores']
                
                lote_num = (i // self.batch_size) + 1
                progreso = min((i + len(lote)) / self.stats['registros_totales'] * 100, 100)
                
                if lote_num % 5 == 0 or lote_num == total_lotes:  # Log cada 5 lotes
                    logger.info(f"Lote {lote_num}/{total_lotes}: {progreso:.1f}%")
            
            # 6. Finalizar
            self.stats['tiempo_total'] = time.time() - inicio
            
            logger.info("="*70)
            logger.info(f"{self.tipo_aporte} COMPLETADO")
            logger.info(f"⏱ {self.stats['tiempo_total']:.2f}s | ✓{self.stats['registros_procesados']} | ⊘{self.stats['registros_omitidos']}")
            logger.info("="*70)
            
            return {'estado': 'completado', 'estadisticas': self.stats, 'errores': self.errors if self.errors else None}
        
        except Exception as e:
            logger.error(f"❌ Error: {e}")
            self.stats['tiempo_total'] = time.time() - inicio
            return {'estado': 'error', 'mensaje': str(e), 'estadisticas': self.stats}


# ============================================================================
# FUNCIONES DE CONVENIENCIA
# ============================================================================

def importar_aporte_individual(archivo_excel: str, anio: int = None, tipo_aporte: str = None, batch_size: int = None) -> Dict[str, Any]:
    importer = AporteIndividualImporter(archivo_excel, anio, tipo_aporte, batch_size)
    return importer.procesar_archivo()

def importar_aportes_desde_excel(archivo_excel: str, anio: int = None, batch_size: int = None) -> Dict[str, Any]:
    return importar_aporte_individual(archivo_excel, anio, None, batch_size)

def importar_aportes_completos(archivo_ademacor: str, archivo_famecor: str, anio: int = None, batch_size: int = None) -> Dict[str, Any]:
    inicio = time.time()
    
    resultado_ademacor = importar_aporte_individual(archivo_ademacor, anio, 'ADEMACOR', batch_size)
    resultado_famecor = importar_aporte_individual(archivo_famecor, anio, 'FAMECOR', batch_size)
    
    return {
        'estado': 'completado',
        'ademacor': resultado_ademacor,
        'famecor': resultado_famecor,
        'tiempo_total': time.time() - inicio
    }