# import pandas as pd  # Temporalmente comentado para migraciones
from typing import Dict, List, Tuple, Any, Optional
from ..utils.alias_definitions import AliasDefinitions
from ..processors.data_validator import DataValidator
from ..core.logger_manager import ImportLoggerManager


class ExcelFormatDetector:
    """
    Detector de formato de archivos Excel (con/sin encabezados, múltiples hojas).
    """
    
    def __init__(self, logger_manager: ImportLoggerManager):
        self.logger = logger_manager
        self.validator = DataValidator(logger_manager)
        self.alias_definitions = AliasDefinitions()
    
    def detect_format_and_load(self, excel_file) -> Tuple[List[pd.DataFrame], bool, Dict[str, Any]]:
        """
        Detecta el formato del Excel y carga los datos apropiadamente.
        
        Args:
            excel_file: Archivo Excel a analizar
            
        Returns:
            tuple: (lista_dataframes, tiene_encabezados, metadatos)
        """
        try:
            # Primero intentar leer las hojas disponibles
            excel_sheets = pd.read_excel(excel_file, sheet_name=None, engine='openpyxl', nrows=5)
            
            metadata = {
                'total_sheets': len(excel_sheets),
                'sheet_names': list(excel_sheets.keys()),
                'format_detected': None,
                'processing_strategy': None
            }
            
            self.logger.logger.info(f"📄 Excel detectado con {metadata['total_sheets']} hojas: {metadata['sheet_names']}")
            
            # Analizar la primera hoja para determinar el formato
            first_sheet_name = list(excel_sheets.keys())[0]
            sample_df = excel_sheets[first_sheet_name]
            
            has_headers = self._detect_headers(sample_df)
            
            if has_headers:
                metadata['format_detected'] = 'with_headers'
                metadata['processing_strategy'] = 'single_sheet_with_headers'
                
                # Cargar solo la primera hoja con encabezados
                full_df = pd.read_excel(excel_file, sheet_name=first_sheet_name, engine='openpyxl')
                dataframes = [full_df]
                
                self.logger.logger.info("✅ Formato detectado: Excel CON encabezados - procesando hoja principal")
                
            else:
                metadata['format_detected'] = 'no_headers'
                metadata['processing_strategy'] = 'all_sheets_no_headers'
                
                # Cargar todas las hojas sin encabezados
                dataframes = []
                all_sheets = pd.read_excel(excel_file, sheet_name=None, engine='openpyxl', header=None)
                
                for sheet_name, df in all_sheets.items():
                    if not df.empty:
                        # Filtrar filas que parezcan datos válidos
                        valid_df = self._filter_valid_data_rows(df)
                        if not valid_df.empty:
                            # Aplicar mapeo de columnas sin encabezados
                            mapped_df = self._apply_no_header_mapping(valid_df)
                            dataframes.append(mapped_df)
                
                self.logger.logger.info(f"✅ Formato detectado: Excel SIN encabezados - procesando {len(dataframes)} hojas con datos válidos")
            
            return dataframes, has_headers, metadata
            
        except Exception as e:
            self.logger.logger.error(f"Error detectando formato de Excel: {str(e)}")
            raise
    
    def _detect_headers(self, sample_df: pd.DataFrame) -> bool:
        """
        Detecta si el DataFrame tiene encabezados válidos.
        
        Args:
            sample_df: DataFrame de muestra (primeras filas)
            
        Returns:
            bool: True si tiene encabezados reconocibles
        """
        if sample_df.empty:
            return False
        
        # Obtener la primera fila como posibles encabezados
        potential_headers = sample_df.iloc[0] if len(sample_df) > 0 else sample_df.columns
        
        # Verificar si alguno de los valores en la primera fila coincide con nuestros alias
        alias_map = self.alias_definitions.get_column_aliases()
        all_aliases = []
        for aliases in alias_map.values():
            all_aliases.extend(aliases)
        
        # Normalizar y comparar
        from ..processors.header_normalizer import HeaderNormalizer
        normalizer = HeaderNormalizer(self.logger)
        
        matches = 0
        total_checked = 0
        
        for header in potential_headers:
            if pd.isna(header):
                continue
            
            total_checked += 1
            header_str = str(header).strip()
            
            # Verificar si el encabezado parece ser un nombre en lugar de un encabezado
            if any(c.isalpha() for c in header_str) and len(header_str) > 30:
                self.logger.logger.info(f"🔍 Encabezado parece ser un nombre: {header_str}")
                return False
                
            normalized_header = normalizer.normalize_header(header_str)
            
            for alias in all_aliases:
                normalized_alias = normalizer.normalize_header(alias)
                if normalized_header == normalized_alias:
                    matches += 1
                    break
        
        # Si al menos 2 encabezados coinciden con nuestros alias, consideramos que tiene encabezados
        has_headers = matches >= 2
        
        self.logger.logger.info(f"🔍 Detección de encabezados: {matches}/{total_checked} coincidencias = {has_headers}")
        
        return has_headers
    
    def _filter_valid_data_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filtra filas que contienen datos válidos (ignora títulos decorativos).
        
        Args:
            df: DataFrame sin encabezados
            
        Returns:
            DataFrame con solo filas de datos válidos
        """
        if df.empty:
            return df
            
        valid_indices = []
        
        # Verificar cada fila para ver si parece contener datos válidos
        for idx, row in df.iterrows():
            # Verificar si la fila parece contener una cédula
            if self.validator.is_valid_cedula_row(row):
                valid_indices.append(idx)
            else:
                # Si no se detecta cédula, verificar si hay algún valor que parezca una cédula en cualquier columna
                for col in df.columns:
                    value = row[col]
                    if pd.notna(value) and isinstance(value, (int, float, str)) and str(value).strip().isdigit() and 5 <= len(str(value).strip()) <= 15:
                        valid_indices.append(idx)
                        break
            
            # Si no se encontró una cédula, verificar si la fila tiene suficientes datos para ser válida
            if idx not in valid_indices and len([x for x in row if pd.notna(x)]) >= 2:
                valid_indices.append(idx)
        
        if valid_indices:
            filtered_df = df.loc[valid_indices].reset_index(drop=True)
            self.logger.logger.info(f"📊 Filtradas {len(filtered_df)} filas válidas de {len(df)} totales")
            return filtered_df
        
        # Si no se encontraron filas válidas, devolver las primeras filas que no estén completamente vacías
        non_empty_rows = df[df.notna().any(axis=1)]
        if not non_empty_rows.empty:
            self.logger.logger.warning("No se detectaron cédulas válidas, usando primeras filas no vacías")
            return non_empty_rows.head(10)  # Limitar a las primeras 10 filas
            
        return pd.DataFrame()  # DataFrame vacío si no se encontraron filas con datos
    
    def _apply_no_header_mapping(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Aplica el mapeo de columnas para Excel sin encabezados.
        Detecta automáticamente si la primera columna es un ID o la cédula.
        
        Args:
            df: DataFrame sin encabezados
            
        Returns:
            DataFrame con columnas mapeadas
        """
        # Obtener las primeras filas para analizar el contenido
        sample_rows = df.head(5)
        
        # Verificar si la primera columna parece ser un ID (números secuenciales)
        first_col = sample_rows.iloc[:, 0] if not sample_rows.empty else None
        is_first_col_id = False
        
        if first_col is not None and len(first_col) > 0:
            # Verificar si los valores de la primera columna parecen ser numéricos secuenciales
            try:
                first_col_numeric = pd.to_numeric(first_col, errors='coerce')
                is_sequential = (first_col_numeric.diff().dropna() == 1).all()
                is_first_col_id = is_sequential or (first_col_numeric == range(1, len(first_col_numeric) + 1)).all()
            except:
                pass
        
        # Obtener el mapeo de columnas base
        column_mapping = self.alias_definitions.get_no_header_column_mapping()
        
        # Si la primera columna es un ID, la ignoramos y mapeamos las columnas siguientes
        if is_first_col_id:
            self.logger.logger.info("📋 Primera columna detectada como ID, ignorando en el mapeo")
            # Creamos un mapeo que ignore la primera columna (columna 0)
            adjusted_mapping = {}
            for k, v in column_mapping.items():
                if k + 1 < len(df.columns):
                    adjusted_mapping[k + 1] = v
        else:
            # Si no hay ID, usamos el mapeo tal cual
            adjusted_mapping = {k: v for k, v in column_mapping.items() 
                             if k < len(df.columns)}
        
        # Crear nuevas columnas basadas en el mapeo
        new_columns = {}
        for col_index, canonical_name in adjusted_mapping.items():
            if col_index < len(df.columns):
                new_columns[canonical_name] = df.iloc[:, col_index]
        
        # Verificar que tengamos al menos la cédula mapeada
        if 'cedula' not in new_columns and len(df.columns) > 0:
            # Si no se pudo mapear la cédula, intentar con la primera columna disponible
            first_col = 0 if not is_first_col_id else 1
            if first_col < len(df.columns):
                new_columns['cedula'] = df.iloc[:, first_col]
                self.logger.logger.warning(f"⚠️ No se pudo mapear la cédula, usando columna {first_col}")
        
        # Crear nuevo DataFrame con las columnas mapeadas
        if new_columns:
            mapped_df = pd.DataFrame(new_columns)
            self.logger.logger.info(f"🔄 Aplicado mapeo sin encabezados. Columnas mapeadas: {list(new_columns.keys())}")
            return mapped_df
        
        return pd.DataFrame()