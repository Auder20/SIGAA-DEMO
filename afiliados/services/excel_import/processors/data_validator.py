import pandas as pd
from typing import List, Any
from ..core.logger_manager import ImportLoggerManager


class DataValidator:
    """
    Validador de datos para importación Excel.
    """
    
    def __init__(self, logger_manager: ImportLoggerManager):
        self.logger = logger_manager
    
    def validate_dataframe(self, df: pd.DataFrame) -> List[str]:
        """
        Valida que el DataFrame tenga las columnas mínimas requeridas.
        
        Args:
            df: DataFrame a validar
            
        Returns:
            List[str]: Lista de errores encontrados
        """
        errors = []
        
        if df is None or df.empty:
            errors.append("DataFrame está vacío o es None")
            return errors
        
        # Verificar que haya al menos una fila de datos
        if len(df) == 0:
            errors.append("DataFrame no contiene filas de datos")
        
        # Verificar que haya al menos una columna
        if len(df.columns) == 0:
            errors.append("DataFrame no contiene columnas")
        
        return errors
    
    def is_valid_cedula_row(self, row: pd.Series) -> bool:
        """
        Determina si una fila contiene datos válidos de cédula.
        Útil para filtrar filas decorativas o títulos.
        
        Args:
            row: Fila del DataFrame
            
        Returns:
            bool: True si la fila contiene una cédula válida
        """
        # Buscar en las primeras columnas un valor que parezca una cédula
        for i in range(min(4, len(row))):  # Revisar las primeras 4 columnas
            value = row.iloc[i]
            if pd.isna(value):
                continue
            
            # Convertir a string y limpiar
            str_value = str(value).strip()
            
            # Verificar si es un número que podría ser una cédula
            if str_value.isdigit() and len(str_value) >= 6:
                return True
            
            # Verificar si es un patrón de cédula con guiones o puntos
            import re
            if re.match(r'^\d{1,3}[.-]?\d{3,}[.-]?\d{3,}', str_value):
                return True
        
        return False
