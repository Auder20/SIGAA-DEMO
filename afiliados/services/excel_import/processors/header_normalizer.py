import re
import unicodedata
import pandas as pd
from typing import Any, Dict, List
from ..core.logger_manager import ImportLoggerManager


class HeaderNormalizer:
    """
    Normalizador de encabezados de Excel.
    """
    
    def __init__(self, logger_manager: ImportLoggerManager):
        self.logger = logger_manager
    
    def normalize_header(self, header: Any) -> str:
        """
        Normaliza un encabezado: baja a minúsculas, elimina acentos y reemplaza espacios/puntuación por guiones bajos.
        
        Args:
            header: Valor a normalizar (puede ser None, str, int, float)
        
        Returns:
            str: Header normalizado o string vacío si el input es None/vacío
        """
        # Manejo seguro de valores None o vacíos
        if header is None or pd.isna(header):
            self.logger.logger.warning("Header nulo o NaN detectado, retornando string vacío")
            return ''
        
        # Convertir a string de manera segura
        try:
            header_str = str(header).strip()
            if not header_str:  # String vacío después del strip
                self.logger.logger.warning("Header vacío después de strip, retornando string vacío")
                return ''
        except Exception as e:
            self.logger.logger.error(f"Error convirtiendo header a string: {e}, valor: {header}")
            return ''
        
        try:
            # Normalizar caracteres Unicode
            header_str = unicodedata.normalize('NFKD', header_str)
            header_str = ''.join(ch for ch in header_str if not unicodedata.combining(ch))
            
            # Convertir a minúsculas
            header_str = header_str.lower()
            
            # Reemplazar caracteres no alfanuméricos por guiones bajos
            header_str = re.sub(r"[^0-9a-z]+", '_', header_str)
            
            # Eliminar múltiples guiones bajos consecutivos
            header_str = re.sub(r'_+', '_', header_str)
            
            # Eliminar guiones bajos al inicio y final
            header_str = header_str.strip('_')
            
            return header_str
            
        except Exception as e:
            self.logger.logger.error(f"Error normalizando header '{header_str}': {e}")
            return ''
    
    def normalize_dataframe_headers(self, df: pd.DataFrame) -> tuple[pd.DataFrame, Dict[str, str]]:
        """
        Normaliza todos los encabezados de un DataFrame.
        
        Args:
            df: DataFrame con encabezados a normalizar
            
        Returns:
            tuple: (DataFrame con headers normalizados, mapeo original->normalizado)
        """
        # Filtrar columnas con nombres válidos
        valid_columns = []
        normalized_to_original = {}
        
        for col in df.columns:
            normalized = self.normalize_header(col)
            if normalized:  # Solo mantener columnas con nombres válidos
                valid_columns.append(col)
                normalized_to_original[normalized] = col
            else:
                self.logger.logger.warning(f"Columna ignorada por nombre inválido: {col}")
        
        if not valid_columns:
            raise ValueError("No se encontraron columnas válidas en el archivo")
        
        # Filtrar DataFrame para solo incluir columnas válidas
        df_filtered = df[valid_columns]
        