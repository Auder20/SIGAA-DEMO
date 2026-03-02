import logging
import sys
from typing import Dict, Any, List, Optional
from datetime import datetime


class ImportLoggerManager:
    """
    Gestor centralizado de logging para el sistema de importación.
    """
    
    def __init__(self, module_name: str = 'excel_import'):
        self.logger = logging.getLogger(f'sigaa.{module_name}')
        self._setup_logger()
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    def _setup_logger(self):
        """Configura el logger con formato estructurado."""
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def log_import_start(self, filename: str, total_rows: int):
        """Log del inicio de importación."""
        self.logger.info("=" * 80)
        self.logger.info("🚀 INICIANDO IMPORTACIÓN DE EXCEL - SIGAA")
        self.logger.info("=" * 80)
        self.logger.info(f"📁 Archivo: {filename}")
        self.logger.info(f"📊 Filas totales: {total_rows}")
        self.logger.info(f"🔢 Sesión: {self.session_id}")
        self.logger.info("=" * 80)
    
    def log_columns_analysis(self, original_columns: List[str], mapped_columns: Dict[str, str]):
        """Log del análisis de columnas."""
        self.logger.info("📋 ANÁLISIS DE COLUMNAS:")
        self.logger.info(f"   Columnas detectadas: {len(original_columns)}")
        self.logger.info(f"   Columnas mapeadas: {len(mapped_columns)}")
        
        for original, canonical in mapped_columns.items():
            self.logger.info(f"   '{original}' → '{canonical}'")
    
    def log_processing_progress(self, current: int, total: int, interval: int = 10):
        """Log del progreso de procesamiento (cada N filas)."""
        if current % interval == 0 or current <= 5:
            progress = (current / total) * 100
            self.logger.info(f"⏳ Progreso: {current}/{total} ({progress:.1f}%)")
    
    def log_row_success(self, row_num: int, cedula: str, action: str):
        """Log de fila procesada exitosamente."""
        self.logger.debug(f"✅ Fila {row_num}: {cedula} - {action}")
    
    def log_row_error(self, row_num: int, error: str, cedula: Optional[str] = None):
        """Log de error en fila."""
        cedula_info = f" (Cédula: {cedula})" if cedula else ""
        self.logger.error(f"❌ Error Fila {row_num}: {error}{cedula_info}")
    
    def log_final_summary(self, summary: Dict[str, Any]):
        """Log del resumen final."""
        self.logger.info("=" * 80)
        self.logger.info("📊 RESUMEN FINAL DE IMPORTACIÓN")
        self.logger.info("=" * 80)
        self.logger.info(f"✅ Filas procesadas: {summary.get('rows_processed', 0)}")
        self.logger.info(f"❌ Filas con errores: {len(summary.get('errors', []))}")
        self.logger.info(f"⚠️  Columnas faltantes: {len(summary.get('missing_columns', []))}")
        
        if summary.get('total_rows', 0) > 0:
            success_rate = (summary.get('rows_processed', 0) / summary.get('total_rows', 1)) * 100
            self.logger.info(f"📈 Tasa de éxito: {success_rate:.1f}%")
        
        self.logger.info("=" * 80)
