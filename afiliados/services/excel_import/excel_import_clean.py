#!/usr/bin/env python
"""
NUEVO IMPORTADOR DE EXCEL COMPLETAMENTE LIMPIO Y FUNCIONAL
Versión mejorada que maneja archivos con y sin encabezados correctamente
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
logger = logging.getLogger('excel_import_clean')

class ExcelImportClean:
    """
    Importador de Excel completamente nuevo, limpio y funcional.
    Maneja automáticamente archivos con y sin encabezados.
    """

    def __init__(self, model_class, batch_size: int = 1000):
        """Inicializa el importador con configuración optimizada
        
        Args:
            model_class: Clase del modelo de Django a utilizar (ej: Afiliado, DatosAdemacor, etc.)
            batch_size: Tamaño del lote para operaciones masivas
        """
        self.model_class = model_class
        self.batch_size = batch_size
        self.processed_rows = 0
        self.errors = []
        self.stats = {
            'created': 0,
            'updated': 0,
            'ignored': 0,
            'errors': 0
        }
        self.logger = logging.getLogger('excel_import_clean')
        self.logger.setLevel(logging.INFO)
        
        # Configurar formato del logger si no está configurado
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            
        # Asegurar que tenemos una conexión a la base de datos
        self._ensure_connection()
    
    def _ensure_connection(self):
        """Asegura que la conexión a la base de datos esté activa"""
        from django.db import connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception:
            connection.close()
        except OperationalError:
            try:
                connection.close()
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
            except Exception:
                self.logger.error("Error de conexión crítico")
                return False
        return True

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

    def process_row_safely(self, row_data: Dict[str, Any], row_number: int) -> bool:
        """Procesa una fila individual"""
        try:
            cedula = str(row_data.get('cedula', '')).strip()
            if not cedula or len(cedula) < 5:
                self.errors.append({
                    'row': row_number,
                    'error': f'Cédula inválida: {cedula}',
                    'data': row_data
                })
                return False

            def create_or_update():
                from afiliados.models import Afiliado
                afiliado, created = Afiliado.objects.get_or_create(
                    cedula=cedula,
                    defaults={
                        'nombre_completo': str(row_data.get('nombre_completo', '')).strip(),
                        'municipio': str(row_data.get('municipio', '')).strip(),
                        'activo': True
                    }
                )
                if not created:
                    # Verificar si la información es exactamente la misma
                    nombre_actual = afiliado.nombre_completo or ''
                    nombre_nuevo = str(row_data.get('nombre_completo', '')).strip()

                    municipio_actual = afiliado.municipio or ''
                    municipio_nuevo = str(row_data.get('municipio', '')).strip()

                    # Si la información es idéntica, no hacer cambios
                    if (nombre_actual == nombre_nuevo and
                        municipio_actual == municipio_nuevo):
                        self.logger.debug(f"🔄 Fila {row_number}: {cedula} - INFORMACIÓN IDÉNTICA (IGNORADO)")
                        return afiliado, 'ignored'  # Devolver 'ignored' para indicar que se ignoró

                    # Si hay cambios, actualizar
                    updated = False
                    if nombre_actual != nombre_nuevo:
                        afiliado.nombre_completo = nombre_nuevo
                        updated = True
                        self.logger.debug(f"📝 Fila {row_number}: {cedula} - NOMBRE ACTUALIZADO: '{nombre_actual}' → '{nombre_nuevo}'")

                    if municipio_actual != municipio_nuevo:
                        afiliado.municipio = municipio_nuevo
                        updated = True
                        self.logger.debug(f"📍 Fila {row_number}: {cedula} - MUNICIPIO ACTUALIZADO: '{municipio_actual}' → '{municipio_nuevo}'")

                    if updated:
                        afiliado.save()
                        self.logger.debug(f"💾 Fila {row_number}: {cedula} - REGISTRO ACTUALIZADO")

                return afiliado, created

            afiliado, result = self.safe_db_operation(create_or_update)
            if afiliado:
                if result == 'ignored':
                    # Contar como procesado pero no actualizar estadísticas de cambios
                    self.stats['ignored'] += 1
                    return True
                elif result:  # created es True
                    self.stats['created'] += 1
                    self.logger.debug(f"✅ Fila {row_number}: {cedula} - NUEVO REGISTRO CREADO")
                    return True
                else:
                    self.stats['updated'] += 1
                    self.logger.debug(f"✅ Fila {row_number}: {cedula} - REGISTRO ACTUALIZADO")
                    return True
            else:
                self.stats['errors'] += 1
                self.errors.append({
                    'row': row_number,
                    'error': 'Error al procesar afiliado',
                    'data': row_data
                })
                return False

        except Exception as e:
            error_msg = f"Error procesando fila {row_number}: {str(e)}"
            self.logger.error(error_msg)
            self.errors.append({
                'row': row_number,
                'error': error_msg,
                'data': row_data
            })
            return False

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

    def _process_batch(self, batch_df: pd.DataFrame, model_class) -> Dict[str, Any]:
        """
        Procesa un lote de registros usando operaciones bulk.
        Esta es la clave de la optimización de rendimiento.
        """
        if batch_df.empty:
            return {'rows_processed': 0}
            
        # Obtener cédulas únicas del lote actual
        cedulas = batch_df['cedula'].unique().tolist()
        
        # Cargar registros existentes en memoria
        existing_records = model_class.objects.filter(
            cedula__in=cedulas
        ).values('id', 'cedula', 'nombre_completo', 'municipio')
        
        # Crear diccionario para búsqueda rápida
        existing_dict = {rec['cedula']: rec for rec in existing_records}
        
        # Preparar listas para operaciones bulk
        to_create = []
        to_update = []
        processed_cedulas = set()
        
        # Procesar cada registro del lote
        for _, row in batch_df.iterrows():
            cedula = row['cedula']
            
            # Evitar duplicados en el mismo lote
            if cedula in processed_cedulas:
                self.stats['ignored'] += 1
                continue
                
            processed_cedulas.add(cedula)
            
            # Obtener datos del registro
            nombre = row.get('nombre_completo', '')
            municipio = row.get('municipio', '')
            
            if cedula in existing_dict:
                # Verificar si hay cambios
                existing = existing_dict[cedula]
                if (existing['nombre_completo'] != nombre or 
                    existing['municipio'] != municipio):
                    # Hay cambios, preparar para actualización
                    obj = model_class(
                        id=existing['id'],
                        cedula=cedula,
                        nombre_completo=nombre,
                        municipio=municipio
                    )
                    to_update.append(obj)
                else:
                    # Sin cambios
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
            # Crear nuevos registros
            if to_create:
                try:
                    model_class.objects.bulk_create(to_create, batch_size=self.batch_size)
                    self.stats['created'] += len(to_create)
                except Exception as e:
                    self.logger.error(f"Error en bulk_create: {str(e)}")
                    self.stats['errors'] += len(to_create)
            
            # Actualizar registros existentes
            if to_update:
                try:
                    model_class.objects.bulk_update(
                        to_update, 
                        ['nombre_completo', 'municipio'],
                        batch_size=self.batch_size
                    )
                    self.stats['updated'] += len(to_update)
                except Exception as e:
                    self.logger.error(f"Error en bulk_update: {str(e)}")
                    self.stats['errors'] += len(to_update)
        
        return {
            'rows_processed': len(processed_cedulas),
            'created': len(to_create),
            'updated': len(to_update),
            'ignored': self.stats['ignored'],
            'errors': self.stats['errors']
        }

    def process_sheet_with_headers(self, df: pd.DataFrame, sheet_name: str) -> Dict[str, Any]:
        """Procesa hoja con encabezados usando operaciones bulk"""
        self.logger.info(f"📋 Procesando hoja CON encabezados: {sheet_name}")
        
        # Crear mapeo inteligente de columnas basado en patrones
        column_mapping = self._create_column_mapping(df.columns)
        
        # Renombrar columnas usando el mapeo
        data_df = df.rename(columns=column_mapping)
        
        # Normalizar y limpiar datos
        if 'cedula' in data_df.columns:
            data_df['cedula'] = data_df['cedula'].astype(str).str.strip()
            data_df = data_df[data_df['cedula'].str.len() >= 5]  # Filtrar cédulas inválidas
        
        if 'nombre_completo' in data_df.columns:
            data_df['nombre_completo'] = data_df['nombre_completo'].fillna('').astype(str).str.strip()
            
        if 'municipio' in data_df.columns:
            data_df['municipio'] = data_df['municipio'].fillna('').astype(str).str.strip()
        
        # Si no hay datos válidos, retornar temprano
        if data_df.empty:
            self.logger.warning(f"⚠️ No se encontraron datos válidos en la hoja {sheet_name}")
            return {'rows_processed': 0}
            
        # Procesar en lotes para evitar consumo excesivo de memoria
        total_processed = 0
        for i in range(0, len(data_df), self.batch_size):
            batch_df = data_df.iloc[i:i + self.batch_size]
            batch_result = self._process_batch(batch_df, self.model_class)
            total_processed += batch_result.get('rows_processed', 0)
            
            # Actualizar estadísticas
            for key in ['created', 'updated', 'ignored', 'errors']:
                if key in batch_result:
                    self.stats[key] += batch_result.get(key, 0)
        
        self.logger.info(f"✅ Hoja {sheet_name} procesada: {total_processed}/{len(df)} filas exitosas")
        return {'rows_processed': total_processed}

    def _create_column_mapping(self, columns) -> Dict[str, str]:
        """
        Crea un mapeo inteligente de nombres de columnas basado en patrones
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

    def process_sheet_without_headers(self, df: pd.DataFrame, sheet_name: str) -> Dict[str, Any]:
        """Procesa hoja sin encabezados usando operaciones bulk"""
        self.logger.info(f"📋 Procesando hoja SIN encabezados: {sheet_name}")
        
        # Detectar automáticamente las posiciones de las columnas
        positions = self._detect_column_positions(df)
        
        # Preparar datos para procesamiento masivo
        data = []
        for idx, row in df.iterrows():
            cedula = str(row.iloc[positions['cedula']]).strip() if positions['cedula'] >= 0 and positions['cedula'] < len(row) else ''
            if not cedula or len(cedula) < 5:  # Validación básica de cédula
                continue
                
            data.append({
                'cedula': cedula,
                'nombre_completo': str(row.iloc[positions['nombre_completo']]).strip() 
                    if positions['nombre_completo'] >= 0 and positions['nombre_completo'] < len(row) else '',
                'municipio': str(row.iloc[positions['municipio']]).strip() 
                    if positions['municipio'] >= 0 and positions['municipio'] < len(row) else ''
            })
        
        # Si no hay datos válidos, retornar temprano
        if not data:
            self.logger.warning(f"⚠️ No se encontraron datos válidos en la hoja {sheet_name}")
            return {'rows_processed': 0}
            
        # Convertir a DataFrame para procesamiento masivo
        data_df = pd.DataFrame(data)
        
        # Procesar en lotes para evitar consumo excesivo de memoria
        total_processed = 0
        for i in range(0, len(data_df), self.batch_size):
            batch_df = data_df.iloc[i:i + self.batch_size]
            batch_result = self._process_batch(batch_df, self.model_class)
            total_processed += batch_result.get('rows_processed', 0)
            
            # Actualizar estadísticas
            for key in ['created', 'updated', 'ignored', 'errors']:
                if key in batch_result:
                    self.stats[key] += batch_result.get(key, 0)
        
        self.logger.info(f"✅ Hoja {sheet_name} procesada: {total_processed}/{len(df)} filas exitosas")
        return {'rows_processed': total_processed}

    def _detect_column_positions(self, df: pd.DataFrame) -> Dict[str, int]:
        """
        Detecta automáticamente las posiciones de las columnas importantes
        analizando patrones típicos de cada tipo de dato
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

        # Para más columnas, detectar automáticamente usando patrones
        sample_rows = df.head(min(10, len(df)))
        self.logger.info(f"📊 Analizando muestra de {len(sample_rows)} filas para detectar patrones")

        # Detectar columna de cédula (números largos)
        cedula_scores = {}
        for i in range(len(df.columns)):
            score = 0
            valid_samples = 0
            for _, row in sample_rows.iterrows():
                if i < len(row) and pd.notna(row.iloc[i]):
                    val = str(row.iloc[i]).strip()
                    if len(val) >= 7 and val.isdigit():
                        score += 1
                        valid_samples += 1
                    elif len(val) >= 5 and val.replace('-', '').replace('.', '').isdigit():
                        score += 0.5
                        valid_samples += 1

            if valid_samples > 0:
                cedula_scores[i] = score / valid_samples  # Normalizar por muestras válidas

        if cedula_scores:
            best_col = max(cedula_scores, key=cedula_scores.get)
            positions['cedula'] = best_col
            self.logger.info(f"✅ Columna CÉDULA detectada en posición {best_col} (score: {cedula_scores[best_col]:.2f})")

        # Detectar columna de nombre (texto largo con espacios y mayúsculas)
        nombre_scores = {}
        for i in range(len(df.columns)):
            if i == positions['cedula']:  # No considerar la columna de cédula
                continue

            score = 0
            valid_samples = 0
            for _, row in sample_rows.iterrows():
                if i < len(row) and pd.notna(row.iloc[i]):
                    val = str(row.iloc[i]).strip()
                    if len(val) > 10 and any(word[0].isupper() for word in val.split()):
                        score += 1
                        valid_samples += 1
                    elif len(val) > 5 and ' ' in val:
                        score += 0.5
                        valid_samples += 1

            if valid_samples > 0:
                nombre_scores[i] = score / valid_samples  # Normalizar por muestras válidas

        if nombre_scores:
            best_col = max(nombre_scores, key=nombre_scores.get)
            positions['nombre_completo'] = best_col
            self.logger.info(f"✅ Columna NOMBRE detectada en posición {best_col} (score: {nombre_scores[best_col]:.2f})")

        # Detectar columna de municipio (texto con mayúsculas, posiblemente abreviado)
        municipio_scores = {}
        for i in range(len(df.columns)):
            if i in [positions['cedula'], positions['nombre_completo']]:  # No considerar columnas ya asignadas
                continue

            score = 0
            valid_samples = 0
            for _, row in sample_rows.iterrows():
                if i < len(row) and pd.notna(row.iloc[i]):
                    val = str(row.iloc[i]).strip().upper()
                    if len(val) >= 3 and val.isalpha():
                        score += 1
                        valid_samples += 1
                    elif len(val) >= 2 and all(c.isalpha() or c in [' '] for c in val):
                        score += 0.5
                        valid_samples += 1

            if valid_samples > 0:
                municipio_scores[i] = score / valid_samples  # Normalizar por muestras válidas

        if municipio_scores:
            best_col = max(municipio_scores, key=municipio_scores.get)
            positions['municipio'] = best_col
            self.logger.info(f"✅ Columna MUNICIPIO detectada en posición {best_col} (score: {municipio_scores[best_col]:.2f})")

        self.logger.info(f"🔍 Columnas detectadas automáticamente: {positions}")
        return positions


    def import_excel_clean(self, excel_file, model_class) -> Dict[str, Any]:
        """
        Método principal para importar desde Excel con tipos forzados a string.
        """
        try:
            # Forzar tipos clave como string para evitar inferencia automática de Pandas
            dtype_dict = {
                'cedula': str,
                'nombre_completo': str,
                'municipio': str
            }

            # Leer todas las hojas del Excel
            excel_data = pd.read_excel(excel_file, sheet_name=None, dtype=dtype_dict)

            total_stats = {
                'created': 0,
                'updated': 0,
                'ignored': 0,
                'errors': 0,
                'sheets_processed': 0
            }

            # Procesar cada hoja
            for sheet_name, df in excel_data.items():
                self.logger.info(f"📋 Procesando hoja: {sheet_name}")
                total_stats['sheets_processed'] += 1

                if df.empty:
                    self.logger.warning(f"⚠️ Hoja '{sheet_name}' está vacía - ignorada")
                    continue

                # Detectar si tiene encabezados
                has_headers = self.detect_headers(df)

                if has_headers:
                    sheet_stats = self.process_sheet_with_headers(df, sheet_name)
                else:
                    sheet_stats = self.process_sheet_without_headers(df, sheet_name)

                # Acumular estadísticas
                for key in total_stats:
                    if key in sheet_stats:
                        total_stats[key] += sheet_stats[key]

            # Log final
            self.logger.info(f"✅ Importación completada: {total_stats}")
            return {
                'stats': total_stats,
                'errors': self.errors,
                'processed_rows': self.processed_rows
            }

        except Exception as e:
            error_msg = f"Error al importar Excel: {str(e)}"
            self.logger.error(error_msg)
            self.errors.append({'error': error_msg})
            return {'stats': total_stats, 'errors': self.errors}
def importar_afiliados_desde_excel(excel_file) -> Dict[str, Any]:
    """Importa afiliados usando el importador optimizado"""
    from afiliados.models import Afiliado
    importer = ExcelImportClean(batch_size=5000)
    return importer.import_excel_clean(excel_file, Afiliado)


def importar_ademacor_desde_excel(excel_file) -> Dict[str, Any]:
    """Importa datos de ADEMACOR usando el importador optimizado"""
    from afiliados.models import DatosAdemacor
    importer = ExcelImportClean(batch_size=5000)
    return importer.import_excel_clean(excel_file, DatosAdemacor)



