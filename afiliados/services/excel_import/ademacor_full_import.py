from afiliados.models import DatosAdemacor
from .excel_import_clean import ExcelImportClean
import logging

logger = logging.getLogger(__name__)

def importar_ademacor_desde_excel(archivo_excel):
    """
    Importa datos de ADEMACOR desde un archivo Excel usando el importador limpio.

    Args:
        archivo_excel: Archivo Excel subido (InMemoryUploadedFile o TemporaryUploadedFile)

    Returns:
        dict: Estadísticas de la importación
    """
    try:
        importador = ExcelImportClean(DatosAdemacor)
        stats = importador.process_file(archivo_excel)
        return stats
    except Exception as e:
        logger.error(f"Error importando datos de ADEMACOR: {e}")
        raise e
