from .core.importador_service import ExcelImportService
from .excel_import_clean import ExcelImportClean, importar_ademacor_desde_excel
from afiliados.models import Afiliado

# Función principal para mantener compatibilidad con código existente
def importar_afiliados_desde_excel(archivo_excel):
    """
    Función que utiliza el nuevo importador optimizado para afiliados.
    
    Args:
        archivo_excel: Archivo Excel a procesar (path o file object)
        
    Returns:
        Dict con resumen de la importación
    """
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(" Iniciando importación con el nuevo importador optimizado...")
    
    try:
        # Crear instancia del importador con la clase de modelo Afiliado
        importador = ExcelImportClean(model_class=Afiliado, batch_size=1000)
        
        # Procesar el archivo Excel
        resultado = importador.import_excel_clean(archivo_excel, Afiliado)
        
        logger.info(f" Importación completada exitosamente. {resultado.get('rows_processed', 0)} filas procesadas")
        return {
            'success': True,
            'rows_processed': resultado.get('rows_processed', 0),
            'created': resultado.get('created', 0),
            'updated': resultado.get('updated', 0),
            'ignored': resultado.get('ignored', 0),
            'errors': resultado.get('errors', [])
        }
    except Exception as e:
        logger.error(f" Error en la importación: {str(e)}", exc_info=True)
        return {
            'success': False,
            'error': str(e),
            'rows_processed': 0,
            'created': 0,
            'updated': 0,
            'ignored': 0,
            'errors': [str(e)]
        }


# Importadores específicos para diferentes tipos de datos (ORIGINALES)


def importar_ademacor_desde_excel_original(archivo_excel, batch_size: int = 1000):
    """
    Función para importar datos de ADEMACOR usando el importador ORIGINAL.
    
    Esta función se mantiene por compatibilidad con código existente.
    Este importador usa la lógica probada que funcionaba correctamente.

    Args:
        archivo_excel: Archivo Excel a procesar
        batch_size: Tamaño del lote para operaciones bulk (default: 1000)

    Returns:
        Dict con resumen de la importación
    """
    from .ademacor_complex_import import importar_ademacor_desde_excel as ademacor_importer
    return ademacor_importer(archivo_excel)


def importar_afiliados_desde_excel_original(archivo_excel, batch_size: int = 1000):
    """
    Función para importar afiliados usando el importador ORIGINAL.

    Este importador usa la lógica probada que funcionaba correctamente.

    Args:
        archivo_excel: Archivo Excel a procesar
        batch_size: Tamaño del lote para operaciones bulk (default: 1000)

    Returns:
        Dict con resumen de la importación
    """
    from .excel_import_clean import importar_afiliados_desde_excel as afiliados_importer
    return afiliados_importer(archivo_excel)


# Mantener compatibilidad con código existente
from .core.importador_service import ExcelImportService


# Exportar funciones para uso avanzado
__all__ = [
    'ExcelImportService',
    'importar_afiliados_desde_excel',
    'importar_ademacor_desde_excel_original',
    'importar_afiliados_desde_excel_original'
]
