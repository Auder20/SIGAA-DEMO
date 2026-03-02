import pandas as pd
import re
import unicodedata
from typing import Any, Optional


class DataConverters:
    """
    Utilidades para conversión segura de datos desde Excel.
    """
    
    @staticmethod
    def safe_string_conversion(value: Any) -> str:
        """
        Convierte un valor a string de manera segura.
        
        Args:
            value: Valor a convertir
            
        Returns:
            str: Valor convertido a string o string vacío
        """
        if value is None or pd.isna(value):
            return ''
        
        try:
            if isinstance(value, (float, int)):
                # Para números flotantes que representan enteros, convertir a int primero
                if isinstance(value, float) and value.is_integer():
                    return str(int(value))
                return str(value)
            return str(value).strip()
        except Exception:
            return ''
    
    @staticmethod
    def safe_cedula_conversion(cedula_value: Any) -> Optional[str]:
        """
        Convierte un valor de cédula de manera segura a string.
        
        Args:
            cedula_value: Valor de cédula desde Excel
            
        Returns:
            str: Cédula normalizada o None si es inválida
        """
        if cedula_value is None or pd.isna(cedula_value):
            return None
            
        try:
            # Si es número, convertir a entero y luego a string
            if isinstance(cedula_value, (float, int)):
                if isinstance(cedula_value, float) and cedula_value.is_integer():
                    return str(int(cedula_value))
                return str(int(cedula_value))
            
            # Si es string, limpiar y validar
            cedula_str = str(cedula_value).strip()
            if not cedula_str or cedula_str.lower() in ['nan', 'none', 'null', '']:
                return None
                
            # Remover caracteres no numéricos si es necesario
            cedula_clean = re.sub(r'[^\d]', '', cedula_str)
            if cedula_clean and len(cedula_clean) >= 6:  # Validación básica de longitud
                return cedula_clean
                
            return cedula_str if cedula_str else None
            
        except Exception:
            return None
    
    @staticmethod
    def safe_int_conversion(value: Any, default: int = 0) -> int:
        """Convierte un valor a entero de manera segura."""
        if value is None or pd.isna(value):
            return default
        
        try:
            if isinstance(value, str) and not value.strip():
                return default
            return int(float(value))
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def safe_float_conversion(value: Any, default: float = 0.0) -> float:
        """Convierte un valor a flotante de manera segura."""
        if value is None or pd.isna(value):
            return default
        
        try:
            if isinstance(value, str) and not value.strip():
                return default
            return float(value)
        except (ValueError, TypeError):
            return default
    
    @staticmethod
    def safe_date_conversion(value: Any):
        """Convierte un valor a fecha de manera segura."""
        if value is None or pd.isna(value):
            return None
        
        try:
            if isinstance(value, pd.Timestamp):
                return value.date()
            elif isinstance(value, str):
                return pd.to_datetime(value).date()
            return value
        except Exception:
            return None