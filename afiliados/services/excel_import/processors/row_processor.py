from typing import Dict, Any, Optional
import pandas as pd
from django.db import transaction

from afiliados.models import Afiliado
from liquidacion.models import Bonificacion
from liquidacion.services.calculo_sueldo_decretos import calcular_sueldo_total_docente

from ..utils.data_converters import DataConverters
from ..core.logger_manager import ImportLoggerManager


class RowProcessor:
    """
    Procesador de filas individuales para crear/actualizar afiliados.
    """
    
    def __init__(self, logger_manager: ImportLoggerManager):
        self.logger = logger_manager
        self.converters = DataConverters()
    
    def process_row(self, row: pd.Series, row_index: int) -> Dict[str, Any]:
        """
        Procesa una fila individual del DataFrame.
        
        Args:
            row: Fila del DataFrame
            row_index: Índice de la fila
            
        Returns:
            Dict con resultado del procesamiento
        """
        result = {
            'success': False,
            'error': None,
            'cedula': None,
            'created': False,
            'salary_processed': False,
            'bonus_processed': False
        }
        
        try:
            # Procesar cédula con validación robusta
            raw_cedula = row.get('cedula', None)
            
            # Validar que la cédula sea un valor numérico
            if raw_cedula is None or pd.isna(raw_cedula):
                result['error'] = "Cédula no proporcionada"
                return result
                
            # Verificar si el valor parece ser un nombre en lugar de una cédula
            if isinstance(raw_cedula, str) and any(c.isalpha() for c in raw_cedula):
                result['error'] = f"Valor de cédula inválido (parece ser un nombre): {raw_cedula}"
                return result
                
            # Intentar convertir a cédula
            cedula = self.converters.safe_cedula_conversion(raw_cedula)
            
            if not cedula:
                result['error'] = f"Cédula vacía o inválida. Valor original: {raw_cedula}"
                return result
                
            # Validar longitud de la cédula
            if len(cedula) < 6 or len(cedula) > 15:  # Ajustar según los requisitos
                result['error'] = f"Longitud de cédula inválida: {cedula} (longitud: {len(cedula)})"
                return result
            
            result['cedula'] = cedula
            
            # Procesar afiliado
            afiliado, created = self._process_afiliado(row, cedula)
            result['created'] = created
            
            # Procesar salario si es posible
            salary_processed = self._process_salary(afiliado, row)
            result['salary_processed'] = salary_processed
            
            # Procesar bonificación si existe
            bonus_processed = self._process_bonus(row)
            result['bonus_processed'] = bonus_processed
            
            result['success'] = True
            
            self.logger.log_row_success(
                row_index + 1, 
                cedula, 
                "CREADO" if created else "ACTUALIZADO"
            )
            
        except Exception as e:
            result['error'] = f"Error general procesando fila: {str(e)}"
            self.logger.log_row_error(row_index + 1, result['error'], result.get('cedula'))
        
        return result
    
    def _process_afiliado(self, row: pd.Series, cedula: str) -> tuple[Afiliado, bool]:
        """
        Crea o actualiza un afiliado con los datos de la fila.
        
        Args:
            row: Fila con datos del afiliado
            cedula: Cédula del afiliado
            
        Returns:
            tuple: (afiliado, fue_creado)
        """
        # Preparar datos del afiliado con conversión segura
        defaults = {
            # Información básica
            'nombre_completo': self.converters.safe_string_conversion(row.get('nombre_completo', '')),
            
            # Información geográfica y personal
            'municipio': self.converters.safe_string_conversion(row.get('municipio', '')),
            'ciudad_de_nacimiento': self.converters.safe_string_conversion(row.get('ciudad_de_nacimiento', '')),
            'fecha_nacimiento': self.converters.safe_date_conversion(row.get('fecha_nacimiento')),
            'edad': self.converters.safe_int_conversion(row.get('edad')),
            'estado_civil': self.converters.safe_string_conversion(row.get('estado_civil', '')),
            'nombre_conyuge': self.converters.safe_string_conversion(row.get('nombre_conyuge', '')),
            'nombre_hijos': self.converters.safe_string_conversion(row.get('nombre_hijos', '')),
            
            # Información de contacto
            'direccion': self.converters.safe_string_conversion(row.get('direccion', '')),
            'telefono': self.converters.safe_string_conversion(row.get('telefono', '')),
            'email': self.converters.safe_string_conversion(row.get('email', '')),
            
            # Información profesional
            'grado_escalafon': self.converters.safe_string_conversion(row.get('grado_escalafon', '')),
            'cargo_desempenado': self.converters.safe_string_conversion(
                row.get('cargo_desempenado', row.get('cargos_desempenñados', ''))
            ),
            'fecha_ingreso': self.converters.safe_date_conversion(row.get('fecha_ingreso')),
            'anos_servicio': self.converters.safe_int_conversion(
                row.get('años_servicio', row.get('años_de_servicio_docente', 0))
            ),
            
            # Información académica
            'titulo_pregrado': self.converters.safe_string_conversion(row.get('titulo_pregrado', '')),
            'titulo_posgrado': self.converters.safe_string_conversion(row.get('titulo_posgrado', '')),
            'estudios_posgrado': self.converters.safe_string_conversion(row.get('estudios_posgrado', '')),
            'otros_titulos': self.converters.safe_string_conversion(row.get('otros_titulos', '')),
            
            # Estado
            'activo': bool(row.get('activo', True))
        }
        
        # Crear o actualizar afiliado
        existing_afiliado = Afiliado.objects.filter(cedula=cedula).first()
        if existing_afiliado:
            # Actualizar campos si han cambiado
            changed = False
            for field, value in defaults.items():
                old_value = getattr(existing_afiliado, field, None)
                if self._normalize_value(old_value) != self._normalize_value(value):
                    setattr(existing_afiliado, field, value)
                    changed = True
            
            if changed:
                existing_afiliado.save()
            
            return existing_afiliado, False
        else:
            # Crear nuevo afiliado
            afiliado = Afiliado.objects.create(cedula=cedula, **defaults)
            return afiliado, True
    
    def _process_salary(self, afiliado: Afiliado, row: pd.Series) -> bool:
        """
        Procesa el salario de un afiliado usando el sistema de decretos.
        
        Args:
            afiliado: Afiliado para procesar salario
            row: Fila con datos de salario
            
        Returns:
            bool: True si se procesó el salario exitosamente
            
        Raises:
            Exception: Si ocurre un error durante el procesamiento del salario
        """
        # Obtener datos necesarios para el cálculo
        escalafon = self.converters.safe_string_conversion(row.get('grado_escalafon', ''))
        cargo = self.converters.safe_string_conversion(row.get('cargo_desempenado', ''))
        titulo_academico = self.converters.safe_string_conversion(row.get('titulo_posgrado', ''))
        tipo_docente = 'docente'  # Valor por defecto
        
        # Calcular sueldo usando el sistema de decretos
        if not escalafon:  # Si no hay escalafón definido, no hay nada que procesar
            return False
            
        resultado = calcular_sueldo_total_docente(
            escalafon=escalafon,
            titulo_academico=titulo_academico,
            cargo=cargo,
            tipo_docente=tipo_docente,
            jornada='completa'  # Asumir jornada completa por defecto
        )
        
        sueldo_valor = float(resultado['sueldo_total'])
        
        # Crear o actualizar registro de sueldo
        if sueldo_valor > 0:
            sueldo, created, _ = afiliado.crear_o_actualizar_sueldo(
                anio=2025,  # Año actual
                cargo_especifico=cargo,
                bonificaciones_adicionales=None
            )
            return True
            
        return False
    
    def _process_bonus(self, row: pd.Series) -> bool:
        """
        Procesa bonificaciones desde la fila.
        
        Args:
            row: Fila con datos de bonificación
            
        Returns:
            bool: True si se procesó la bonificación exitosamente
            
        Raises:
            Exception: Si ocurre un error durante el procesamiento de la bonificación
        """
        if 'bonificacion' not in row or pd.isna(row.get('bonificacion')):
            return False
        
        anio = self.converters.safe_int_conversion(row.get('anio', 2025))
        descripcion = self.converters.safe_string_conversion(row.get('bonificacion', 'Bonificación'))
        porcentaje = self.converters.safe_float_conversion(row.get('porcentaje_bonificacion', 0))
        
        Bonificacion.objects.update_or_create(
            anio=anio,
            descripcion=descripcion,
            defaults={'porcentaje': porcentaje}
        )
        return True
    
    def _normalize_value(self, value: Any) -> str:
        """Normaliza un valor para comparación."""
        if value is None:
            return ''
        if isinstance(value, str):
            return value.strip()
        return str(value)
