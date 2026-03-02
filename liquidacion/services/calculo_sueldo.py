"""
Servicio para calcular el sueldo neto de un afiliado basado en parámetros como:
- Grado de escalafón: Determina el salario base desde TablaSalarial
- Cargo desempeñado: Aplica bonificaciones según el cargo (rector 25%, decano 15%, etc.)
- Años de servicio: Bonificaciones por antigüedad (2% a 12% según años)
- Nivel educativo: Bonificaciones por títulos (doctorado 15%, maestría 10%, etc.)
- Otros factores adicionales: Bonificaciones personalizadas

Este servicio reemplaza la importación directa de sueldos desde Excel,
calculando automáticamente basado en los parámetros del afiliado.

Clases principales:
- CalculadorSueldo: Clase principal para cálculos de sueldo
- Funciones utilitarias para cálculos masivos y por cédula

Ejemplo de uso:
    calculadora = CalculadorSueldo(afiliado, 2025)
    resultado = calculadora.calcular_sueldo_neto()
    sueldo, created, calculo = calculadora.crear_o_actualizar_sueldo()
"""

from django.db import transaction
from decimal import Decimal
from django.db import models
from liquidacion.models import TablaSalarial, Sueldo, Aporte
from afiliados.models import Afiliado
import logging

logger = logging.getLogger(__name__)


class CalculadorSueldo:
    """
    Calculadora de sueldos basada en parámetros del afiliado.
    
    Esta clase centraliza toda la lógica de cálculo de sueldos, aplicando
    bonificaciones según cargo, antigüedad, educación y otros factores.
    
    Attributes:
        afiliado (Afiliado): Instancia del afiliado para calcular sueldo
        anio (int): Año para el cual se calcula el sueldo
        
    Constants:
        BONIFICACIONES_CARGO: Dict con porcentajes por cargo desempeñado
        BONIFICACIONES_ANTIGUEDAD: Lista de tuplas (años_minimos, porcentaje)
        BONIFICACIONES_EDUCACION: Dict con porcentajes por nivel educativo
    """
    
    # Bonificaciones por cargo desempeñado (porcentajes sobre salario base)
    BONIFICACIONES_CARGO = {
        'rector': Decimal('25.0'),
        'vicerrector': Decimal('20.0'),
        'decano': Decimal('15.0'),
        'vicedecano': Decimal('12.0'),
        'director_departamento': Decimal('10.0'),
        'coordinador_programa': Decimal('8.0'),
        'coordinador_area': Decimal('6.0'),
        'jefe_laboratorio': Decimal('5.0'),
        'secretario_academico': Decimal('4.0'),
        'ninguno': Decimal('0.0'),
    }
    
    # Bonificaciones por años de servicio (porcentajes sobre salario base)
    BONIFICACIONES_ANTIGUEDAD = [
        (5, Decimal('2.0')),    # 5+ años: 2%
        (10, Decimal('4.0')),   # 10+ años: 4%
        (15, Decimal('6.0')),   # 15+ años: 6%
        (20, Decimal('8.0')),   # 20+ años: 8%
        (25, Decimal('10.0')),  # 25+ años: 10%
        (30, Decimal('12.0')),  # 30+ años: 12%
    ]
    
    # Bonificaciones por nivel educativo (porcentajes sobre salario base)
    BONIFICACIONES_EDUCACION = {
        'doctorado': Decimal('15.0'),
        'maestria': Decimal('10.0'),
        'especializacion': Decimal('5.0'),
        'pregrado': Decimal('0.0'),
    }
    
    def __init__(self, afiliado, anio=None):
        """
        Inicializa la calculadora para un afiliado específico.
        
        Configura los datos básicos necesarios para realizar los cálculos
        de sueldo del afiliado en el año especificado.
        
        Args:
            afiliado (Afiliado): Instancia del modelo Afiliado con todos sus datos
            anio (int, optional): Año para el cálculo. Si no se especifica, usa 2025
        """
        self.afiliado = afiliado
        self.anio = anio or 2025
        
    def obtener_salario_base(self):
        """
        Obtiene el salario base según el grado de escalafón del afiliado.
        
        Busca en la tabla salarial el salario base correspondiente al grado
        del afiliado para el año especificado. Si no encuentra el grado o
        la tabla salarial, retorna 0 y registra un warning en los logs.
        
        Returns:
            Decimal: Salario base del grado, o 0 si no se encuentra
            
        Logs:
            - Warning si el afiliado no tiene grado definido
            - Warning si el grado no es válido
            - Warning si no existe tabla salarial para el grado/año
        """
        if not hasattr(self.afiliado, 'grado_escalafon') or not self.afiliado.grado_escalafon:
            logger.warning(f"Afiliado {getattr(self.afiliado, 'cedula', 'sin cédula')} no tiene grado de escalafón definido")
            return Decimal('0')
        
        grado = str(self.afiliado.grado_escalafon).strip()
        
        # Validar que el grado sea válido
        if not self._es_grado_escalafon_valido(grado):
            logger.warning(f"Grado de escalafón inválido para afiliado {getattr(self.afiliado, 'cedula', 'sin cédula')}: {grado}")
            return Decimal('0')
            
        try:
            # Normalizar el grado (mayúsculas para letras)
            grado = grado.upper() if grado.upper() in ['A', 'B'] else grado
            
            tabla = TablaSalarial.objects.get(anio=self.anio, grado=grado)
            logger.debug(f"Tabla salarial encontrada para grado {grado}, año {self.anio}: {tabla.salario_base}")
            return tabla.salario_base
            
        except TablaSalarial.DoesNotExist:
            logger.warning(f"No se encontró tabla salarial para grado {grado} en año {self.anio}")
            return Decimal('0')
    
    def _es_grado_escalafon_valido(self, grado):
        """
        Valida si un grado de escalafón es válido.
        
        Args:
            grado (str): Grado a validar
            
        Returns:
            bool: True si el grado es válido, False en caso contrario
        """
        if not grado:
            return False
            
        # Grados válidos: 1-14, A, B
        if grado.isdigit():
            return 1 <= int(grado) <= 14
        return grado.upper() in ['A', 'B']
    
    def calcular_bonificacion_cargo(self, cargo=None):
        """
        Calcula la bonificación por cargo desempeñado del afiliado.
        
        Si no se especifica un cargo, analiza los campos 'cargo_desempeñado' 
        y 'ultimo_cargo' del afiliado buscando coincidencias con los cargos
        definidos en BONIFICACIONES_CARGO. Usa búsqueda de texto para detectar
        palabras clave como 'rector', 'decano', etc.
        
        Args:
            cargo (str, optional): Cargo específico a evaluar. Si no se especifica,
                                 busca automáticamente en los campos del afiliado
            
        Returns:
            Decimal: Porcentaje de bonificación por cargo (0.0 a 25.0)
            
        Example:
            Si el afiliado tiene 'ultimo_cargo' = 'Decano de Facultad',
            retornará Decimal('15.0') correspondiente al 15% de bonificación
        """
        # Si se especifica un cargo, usarlo directamente
        if cargo:
            cargo = str(cargo).lower().strip()
            # Intentar con el cargo exacto primero
            if cargo in self.BONIFICACIONES_CARGO:
                return self.BONIFICACIONES_CARGO[cargo]
            # Intentar reemplazar espacios por guiones bajos
            cargo_con_guion = cargo.replace(' ', '_')
            if cargo_con_guion in self.BONIFICACIONES_CARGO:
                return self.BONIFICACIONES_CARGO[cargo_con_guion]
            return Decimal('0')
        
        # Obtener cargo del afiliado con manejo de valores nulos
        cargo_text = (getattr(self.afiliado, 'cargo_desempeñado', '') or '').lower().strip()
        ultimo_cargo = (getattr(self.afiliado, 'ultimo_cargo', '') or '').lower().strip()
        
        logger.debug(f'Buscando bonificación por cargo en: "{cargo_text}" o "{ultimo_cargo}"')
        
        # Primero verificar si hay una coincidencia exacta en los cargos del sistema
        for cargo_key in self.BONIFICACIONES_CARGO:
            # Convertir el cargo_key a formato legible (reemplazar guiones bajos por espacios)
            cargo_legible = cargo_key.replace('_', ' ')
            
            # Buscar coincidencias exactas primero (ignorando mayúsculas/minúsculas)
            if (cargo_key.lower() == cargo_text or 
                cargo_key.lower() == ultimo_cargo or
                cargo_legible.lower() == cargo_text or 
                cargo_legible.lower() == ultimo_cargo):
                logger.debug(f'Coincidencia exacta encontrada: {cargo_key} = {self.BONIFICACIONES_CARGO[cargo_key]}%')
                return self.BONIFICACIONES_CARGO[cargo_key]
        
        # Si no hay coincidencia exacta, buscar subcadenas
        for cargo_key, porcentaje in self.BONIFICACIONES_CARGO.items():
            if cargo_key == 'ninguno':
                continue
                
            cargo_legible = cargo_key.replace('_', ' ')
            
            # Buscar tanto la versión con guión bajo como con espacio
            if (cargo_key in cargo_text or 
                cargo_key in ultimo_cargo or
                cargo_legible in cargo_text or 
                cargo_legible in ultimo_cargo):
                logger.debug(f'Coincidencia parcial encontrada: {cargo_key} = {porcentaje}%')
                return porcentaje
        
        logger.debug('No se encontró coincidencia para bonificación por cargo')
        return self.BONIFICACIONES_CARGO['ninguno']
    
    def calcular_bonificacion_antiguedad(self):
        """
        Calcula la bonificación por años de servicio del afiliado.
        
        Evalúa el campo 'anos_servicio' del afiliado y aplica
        el porcentaje de bonificación correspondiente según la escala:
        - 5+ años: 2%, 10+ años: 4%, 15+ años: 6%, 20+ años: 8%,
        - 25+ años: 10%, 30+ años: 12%
        
        Busca el mayor porcentaje aplicable (el afiliado califica para
        el nivel más alto que cumpla).
        
        Returns:
            Decimal: Porcentaje de bonificación por antigüedad (0.0 a 12.0)
            
        Example:
            Si el afiliado tiene 18 años de servicio, retornará Decimal('6.0')
            correspondiente al 6% (califica para 15+ años pero no para 20+)
        """
        try:
            # Usar getattr con valor por defecto 0 si el campo no existe o es None
            años_servicio = int(getattr(self.afiliado, 'anos_servicio', 0) or 0)
            
            # Asegurarse de que los años de servicio no sean negativos
            años_servicio = max(0, años_servicio)
            
            logger.debug(f'Cálculo de bonificación por antigüedad para {getattr(self.afiliado, "cedula", "sin cédula")}: {años_servicio} años')
            
            # Buscar el mayor porcentaje aplicable
            for años_minimos, porcentaje in reversed(self.BONIFICACIONES_ANTIGUEDAD):
                if años_servicio >= años_minimos:
                    logger.debug(f'- Aplica bonificación de {porcentaje}% para {años_minimos}+ años')
                    return porcentaje
                    
            logger.debug('- No aplica bonificación por antigüedad')
            return Decimal('0')
            
        except (ValueError, TypeError) as e:
            logger.error(f'Error al calcular bonificación por antigüedad para {getattr(self.afiliado, "cedula", "sin cédula")}: {str(e)}')
            return Decimal('0')
    
    def calcular_bonificacion_educacion(self):
        """
        Calcula la bonificación por nivel educativo del afiliado.
        
        Analiza los campos 'titulo_posgrado', 'estudios_posgrado' y 'otros_titulos'
        del afiliado buscando palabras clave que indiquen el nivel educativo:
        - 'doctorado', 'phd': 15% de bonificación
        - 'maestria', 'master', 'magister': 10% de bonificación  
        - 'especializacion', 'especialista': 5% de bonificación
        - Solo pregrado o sin títulos: 0% de bonificación
        
        Aplica el mayor porcentaje encontrado (si tiene maestría y doctorado,
        aplica el 15% del doctorado).
        
        Returns:
            Decimal: Porcentaje de bonificación por educación (0.0 a 15.0)
            
        Example:
            Si 'titulo_posgrado' contiene 'Maestría en Educación',
            retornará Decimal('10.0') correspondiente al 10%
        """
        # Verificar títulos de posgrado
        titulo_posgrado = (self.afiliado.titulo_posgrado or '').lower()
        estudios_posgrado = (self.afiliado.estudios_posgrado or '').lower()
        otros_titulos = (self.afiliado.otros_titulos or '').lower()
        
        texto_completo = f"{titulo_posgrado} {estudios_posgrado} {otros_titulos}"
        
        if 'doctorado' in texto_completo or 'phd' in texto_completo:
            return self.BONIFICACIONES_EDUCACION['doctorado']
        elif 'maestria' in texto_completo or 'master' in texto_completo or 'magister' in texto_completo:
            return self.BONIFICACIONES_EDUCACION['maestria']
        elif 'especializacion' in texto_completo or 'especialista' in texto_completo:
            return self.BONIFICACIONES_EDUCACION['especializacion']
        
        return self.BONIFICACIONES_EDUCACION['pregrado']
    
    def calcular_sueldo_neto(self, cargo_especifico=None, bonificaciones_adicionales=None):
        """
        Calcula el sueldo neto total del afiliado aplicando todas las bonificaciones.
        
        Este es el método principal que coordina todos los cálculos:
        1. Verifica si el afiliado debe tener salario
        2. Obtiene el salario base según el grado de escalafón
        3. Calcula bonificación por cargo desempeñado
        4. Calcula bonificación por años de servicio
        5. Calcula bonificación por nivel educativo
        6. Aplica bonificaciones adicionales si se especifican
        7. Suma todo para obtener el sueldo bruto y neto
        
        Args:
            cargo_especifico (str, optional): Cargo específico para bonificación.
                                            Si no se especifica, usa los campos del afiliado
            bonificaciones_adicionales (dict, optional): Bonificaciones extra en formato
                                                        {concepto: porcentaje}
                
        Returns:
            dict: Diccionario completo con el desglose del cálculo conteniendo:
                - salario_base: Salario base del grado (0 si no aplica)
                - bonificacion_cargo: Monto por cargo (0 si no aplica)
                - bonificacion_antiguedad: Monto por años de servicio (0 si no aplica)
                - bonificacion_educacion: Monto por nivel educativo (0 si no aplica)
                - bonificaciones_adicionales: Monto de bonificaciones extra (0 si no aplica)
                - sueldo_bruto: Suma de salario base + todas las bonificaciones (0 si no aplica)
                - sueldo_neto: Sueldo final (0 si no aplica)
                - desglose: Detalle de porcentajes y montos por concepto
                - error: Mensaje de error si no se puede calcular o si no aplica salario
        """
        # Validar que el afiliado tenga la información necesaria
        if not hasattr(self.afiliado, 'grado_escalafon') or not self.afiliado.grado_escalafon:
            error_msg = 'El afiliado no tiene grado de escalafón definido'
            logger.warning(f'Advertencia en cálculo de sueldo: {error_msg}')
            return {
                'salario_base': Decimal('0'),
                'bonificacion_cargo': Decimal('0'),
                'bonificacion_antiguedad': Decimal('0'),
                'bonificacion_educacion': Decimal('0'),
                'bonificaciones_adicionales': Decimal('0'),
                'sueldo_bruto': Decimal('0'),
                'sueldo_neto': Decimal('0'),
                'desglose': 'No aplica cálculo de sueldo',
                'error': error_msg
            }
            
        # Verificar si el afiliado debería tener un salario calculado
        if not self.afiliado.activo:
            error_msg = 'El afiliado no está activo en el sistema'
            logger.warning(f'Advertencia en cálculo de sueldo: {error_msg}')
            return {
                'salario_base': Decimal('0'),
                'bonificacion_cargo': Decimal('0'),
                'bonificacion_antiguedad': Decimal('0'),
                'bonificacion_educacion': Decimal('0'),
                'bonificaciones_adicionales': Decimal('0'),
                'sueldo_bruto': Decimal('0'),
                'sueldo_neto': Decimal('0'),
                'desglose': 'Afiliado inactivo - No aplica sueldo',
                'error': error_msg
            }
            
        try:
            # 1. Obtener salario base
            salario_base = self.obtener_salario_base()
            if salario_base == 0:
                error_msg = 'No se pudo determinar el salario base. Verifique el grado de escalafón y las tablas salariales.'
                logger.error(error_msg)
                return {'error': error_msg}
            
            logger.debug(f'Cálculo de sueldo para afiliado {getattr(self.afiliado, "cedula", "sin cédula")}:')
            logger.debug(f'- Grado: {self.afiliado.grado_escalafon}')
            logger.debug(f'- Salario base: {salario_base}')
            
            # 2. Calcular bonificaciones
            bonif_cargo_pct = self.calcular_bonificacion_cargo(cargo_especifico)
            bonif_antiguedad_pct = self.calcular_bonificacion_antiguedad()
            bonif_educacion_pct = self.calcular_bonificacion_educacion()
            
            logger.debug(f'- Bonificación por cargo: {bonif_cargo_pct}%')
            logger.debug(f'- Bonificación por antigüedad: {bonif_antiguedad_pct}%')
            logger.debug(f'- Bonificación por educación: {bonif_educacion_pct}%')
            
            # 3. Calcular montos de bonificaciones
            bonif_cargo = (salario_base * bonif_cargo_pct) / 100
            bonif_antiguedad = (salario_base * bonif_antiguedad_pct) / 100
            bonif_educacion = (salario_base * bonif_educacion_pct) / 100
            
            # 4. Procesar bonificaciones adicionales
            bonif_adicionales = {}
            bonif_adicionales_total = Decimal('0')
            
            if bonificaciones_adicionales and isinstance(bonificaciones_adicionales, dict):
                logger.debug(f'Procesando {len(bonificaciones_adicionales)} bonificaciones adicionales')
                for concepto, porcentaje in bonificaciones_adicionales.items():
                    try:
                        pct = Decimal(str(porcentaje))
                        monto = (salario_base * pct) / 100
                        bonif_adicionales[concepto] = {
                            'porcentaje': float(pct),
                            'monto': float(monto)
                        }
                        bonif_adicionales_total += monto
                        logger.debug(f'  - {concepto}: {pct}% = {monto}')
                    except (ValueError, TypeError, decimal.InvalidOperation) as e:
                        error_msg = f'Error procesando bonificación adicional {concepto}: {e}'
                        logger.warning(error_msg)
                        # Continuar con el resto de bonificaciones
            
            # 5. Calcular totales
            total_bonificaciones = bonif_cargo + bonif_antiguedad + bonif_educacion + bonif_adicionales_total
            sueldo_bruto = salario_base + total_bonificaciones
            
            logger.debug(f'- Total bonificaciones: {total_bonificaciones}')
            logger.debug(f'- Sueldo bruto: {sueldo_bruto}')
            
            # 6. Preparar desglose detallado
            desglose = {
                'salario_base': float(salario_base),
                'cargo': {
                    'porcentaje': float(bonif_cargo_pct),
                    'monto': float(bonif_cargo)
                },
                'antiguedad': {
                    'porcentaje': float(bonif_antiguedad_pct),
                    'monto': float(bonif_antiguedad)
                },
                'educacion': {
                    'porcentaje': float(bonif_educacion_pct),
                    'monto': float(bonif_educacion)
                },
                'adicionales': bonif_adicionales,
                'total_bonificaciones': float(total_bonificaciones)
            }
            
            resultado = {
                'salario_base': float(salario_base),
                'bonificacion_cargo': float(bonif_cargo),
                'bonificacion_antiguedad': float(bonif_antiguedad),
                'bonificacion_educacion': float(bonif_educacion),
                'bonificaciones_adicionales': float(bonif_adicionales_total),
                'sueldo_bruto': float(sueldo_bruto),
                'sueldo_neto': float(sueldo_bruto),  # Por ahora es igual al bruto
                'desglose': desglose
            }
            
            logger.info(f'Cálculo de sueldo completado para afiliado {getattr(self.afiliado, "cedula", "sin cédula")}.')
            logger.debug(f'Resultado detallado: {resultado}')
            
            return resultado
            
        except Exception as e:
            error_msg = f'Error al calcular sueldo para afiliado {getattr(self.afiliado, "cedula", "sin cédula")}: {str(e)}'
            logger.exception(error_msg)
            return {'error': error_msg}
    
    def _guardar_bonificaciones(self, sueldo, desglose):
        """
        Guarda las bonificaciones en la tabla BonificacionPago.
        
        Args:
            sueldo (Sueldo): Instancia del modelo Sueldo
            desglose (dict): Diccionario con el desglose de bonificaciones
        """
        from liquidacion.models import BonificacionPago
        
        try:
            # Eliminar bonificaciones anteriores para este sueldo
            BonificacionPago.objects.filter(sueldo=sueldo).delete()
            
            # Guardar bonificación por cargo
            if desglose['cargo']['monto'] > 0:
                BonificacionPago.objects.create(
                    sueldo=sueldo,
                    anio=self.anio,
                    descripcion=f"Bonificación por cargo ({desglose['cargo']['porcentaje']}%)",
                    porcentaje=float(desglose['cargo']['porcentaje']),
                    monto=float(desglose['cargo']['monto'])
                )
            
            # Guardar bonificación por antigüedad
            if desglose['antiguedad']['monto'] > 0:
                BonificacionPago.objects.create(
                    sueldo=sueldo,
                    anio=self.anio,
                    descripcion=f"Bonificación por antigüedad ({desglose['antiguedad']['porcentaje']}%)",
                    porcentaje=float(desglose['antiguedad']['porcentaje']),
                    monto=float(desglose['antiguedad']['monto'])
                )
            
            # Guardar bonificación por educación
            if desglose['educacion']['monto'] > 0:
                BonificacionPago.objects.create(
                    sueldo=sueldo,
                    anio=self.anio,
                    descripcion=f"Bonificación por nivel educativo ({desglose['educacion']['porcentaje']}%)",
                    porcentaje=float(desglose['educacion']['porcentaje']),
                    monto=float(desglose['educacion']['monto'])
                )
            
            # Guardar bonificaciones adicionales
            for concepto, datos in desglose['adicionales'].items():
                if datos['monto'] > 0:
                    BonificacionPago.objects.create(
                        sueldo=sueldo,
                        anio=self.anio,
                        descripcion=f"Bonificación adicional: {concepto} ({datos['porcentaje']}%)",
                        porcentaje=float(datos['porcentaje']),
                        monto=float(datos['monto'])
                    )
                    
        except Exception as e:
            logger.error(f"Error guardando bonificaciones para sueldo {sueldo.id}: {str(e)}")
            raise
    
    def crear_o_actualizar_sueldo(self, cargo_especifico=None, bonificaciones_adicionales=None):
        """
        Crea o actualiza el registro de sueldo del afiliado en la base de datos.
        
        Realiza el cálculo completo del sueldo y luego:
        1. Busca o crea la tabla salarial correspondiente al grado/año
        2. Crea o actualiza el registro de Sueldo del afiliado
        3. Guarda el desglose de bonificaciones en BonificacionPago
        4. Los aportes se recalculan automáticamente via signals de Django
        
        Args:
            cargo_especifico (str, optional): Cargo específico para bonificación
            bonificaciones_adicionales (dict, optional): Bonificaciones extra
            
        Returns:
            tuple: (Sueldo instance, created boolean, calculo dict)
                - Sueldo instance: El objeto Sueldo creado o actualizado
                - created boolean: True si se creó nuevo, False si se actualizó
                - calculo dict: El desglose completo del cálculo realizado
                
        Raises:
            Exception: Si hay errores en el cálculo o guardado en base de datos
        """
        if not self.afiliado.grado_escalafon:
            error_msg = "El afiliado no tiene un grado de escalafón definido"
            logger.error(f"Error calculando sueldo para {self.afiliado.cedula}: {error_msg}")
            return None, False, {'error': error_msg}
        
        # Calcular el sueldo neto con todas las bonificaciones
        calculo = self.calcular_sueldo_neto(cargo_especifico, bonificaciones_adicionales)
        
        if 'error' in calculo:
            logger.error(f"Error calculando sueldo para {self.afiliado.cedula}: {calculo['error']}")
            return None, False, calculo
        
        try:
            with transaction.atomic():
                # Buscar o crear tabla salarial
                tabla_salarial, _ = TablaSalarial.objects.get_or_create(
                    anio=self.anio,
                    grado=self.afiliado.grado_escalafon,
                    defaults={'salario_base': calculo['salario_base']}
                )
                
                # Crear o actualizar sueldo
                sueldo, created = Sueldo.objects.update_or_create(
                    afiliado=self.afiliado,
                    anio=self.anio,
                    defaults={
                        'sueldo_neto': calculo['sueldo_neto'],
                        'tabla_salarial': tabla_salarial
                    }
                )
                
                # Guardar el desglose de bonificaciones
                self._guardar_bonificaciones(sueldo, calculo['desglose'])
                
                logger.info(f"Sueldo {'creado' if created else 'actualizado'} para {self.afiliado.cedula} - "
                          f"Año: {self.anio}, Sueldo neto: {calculo['sueldo_neto']:,.2f}")
                
                return sueldo, created, calculo
                
        except Exception as e:
            error_msg = f"Error al guardar el sueldo para {self.afiliado.cedula}: {str(e)}"
            logger.exception(error_msg)
            return None, False, {'error': error_msg}


def calcular_sueldo_afiliado(cedula, anio=None, cargo_especifico=None, bonificaciones_adicionales=None):
    """
    Función de conveniencia para calcular el sueldo de un afiliado por cédula.
    
    Busca el afiliado por cédula y realiza el cálculo de sueldo usando
    la clase CalculadorSueldo. Es útil para cálculos rápidos sin necesidad
    de instanciar objetos manualmente.
    
    Args:
        cedula (str): Cédula del afiliado a calcular
        anio (int, optional): Año para el cálculo. Por defecto usa el año actual
        cargo_especifico (str, optional): Cargo específico para bonificación
        bonificaciones_adicionales (dict, optional): Bonificaciones extra {concepto: porcentaje}
        
    Returns:
        dict: Resultado del cálculo con el mismo formato que calcular_sueldo_neto(),
              o dict con clave 'error' si el afiliado no existe
              
    Example:
        resultado = calcular_sueldo_afiliado('12345678', 2025)
        if 'error' not in resultado:
            print(f"Sueldo: ${resultado['sueldo_neto']}")
    """
    try:
        afiliado = Afiliado.objects.get(cedula=cedula)
        calculadora = CalculadorSueldo(afiliado, anio)
        return calculadora.calcular_sueldo_neto(cargo_especifico, bonificaciones_adicionales)
    except Afiliado.DoesNotExist:
        return {'error': f'Afiliado con cédula {cedula} no encontrado'}


def recalcular_sueldos_masivo(anio=None, filtros=None):
    """
    Recalcula los sueldos de múltiples afiliados de forma masiva.
    
    Procesa todos los afiliados activos (o los filtrados) y recalcula
    sus sueldos usando el sistema de cálculo automático. Útil para
    actualizaciones masivas cuando cambian las tablas salariales o
    las reglas de bonificación.
    
    Args:
        anio (int, optional): Año para el cálculo. Por defecto usa 2025
        filtros (dict, optional): Filtros adicionales para el queryset de afiliados.
                                Ejemplo: {'grado_escalafon': '14'} para solo grado 14
        
    Returns:
        dict: Resumen del proceso conteniendo:
            - procesados: Número total de afiliados procesados exitosamente
            - creados: Número de nuevos registros de sueldo creados
            - actualizados: Número de registros de sueldo actualizados
            - errores: Lista de errores con formato [{'cedula': str, 'error': str}]
            
    Example:
        # Recalcular todos los sueldos del 2025
        resultado = recalcular_sueldos_masivo(2025)
        
        # Solo afiliados de grado 14
        resultado = recalcular_sueldos_masivo(2025, {'grado_escalafon': '14'})
    """
    anio = anio or 2025
    
    # Aplicar filtros
    queryset = Afiliado.objects.filter(activo=True)
    if filtros:
        queryset = queryset.filter(**filtros)
    
    resultados = {
        'procesados': 0,
        'creados': 0,
        'actualizados': 0,
        'errores': []
    }
    
    for afiliado in queryset:
        try:
            calculadora = CalculadorSueldo(afiliado, anio)
            sueldo, created, calculo = calculadora.crear_o_actualizar_sueldo()
            
            if sueldo:
                resultados['procesados'] += 1
                if created:
                    resultados['creados'] += 1
                else:
                    resultados['actualizados'] += 1
            else:
                resultados['errores'].append({
                    'cedula': afiliado.cedula,
                    'error': calculo.get('error', 'Error desconocido')
                })
                
        except Exception as e:
            logger.exception(f"Error procesando afiliado {afiliado.cedula}: {e}")
            resultados['errores'].append({
                'cedula': afiliado.cedula,
                'error': str(e)
            })
    
    return resultados
