from typing import Dict, List, Tuple
from ..utils.alias_definitions import AliasDefinitions
from ..core.logger_manager import ImportLoggerManager


class ColumnMapper:
    """
    Mapeador de columnas usando alias definidos.
    """
    
    def __init__(self, logger_manager: ImportLoggerManager):
        self.logger = logger_manager
        self.alias_definitions = AliasDefinitions()
    
    def map_columns(self, normalized_to_original: Dict[str, str]) -> Tuple[Dict[str, str], List[str]]:
        """
        Mapea columnas normalizadas a nombres canónicos usando alias.
        
        Args:
            normalized_to_original: Mapeo de headers normalizados a originales
            
        Returns:
            tuple: (mapeo_final, columnas_criticas_faltantes)
        """
        alias_map = self.alias_definitions.get_column_aliases()
        column_mapping = {}
        missing_critical = []
        
        # Encontrar para cada canonical el primer alias presente en el archivo
        for canonical, aliases in alias_map.items():
            found = False
            for alias in aliases:
                # Normalizar el alias para comparación
                from ..processors.header_normalizer import HeaderNormalizer
                dummy_logger = ImportLoggerManager('dummy')
                normalizer = HeaderNormalizer(dummy_logger)
                normalized_alias = normalizer.normalize_header(alias)
                
                if normalized_alias in normalized_to_original:
                    original_name = normalized_to_original[normalized_alias]
                    column_mapping[original_name] = canonical
                    found = True
                    break
            
            # Solo marcar como faltante si es crítico
            if not found and canonical in ('cedula', 'nombre_completo'):
                missing_critical.append(canonical)
        
        self.logger.log_columns_analysis(
            list(normalized_to_original.values()),
            column_mapping
        )
        
        return column_mapping, missing_critical
    
    def validate_critical_columns(self, missing_critical: List[str]) -> None:
        """
        Valida que las columnas críticas estén presentes.
        
        Args:
            missing_critical: Lista de columnas críticas faltantes
            
        Raises:
            ValueError: Si faltan columnas críticas obligatorias
        """
        if 'cedula' in missing_critical:
            raise ValueError("Columna 'cedula' no encontrada. Esta es una columna obligatoria.")