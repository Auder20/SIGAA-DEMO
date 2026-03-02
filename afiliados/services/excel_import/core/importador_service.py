import pandas as pd
import tempfile
import os
from typing import Dict, Any, List, Optional
from django.db import transaction, connection, OperationalError
from django.core.files.base import ContentFile
import time

from ..core.logger_manager import ImportLoggerManager
from ..core.excel_detector import ExcelFormatDetector
from ..processors.header_normalizer import HeaderNormalizer
from ..processors.column_mapper import ColumnMapper
from ..processors.data_validator import DataValidator
from ..processors.row_processor import RowProcessor


class ExcelImportService:
    """
    Servicio principal para importación de datos desde Excel.
    """
    
    def __init__(self):
        self.logger_manager = ImportLoggerManager('excel_import')
        self.excel_detector = ExcelFormatDetector(self.logger_manager)
        self.header_normalizer = HeaderNormalizer(self.logger_manager)
        self.column_mapper = ColumnMapper(self.logger_manager)
        self.data_validator = DataValidator(self.logger_manager)
        self.row_processor = RowProcessor(self.logger_manager)
        
    def _ensure_connection(self):
        """Mantiene la conexión a BD activa con keep-alive"""
        try:
            # Verificar si estamos dentro de una transacción atómica
            if hasattr(connection, 'in_atomic_block') and connection.in_atomic_block:
                # Si estamos en una transacción atómica, no podemos ejecutar queries
                # Simplemente retornamos sin hacer nada
                return

            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except OperationalError:
            # Si hay error de conexión, cerrar y dejar que Django cree una nueva
            if not (hasattr(connection, 'in_atomic_block') and connection.in_atomic_block):
                connection.close()
        except Exception:
            # Ignorar otros errores para no interrumpir el flujo
            pass
    
    def _create_error_file(self, errors: List[Dict], original_filename: str = None) -> Optional[str]:
        """
        Crea un archivo temporal con los registros que generaron errores.
        
        Args:
            errors: Lista de diccionarios con información de errores
            original_filename: Nombre del archivo original (para el nombre del archivo de error)
            
        Returns:
            Ruta del archivo temporal creado o None si no hay errores
        """
        if not errors:
            return None
            
        # Filtrar solo los errores que tienen datos de fila
        error_data = []
        for error in errors:
            if 'row_data' in error and isinstance(error['row_data'], dict):
                row_data = error['row_data'].copy()
                row_data['error'] = error.get('error', 'Error desconocido')
                error_data.append(row_data)
        
        if not error_data:
            return None
            
        # Crear DataFrame y guardar en archivo temporal
        try:
            error_df = pd.DataFrame(error_data)
            
            # Crear nombre de archivo descriptivo
            base_name = 'importacion'
            if original_filename:
                base_name = os.path.splitext(os.path.basename(original_filename))[0]
                
            error_filename = f"{base_name}_errores_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            
            # Crear archivo temporal
            temp_dir = tempfile.gettempdir()
            error_filepath = os.path.join(temp_dir, error_filename)
            
            # Guardar en Excel
            error_df.to_excel(error_filepath, index=False, engine='openpyxl')
            return error_filepath
            
        except Exception as e:
            self.logger_manager.logger.error(f"Error al crear archivo de errores: {str(e)}")
            return None
    
    def import_from_excel(self, excel_file) -> Dict[str, Any]:
        """
        Importa afiliados desde un archivo Excel con detección automática de formato.
        
        Args:
            excel_file: Archivo Excel a procesar
            
        Returns:
            Dict con resumen de la importación que incluye:
            - rows_processed: Número de filas procesadas exitosamente
            - missing_columns: Columnas faltantes
            - errors: Lista de errores encontrados
            - total_rows: Total de filas en el archivo
            - metadata: Metadatos del archivo
            - error_file: Ruta al archivo con los registros que generaron errores (si aplica)
        """
        summary = {
            'rows_processed': 0,
            'missing_columns': [],
            'errors': [],
            'total_rows': 0,
            'metadata': {},
            'error_file': None
        }
        
        try:
            # 1. Detectar formato y cargar datos
            dataframes, has_headers, metadata = self.excel_detector.detect_format_and_load(excel_file)
            summary['metadata'] = metadata
            
            if not dataframes:
                raise ValueError("No se encontraron datos válidos en el archivo Excel")
            
            # 2. Procesar cada DataFrame (puede ser una o múltiples hojas)
            total_rows = sum(len(df) for df in dataframes)
            summary['total_rows'] = total_rows
            
            filename = getattr(excel_file, 'name', 'archivo_excel')
            self.logger_manager.log_import_start(filename, total_rows)
            
            # 3. Procesar con transacciones más pequeñas y manejo de reconexión
            try:
                # Procesar en lotes más pequeños para evitar timeouts
                batch_size = 10  # Procesar 10 filas por transacción
                total_processed = 0

                for df_index, df in enumerate(dataframes):
                    sheet_summary = self._process_dataframe_with_reconnection(df, df_index, has_headers, batch_size)

                    # Agregar resultados al resumen general
                    summary['rows_processed'] += sheet_summary['rows_processed']
                    summary['errors'].extend(sheet_summary['errors'])

                    # Solo agregar missing_columns de la primera hoja para evitar duplicados
                    if df_index == 0:
                        summary['missing_columns'] = sheet_summary['missing_columns']

                    total_processed += sheet_summary['rows_processed']
                
                # 4. Crear archivo de errores si es necesario
                if summary['errors']:
                    error_filepath = self._create_error_file(
                        summary['errors'],
                        getattr(excel_file, 'name', None)
                    )
                    summary['error_file'] = error_filepath
                    
                # 5. Log final solo si la transacción fue exitosa
                self.logger_manager.log_final_summary(summary)
                
            except Exception as e:
                # Si hay un error crítico en el procesamiento general
                error_msg = f"Error crítico durante la importación: {str(e)}"
                self.logger_manager.logger.error(error_msg)
                if hasattr(e, '__traceback__'):
                    import traceback
                    self.logger_manager.logger.error(traceback.format_exc())
                
                summary['errors'].append({'row': 0, 'error': error_msg})
        
        except Exception as e:
            # Manejar cualquier otro error fuera de la transacción
            error_msg = f"Error crítico durante la importación: {str(e)}"
            print(f"\nERROR CRÍTICO: {error_msg}")
            if hasattr(e, '__traceback__'):
                import traceback
                traceback.print_exc()
            summary['errors'].append({'row': 0, 'error': error_msg})
        
        return summary
    
    def _process_dataframe_with_reconnection(self, df: pd.DataFrame, df_index: int, has_headers: bool, batch_size: int = 10) -> Dict[str, Any]:
        """
        Procesa un DataFrame con manejo robusto de reconexión y lotes pequeños.

        Args:
            df: DataFrame a procesar
            df_index: Índice del DataFrame
            has_headers: Si el DataFrame tiene encabezados
            batch_size: Número de filas por transacción

        Returns:
            Dict con resumen del procesamiento
        """
        sheet_summary = {
            'rows_processed': 0,
            'missing_columns': [],
            'errors': []
        }

        try:
            # 1. Validar DataFrame
            validation_errors = self.data_validator.validate_dataframe(df)
            if validation_errors:
                for error in validation_errors:
                    sheet_summary['errors'].append({'row': 0, 'error': f'validacion_dataframe: {error}'})
                return sheet_summary

            # 2. Procesar encabezados si los tiene
            if has_headers:
                df, normalized_to_original = self.header_normalizer.normalize_dataframe_headers(df)
                column_mapping, missing_critical = self.column_mapper.map_columns(normalized_to_original)

                # Validar columnas críticas
                try:
                    self.column_mapper.validate_critical_columns(missing_critical)
                except ValueError as e:
                    sheet_summary['errors'].append({'row': 0, 'error': str(e)})
                    sheet_summary['missing_columns'] = missing_critical
                    return sheet_summary

                # Renombrar columnas
                if column_mapping:
                    df = df.rename(columns=column_mapping)

                sheet_summary['missing_columns'] = missing_critical

            # 3. Procesar filas en lotes pequeños
            total_rows = len(df)
            processed_rows = 0

            while processed_rows < total_rows:
                batch_df = df.iloc[processed_rows:processed_rows + batch_size]
                batch_start = processed_rows

                # Procesar lote con reintentos
                batch_success = self._process_batch_with_retry(batch_df, batch_start, sheet_summary)

                if batch_success:
                    sheet_summary['rows_processed'] += len(batch_df)
                    processed_rows += len(batch_df)
                else:
                    # Si el lote falla completamente, marcar error y continuar
                    for idx, row in batch_df.iterrows():
                        sheet_summary['errors'].append({
                            'row': processed_rows + 2,
                            'error': 'Error procesando lote completo',
                            'row_data': row.to_dict()
                        })
                    processed_rows += len(batch_df)

            if df_index == 0:
                self.logger_manager.logger.info(f"✅ Hoja principal procesada: {sheet_summary['rows_processed']} filas exitosas")
            else:
                self.logger_manager.logger.info(f"✅ Hoja {df_index + 1} procesada: {sheet_summary['rows_processed']} filas exitosas")

        except Exception as e:
            error_msg = f"Error procesando DataFrame {df_index}: {str(e)}"
            self.logger_manager.logger.error(error_msg)
            sheet_summary['errors'].append({'row': 0, 'error': error_msg})

        return sheet_summary

    def _process_batch_with_retry(self, batch_df: pd.DataFrame, batch_start: int, sheet_summary: Dict[str, Any]) -> bool:
        """
        Procesa un lote de filas con reintentos automáticos y manejo robusto de bloqueos.

        Args:
            batch_df: DataFrame con las filas del lote
            batch_start: Índice inicial del lote
            sheet_summary: Diccionario para acumular resultados

        Returns:
            bool: True si el lote se procesó exitosamente
        """
        max_retries = 3
        retry_delay = 2  # segundos

        for attempt in range(max_retries):
            try:
                # Procesar lote dentro de una transacción atómica pequeña
                with transaction.atomic():
                    for idx, row in batch_df.iterrows():
                        try:
                            self.logger_manager.log_processing_progress(batch_start + idx + 1, len(batch_df))

                            # Guardar datos originales para posibles errores
                            row_data = row.to_dict()

                            # Procesar fila individual
                            result = self.row_processor.process_row(row, idx)

                            if not result.get('success', False):
                                # Agregar error pero continuar con el lote
                                error_info = {
                                    'row': batch_start + idx + 2,
                                    'error': result.get('error', 'Error desconocido'),
                                    'row_data': row_data
                                }
                                sheet_summary['errors'].append(error_info)
                                self.logger_manager.logger.warning(f"Error en fila {batch_start + idx + 2}: {error_info['error']}")

                        except Exception as e:
                            error_msg = f"Error procesando fila {batch_start + idx + 2}: {str(e)}"

                            # Verificar si es un error de bloqueo de base de datos
                            if "Lock wait timeout exceeded" in str(e):
                                self.logger_manager.logger.warning(f"🔒 Bloqueo detectado en fila {batch_start + idx + 2} - marcando como error pero continuando")
                                sheet_summary['errors'].append({
                                    'row': batch_start + idx + 2,
                                    'error': f"Bloqueo de BD: {str(e)}",
                                    'row_data': row_data if 'row_data' in locals() else {}
                                })
                            elif "TransactionManagementError" in str(e):
                                self.logger_manager.logger.warning(f"🔄 Error de transacción en fila {batch_start + idx + 2} - marcando como error pero continuando")
                                sheet_summary['errors'].append({
                                    'row': batch_start + idx + 2,
                                    'error': f"Error de transacción: {str(e)}",
                                    'row_data': row_data if 'row_data' in locals() else {}
                                })
                            else:
                                self.logger_manager.logger.error(error_msg, exc_info=True)
                                sheet_summary['errors'].append({
                                    'row': batch_start + idx + 2,
                                    'error': error_msg,
                                    'row_data': row_data if 'row_data' in locals() else {}
                                })

                # Si llegamos aquí, el lote se procesó exitosamente
                return True

            except Exception as e:
                error_msg = f"Error en lote (intento {attempt + 1}/{max_retries}): {str(e)}"
                self.logger_manager.logger.warning(error_msg)

                # Verificar si es un error de bloqueo de base de datos
                is_lock_error = False
                if "Lock wait timeout exceeded" in str(e):
                    is_lock_error = True
                    self.logger_manager.logger.warning("🔒 Detectado bloqueo de base de datos - esperando antes de reintentar")
                elif "TransactionManagementError" in str(e):
                    is_lock_error = True
                    self.logger_manager.logger.warning("🔄 Error de gestión de transacción - limpiando estado")

                if attempt < max_retries - 1 and is_lock_error:
                    # Intentar reconectar y limpiar estado
                    try:
                        # Forzar cierre de conexión para obtener una nueva
                        from django.db import connection
                        connection.close()

                        # Limpiar cualquier estado de transacción pendiente
                        if hasattr(connection, 'in_atomic_block') and connection.in_atomic_block:
                            # Si estamos en una transacción rota, intentar rollback
                            try:
                                transaction.set_rollback()
                            except:
                                pass  # Ignorar errores de rollback

                        # Esperar más tiempo para errores de bloqueo
                        wait_time = retry_delay * (2 if is_lock_error else 1)
                        import time
                        time.sleep(wait_time)

                        self.logger_manager.logger.info(f"🔄 Reintentando lote después de limpieza (intento {attempt + 2})")
                    except Exception as reconnect_error:
                        self.logger_manager.logger.error(f"Error al limpiar conexión: {reconnect_error}")

        # Si todos los intentos fallaron
        self.logger_manager.logger.error(f"❌ Lote falló completamente después de {max_retries} intentos")
        return False