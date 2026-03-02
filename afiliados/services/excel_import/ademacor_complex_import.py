#!/usr/bin/env python
"""
IMPORTADOR ULTRA-OPTIMIZADO ESPECÍFICO PARA ADEMACOR
Versión completamente optimizada que maneja archivos con y sin encabezados correctamente
Adaptado específicamente para el modelo DatosAdemacor
"""

import pandas as pd
import logging
import time
from typing import Dict, Any, List, Set
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection, OperationalError, transaction
import os

# Configurar logging básico
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('ademacor_ultra_optimized')

class AdemacorUltraOptimized:
    """
    Importador ultra-optimizado específico para datos de ADEMACOR.
    Maneja automáticamente archivos con y sin encabezados.
    Adaptado para trabajar con el modelo DatosAdemacor.
    """

    def __init__(self, batch_size: int = 5000):
        self.logger = logger
        self.batch_size = batch_size
        self.processed_rows = 0
        self.errors: List[Dict[str, Any]] = []
        self.stats = {
            'created': 0,
            'updated': 0,
            'ignored': 0,
            'errors': 0
        }
        self.logger.info("🚀 AdemacorUltraOptimized inicializado correctamente")

    def ensure_connection(self) -> bool:
        """Asegura que la conexión a BD esté activa"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            return True
        except OperationalError:
            try:
                connection.close()
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                return True
            except Exception as e:
                self.logger.error(f"Error de conexión crítico: {e}")
                return False

    def safe_db_operation(self, operation_func, max_retries: int = 3) -> Any:
        """Ejecuta operación de BD con reintentos"""
        for attempt in range(max_retries):
            try:
                if not self.ensure_connection():
                    time.sleep(1)
                    continue
                return operation_func()
            except OperationalError as e:
                if "Lock wait timeout exceeded" in str(e):
                    self.logger.warning(f"Bloqueo detectado (intento {attempt + 1})")
                    time.sleep(2)
                elif "Server has gone away" in str(e):
                    connection.close()
                    time.sleep(1)
                else:
                    if attempt == max_retries - 1:
                        raise
        return None

    def detect_headers(self, df: pd.DataFrame) -> bool:
        """Detecta si el DataFrame tiene encabezados"""
        if df.empty or len(df) < 2:
            return False

        first_row = df.iloc[0]
        header_count = 0

        for col_value in first_row:
            if pd.isna(col_value):
                continue
            col_str = str(col_value).strip().lower()
            if (len(col_str) > 2 and
                not col_str.isdigit() and
                any(word in col_str for word in ['cedula', 'nombre', 'municipio', 'cargo'])):
                header_count += 1

        return header_count >= (len(first_row) * 0.5)

    def process_dataframe_bulk(self, df: pd.DataFrame, model_class, has_headers: bool) -> Dict[str, Any]:
        """
        Procesa DataFrame completo usando operaciones bulk.
        Esta es la clave de la optimización.
        """
        self.logger.info(f"📊 Procesando {len(df)} filas con operaciones bulk...")

        # Preparar DataFrame
        if has_headers:
            column_mapping = self._create_column_mapping(df.columns)
            df = df.rename(columns=column_mapping)
        else:
            positions = self._detect_column_positions(df)
            # Crear nuevo DataFrame con columnas correctas
            data = []
            for _, row in df.iterrows():
                row_dict = {}
                for col_name, position in positions.items():
                    if position >= 0 and position < len(row):
                        row_dict[col_name] = row.iloc[position]
                    else:
                        row_dict[col_name] = None
                data.append(row_dict)
            df = pd.DataFrame(data)

        # Limpiar y validar datos
        df['cedula'] = df['cedula'].astype(str).str.strip()
        df['nombre_completo'] = df['nombre_completo'].fillna('').astype(str).str.strip()
        df['municipio'] = df['municipio'].fillna('').astype(str).str.strip()

        # Filtrar cédulas inválidas
        valid_df = df[df['cedula'].str.len() >= 5].copy()
        invalid_count = len(df) - len(valid_df)
        if invalid_count > 0:
            self.logger.warning(f"⚠️ {invalid_count} registros con cédulas inválidas fueron descartados")
            self.stats['errors'] += invalid_count

        if valid_df.empty:
            return {'rows_processed': 0}

        # OPTIMIZACIÓN CLAVE: Cargar TODOS los registros existentes en memoria de una vez
        self.logger.info("🔍 Cargando registros existentes en memoria...")
        existing_cedulas = set(valid_df['cedula'].unique())

        existing_records = model_class.objects.filter(
            cedula__in=existing_cedulas
        ).values('cedula', 'nombre_completo', 'municipio', 'id')

        # Crear diccionario para búsqueda O(1)
        existing_dict = {rec['cedula']: rec for rec in existing_records}
        self.logger.info(f"✅ Cargados {len(existing_dict)} registros existentes")

        # Preparar listas para bulk operations
        to_create = []
        to_update = []
        cedulas_procesadas: Set[str] = set()

        # Procesar cada registro
        for _, row in valid_df.iterrows():
            cedula = row['cedula']

            # Evitar duplicados en el mismo archivo
            if cedula in cedulas_procesadas:
                self.stats['ignored'] += 1
                continue

            cedulas_procesadas.add(cedula)
            nombre = row['nombre_completo']
            municipio = row['municipio']

            if cedula in existing_dict:
                # Registro existe - verificar si necesita actualización
                existing = existing_dict[cedula]
                nombre_actual = existing['nombre_completo'] or ''
                municipio_actual = existing['municipio'] or ''

                if nombre_actual != nombre or municipio_actual != municipio:
                    # Hay cambios - preparar para actualización
                    obj = model_class(
                        id=existing['id'],
                        cedula=cedula,
                        nombre_completo=nombre,
                        municipio=municipio
                    )
                    to_update.append(obj)
                else:
                    # Información idéntica
                    self.stats['ignored'] += 1
            else:
                # Nuevo registro
                obj = model_class(
                    cedula=cedula,
                    nombre_completo=nombre,
                    municipio=municipio
                )
                to_create.append(obj)

        # Ejecutar operaciones bulk en transacción
        with transaction.atomic():
            # Bulk create
            if to_create:
                self.logger.info(f"➕ Creando {len(to_create)} nuevos registros...")
                model_class.objects.bulk_create(to_create, batch_size=self.batch_size)
                self.stats['created'] += len(to_create)

            # Bulk update
            if to_update:
                self.logger.info(f"📝 Actualizando {len(to_update)} registros...")
                model_class.objects.bulk_update(
                    to_update,
                    ['nombre_completo', 'municipio'],
                    batch_size=self.batch_size
                )
                self.stats['updated'] += len(to_update)

        return {'rows_processed': len(cedulas_procesadas)}

    def _create_column_mapping(self, columns) -> Dict[str, str]:
        """
        Crea un mapeo inteligente de nombres de columnas basado en patrones
        Específico para datos de ADEMACOR
        """
        mapping = {}

        # Patrones para cada tipo de columna
        cedula_patterns = ['cedula', 'cédula', 'documento', 'doc', 'dni', 'id_number', 'numero_documento']
        nombre_patterns = ['nombre', 'name', 'full_name', 'nombre_completo', 'apellido', 'apellidos']
        municipio_patterns = ['municipio', 'city', 'ciudad', 'town', 'localidad', 'location']

        for i, col in enumerate(columns):
            col_lower = str(col).strip().lower()

            # Buscar patrón de cédula
            if any(pattern in col_lower for pattern in cedula_patterns):
                mapping[col] = 'cedula'

            # Buscar patrón de nombre
            elif any(pattern in col_lower for pattern in nombre_patterns):
                mapping[col] = 'nombre_completo'

            # Buscar patrón de municipio
            elif any(pattern in col_lower for pattern in municipio_patterns):
                mapping[col] = 'municipio'

            # Si no coincide con ningún patrón, ignorar la columna
            else:
                self.logger.debug(f"⚠️ Columna '{col}' no reconocida - será ignorada")

        self.logger.info(f"🔍 Mapeo de columnas creado: {mapping}")
        return mapping

    def _detect_column_positions(self, df: pd.DataFrame) -> Dict[str, int]:
        """
        Detecta automáticamente las posiciones de las columnas importantes
        analizando patrones típicos de cada tipo de dato
        Específicamente adaptado para datos de ADEMACOR
        """
        positions = {
            'cedula': -1,
            'nombre_completo': -1,
            'municipio': -1
        }

        if df.empty or len(df.columns) == 0:
            self.logger.warning("⚠️ DataFrame vacío o sin columnas")
            return positions

        self.logger.info(f"🔍 Analizando {len(df.columns)} columnas para detectar patrones...")

        # Si hay pocas columnas, asumir orden estándar
        if len(df.columns) <= 3:
            for i, col_name in enumerate(['cedula', 'nombre_completo', 'municipio']):
                if i < len(df.columns):
                    positions[col_name] = i
            self.logger.info(f"📋 Pocas columnas detectadas, usando orden estándar: {positions}")
            return positions

        # Para más columnas, detectar automáticamente usando patrones mejorados
        sample_rows = df.head(min(15, len(df)))
        self.logger.info(f"📊 Analizando muestra de {len(sample_rows)} filas para detectar patrones")

        # Detectar columna de cédula (números largos) - MEJORADO
        cedula_scores = {}
        for i in range(len(df.columns)):
            score = 0
            valid_samples = 0
            for _, row in sample_rows.iterrows():
                if i < len(row) and pd.notna(row.iloc[i]):
                    val = str(row.iloc[i]).strip()
                    # Mejorar detección de cédulas
                    if len(val) >= 7 and val.isdigit():
                        score += 2  # Mayor peso para números largos
                        valid_samples += 1
                    elif len(val) >= 5 and val.replace('-', '').replace('.', '').replace(' ', '').isdigit():
                        score += 1.5
                        valid_samples += 1
                    elif len(val) >= 8 and val.replace('-', '').isdigit():
                        score += 1.8
                        valid_samples += 1

            if valid_samples > 0:
                cedula_scores[i] = score / valid_samples

        if cedula_scores:
            best_col = max(cedula_scores, key=cedula_scores.get)
            positions['cedula'] = best_col
            self.logger.info(f"✅ Columna CÉDULA detectada en posición {best_col} (score: {cedula_scores[best_col]:.2f})")

        # Detectar columna de nombre (texto largo con espacios y mayúsculas) - MEJORADO
        nombre_scores = {}
        for i in range(len(df.columns)):
            if i == positions['cedula']:  # No considerar la columna de cédula
                continue

            score = 0
            valid_samples = 0
            for _, row in sample_rows.iterrows():
                if i < len(row) and pd.notna(row.iloc[i]):
                    val = str(row.iloc[i]).strip()
                    # Mejorar detección de nombres
                    words = val.split()
                    if len(val) > 10 and len(words) >= 2:
                        # Verificar si hay palabras con mayúsculas
                        has_upper = any(word[0].isupper() for word in words if len(word) > 2)
                        if has_upper:
                            score += 2
                            valid_samples += 1
                        else:
                            score += 1
                            valid_samples += 1
                    elif len(val) > 5 and ' ' in val:
                        score += 0.8
                        valid_samples += 1

            if valid_samples > 0:
                nombre_scores[i] = score / valid_samples

        if nombre_scores:
            best_col = max(nombre_scores, key=nombre_scores.get)
            positions['nombre_completo'] = best_col
            self.logger.info(f"✅ Columna NOMBRE detectada en posición {best_col} (score: {nombre_scores[best_col]:.2f})")

        # Detectar columna de municipio (texto con mayúsculas, posiblemente abreviado) - MEJORADO
        municipio_scores = {}
        for i in range(len(df.columns)):
            if i in [positions['cedula'], positions['nombre_completo']]:  # No considerar columnas ya asignadas
                continue

            score = 0
            valid_samples = 0
            for _, row in sample_rows.iterrows():
                if i < len(row) and pd.notna(row.iloc[i]):
                    val = str(row.iloc[i]).strip().upper()
                    # Mejorar detección de municipios
                    if len(val) >= 3 and val.isalpha():
                        score += 2
                        valid_samples += 1
                    elif len(val) >= 2 and all(c.isalpha() or c in [' '] for c in val):
                        score += 1
                        valid_samples += 1
                    elif len(val) >= 4 and val.replace(' ', '').isalpha():
                        score += 1.5
                        valid_samples += 1

            if valid_samples > 0:
                municipio_scores[i] = score / valid_samples

        if municipio_scores:
            best_col = max(municipio_scores, key=municipio_scores.get)
            positions['municipio'] = best_col
            self.logger.info(f"✅ Columna MUNICIPIO detectada en posición {best_col} (score: {municipio_scores[best_col]:.2f})")

        self.logger.info(f"🔍 Columnas detectadas automáticamente: {positions}")
        return positions

    def import_ademacor_excel(self, excel_file, model_class) -> Dict[str, Any]:
        """Importa Excel manejando encabezados automáticamente para ADEMACOR"""
        self.logger.info("=" * 80)
        self.logger.info("🚀 INICIANDO IMPORTACIÓN ULTRA-OPTIMIZADA DE ADEMACOR")
        self.logger.info("=" * 80)

        start_time = time.time()

        try:
            # Verificar que el archivo existe y es válido
            self.logger.info(f"📁 Archivo recibido: {type(excel_file)}")

            if hasattr(excel_file, 'name'):
                self.logger.info(f"📄 Nombre del archivo: {excel_file.name}")

            # Leer todas las hojas con dtype específico para columnas clave
            self.logger.info("📖 Leyendo archivo Excel...")
            df_dict = pd.read_excel(excel_file, sheet_name=None, dtype={
                'cedula': str,
                'cédula': str,  # Variaciones con tilde
                'documento': str,
                'id': str,
                'nombre_completo': str,
                'municipio': str
            })

            # Función para normalizar cédulas específicamente
            def normalize_cedula(value):
                """Normaliza un valor de cédula removiendo ceros extra, .0 y espacios"""
                if pd.isna(value):
                    return ''
                val_str = str(value).strip()
                # Remover .0 y ceros extra del final si es numérico
                if val_str.replace('.', '').replace('-', '').isdigit():
                    # Convertir a float para remover decimales, luego a int si no hay decimales reales
                    try:
                        num = float(val_str)
                        if num.is_integer():
                            return str(int(num))  # Remueve .0 y ceros innecesarios
                        else:
                            return str(num)
                    except ValueError:
                        return val_str
                return val_str

            for sheet_name, df in df_dict.items():
                if not df.empty:
                    # Normalizar solo la columna de cédulas (buscar variaciones)
                    for col in df.columns:
                        if 'cedula' in str(col).lower():
                            df[col] = df[col].apply(normalize_cedula)
            self.logger.info(f"✅ {len(df_dict)} hoja(s) encontrada(s)")

            total_rows = sum(len(df) for df in df_dict.values())
            self.logger.info(f"📊 Total de filas: {total_rows:,}")

            # Procesar cada hoja
            for sheet_name, df in df_dict.items():
                if df.empty:
                    continue

                self.logger.info(f"\n{'='*60}")
                self.logger.info(f"📋 Hoja: {sheet_name} ({len(df):,} filas)")
                self.logger.info(f"{'='*60}")

                sheet_start = time.time()
                has_headers = self.detect_headers(df)
                self.logger.info(f"🔍 Encabezados: {'SÍ' if has_headers else 'NO'}")

                # Procesar hoja completa con bulk operations
                self.process_dataframe_bulk(df, model_class, has_headers)

                sheet_duration = time.time() - sheet_start
                rows_per_sec = len(df) / sheet_duration if sheet_duration > 0 else 0
                self.logger.info(f"⏱️ Completado en {sheet_duration:.2f}s ({rows_per_sec:.0f} filas/seg)")

            # Resultados finales
            duration = time.time() - start_time
            total_processed = self.stats['created'] + self.stats['updated'] + self.stats['ignored']
            rows_per_sec = total_processed / duration if duration > 0 else 0

            self.logger.info("\n" + "=" * 80)
            self.logger.info("📊 RESULTADOS FINALES")
            self.logger.info("=" * 80)
            self.logger.info(f"✅ Registros creados: {self.stats['created']:,}")
            self.logger.info(f"📝 Registros actualizados: {self.stats['updated']:,}")
            self.logger.info(f"🔄 Registros ignorados: {self.stats['ignored']:,}")
            self.logger.info(f"❌ Errores: {self.stats['errors']:,}")
            self.logger.info(f"⏱️ Tiempo total: {duration:.2f} segundos ({duration/60:.1f} minutos)")
            self.logger.info(f"🚀 Velocidad: {rows_per_sec:.0f} filas/segundo")
            self.logger.info("=" * 80)

            # Estimación de mejora
            old_time_hours = 5
            old_time_seconds = old_time_hours * 3600
            improvement = ((old_time_seconds - duration) / old_time_seconds) * 100
            self.logger.info(f"📈 Mejora de rendimiento: {improvement:.1f}% más rápido")
            self.logger.info(f"⏰ Tiempo ahorrado: {(old_time_hours - duration/3600):.1f} horas")

            return {
                'success': True,
                'rows_processed': total_processed,
                'total_rows': total_rows,
                'created': self.stats['created'],
                'updated': self.stats['updated'],
                'ignored': self.stats['ignored'],
                'errors': self.stats['errors'],
                'duration': duration,
                'rows_per_second': rows_per_sec
            }

        except Exception as e:
            error_msg = f"Error crítico durante la importación: {str(e)}"
            self.logger.error(f"💥 {error_msg}")
            import traceback
            traceback.print_exc()

            return {
                'success': False,
                'rows_processed': 0,
                'total_rows': 0,
                'errors': [{'row': 0, 'error': error_msg}],
                'duration': time.time() - start_time
            }


def importar_ademacor_desde_excel(excel_file) -> Dict[str, Any]:
    """
    Función principal para importar datos de ADEMACOR desde Excel.

    Usa el importador ultra-optimizado que detecta automáticamente si hay encabezados
    y procesa múltiples hojas con operaciones bulk.

    Args:
        excel_file: Archivo Excel a procesar

    Returns:
        dict: Resumen de la importación con estadísticas
    """
    from afiliados.models import DatosAdemacor
    importer = AdemacorUltraOptimized(batch_size=5000)
    return importer.import_ademacor_excel(excel_file, DatosAdemacor)
