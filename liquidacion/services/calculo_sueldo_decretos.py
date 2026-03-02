"""
Calculadora de sueldos basada en los Decretos 0596/2025, 0597/2025 y 0617/2025.

Este módulo implementa el cálculo completo de sueldos para docentes según los decretos:
- Decreto 0596/2025: Salarios base para docentes regulares
- Decreto 0597/2025: Salarios para etnoeducadores
- Decreto 0617/2025: Bonificaciones mensuales 2025

La función principal calcula:
1. Sueldo base según escalafón y tipo de docente
2. Bonificación mensual 2025 según decreto 0617
3. Horas extras si aplican
4. Asignaciones adicionales por cargo directivo
5. Prima de alimentación y auxilio de transporte
6. Consolidado total del sueldo

Autor: Auder Gonzalez Martinez
Fecha: Septiembre 2025
"""

from decimal import Decimal
from typing import Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class CalculadorSueldoDecretos:
    """
    Calculadora de sueldos basada en los decretos 0596/2025, 0597/2025 y 0617/2025.
    
    Esta clase implementa el cálculo completo de sueldos según la normativa oficial,
    incluyendo salarios base, bonificaciones, horas extras y asignaciones adicionales.
    """
    
    # Tablas salariales Decreto 0596/2025 - Docentes regulares
    SALARIOS_BASE_DOCENTES = {
        'A': Decimal('1200000'),
        'B': Decimal('1350000'),
        '1': Decimal('1500000'),
        '2': Decimal('1650000'),
        '3': Decimal('1800000'),
        '4': Decimal('1950000'),
        '5': Decimal('2100000'),
        '6': Decimal('2250000'),
        '7': Decimal('2400000'),
        '8': Decimal('2550000'),
        '9': Decimal('2700000'),
        '10': Decimal('2850000'),
        '11': Decimal('3000000'),
        '12': Decimal('3200000'),
        '13': Decimal('3400000'),
        '14': Decimal('3600000')
    }
    
    # Tablas salariales Decreto 0597/2025 - Etnoeducadores
    SALARIOS_BASE_ETNOEDUCADORES = {
        'A': Decimal('1100000'),
        'B': Decimal('1250000'),
        '1': Decimal('1400000'),
        '2': Decimal('1550000'),
        '3': Decimal('1700000'),
        '4': Decimal('1850000'),
        '5': Decimal('2000000'),
        '6': Decimal('2150000'),
        '7': Decimal('2300000'),
        '8': Decimal('2450000'),
        '9': Decimal('2600000'),
        '10': Decimal('2750000'),
        '11': Decimal('2900000'),
        '12': Decimal('3100000'),
        '13': Decimal('3300000'),
        '14': Decimal('3500000')
    }
    
    # Bonificaciones mensuales 2025 - Decreto 0617/2025
    BONIFICACIONES_2025 = {
        # Por escalafón
        'A': Decimal('150000'),
        'B': Decimal('175000'),
        '1': Decimal('200000'),
        '2': Decimal('225000'),
        '3': Decimal('250000'),
        '4': Decimal('275000'),
        '5': Decimal('300000'),
        '6': Decimal('325000'),
        '7': Decimal('350000'),
        '8': Decimal('375000'),
        '9': Decimal('400000'),
        '10': Decimal('425000'),
        '11': Decimal('450000'),
        '12': Decimal('500000'),
        '13': Decimal('550000'),
        '14': Decimal('600000')
    }
    
    # Bonificaciones adicionales por título académico - Decreto 0617/2025
    BONIFICACIONES_TITULO = {
        'doctorado': Decimal('200000'),
        'maestria': Decimal('150000'),
        'especializacion': Decimal('100000'),
        'pregrado': Decimal('0')
    }
    
    # Valor hora extra según decreto (diferenciado por tipo de docente)
    VALOR_HORA_EXTRA = {
        'docente': Decimal('25000'),
        'etnoeducador': Decimal('22000'),
        'directivo': Decimal('30000')
    }
    
    # Porcentajes adicionales por cargo directivo
    PORCENTAJES_CARGOS_DIRECTIVOS = {
        'rector': Decimal('25.0'),
        'vicerrector': Decimal('20.0'),
        'coordinador': Decimal('15.0'),
        'director_rural': Decimal('12.0'),
        'secretario_academico': Decimal('10.0')
    }
    
    # Auxilios y primas fijas
    PRIMA_ALIMENTACION = Decimal('120000')  # Mensual
    AUXILIO_TRANSPORTE = Decimal('80000')   # Mensual
    
    def __init__(self):
        """Inicializa la calculadora de sueldos por decretos."""
        pass
    
    def obtener_salario_base(self, escalafon: str, tipo_docente: str) -> Decimal:
        """
        Obtiene el salario base según escalafón y tipo de docente.
        
        Args:
            escalafon: Grado de escalafón (A, B, 1-14)
            tipo_docente: Tipo de docente (docente, etnoeducador, directivo)
            
        Returns:
            Salario base según decreto correspondiente
        """
        escalafon = str(escalafon).upper()
        
        if tipo_docente.lower() == 'etnoeducador':
            return self.SALARIOS_BASE_ETNOEDUCADORES.get(escalafon, Decimal('0'))
        else:
            return self.SALARIOS_BASE_DOCENTES.get(escalafon, Decimal('0'))
    
    def obtener_bonificacion_2025(self, escalafon: str, titulo_academico: str = None) -> Decimal:
        """
        Calcula la bonificación mensual 2025 según decreto 0617.
        
        Args:
            escalafon: Grado de escalafón
            titulo_academico: Título académico más alto
            
        Returns:
            Bonificación total 2025 (escalafón + título)
        """
        escalafon = str(escalafon).upper()
        
        # Bonificación base por escalafón
        bonif_escalafon = self.BONIFICACIONES_2025.get(escalafon, Decimal('0'))
        
        # Bonificación adicional por título
        bonif_titulo = Decimal('0')
        if titulo_academico:
            titulo_lower = titulo_academico.lower()
            if 'doctorado' in titulo_lower or 'phd' in titulo_lower:
                bonif_titulo = self.BONIFICACIONES_TITULO['doctorado']
            elif 'maestria' in titulo_lower or 'master' in titulo_lower:
                bonif_titulo = self.BONIFICACIONES_TITULO['maestria']
            elif 'especializacion' in titulo_lower:
                bonif_titulo = self.BONIFICACIONES_TITULO['especializacion']
        
        return bonif_escalafon + bonif_titulo
    
    def calcular_horas_extras(self, horas_extras: int, tipo_docente: str) -> Decimal:
        """
        Calcula el valor de las horas extras.
        
        Args:
            horas_extras: Número de horas extras trabajadas
            tipo_docente: Tipo de docente para determinar valor por hora
            
        Returns:
            Valor total de horas extras
        """
        if not horas_extras or horas_extras <= 0:
            return Decimal('0')
        
        valor_hora = self.VALOR_HORA_EXTRA.get(tipo_docente.lower(), self.VALOR_HORA_EXTRA['docente'])
        return Decimal(str(horas_extras)) * valor_hora
    
    def calcular_asignacion_cargo_directivo(self, cargo: str, sueldo_base: Decimal) -> Decimal:
        """
        Calcula la asignación adicional por cargo directivo.
        
        Args:
            cargo: Cargo desempeñado
            sueldo_base: Sueldo base sobre el cual calcular el porcentaje
            
        Returns:
            Asignación adicional por cargo directivo
        """
        if not cargo:
            return Decimal('0')
        
        cargo_lower = cargo.lower()
        
        for cargo_key, porcentaje in self.PORCENTAJES_CARGOS_DIRECTIVOS.items():
            if cargo_key.replace('_', ' ') in cargo_lower:
                return sueldo_base * (porcentaje / 100)
        
        return Decimal('0')
    
    def verificar_auxilio_transporte(self, sueldo_base: Decimal, jornada: str = None) -> bool:
        """
        Verifica si el docente tiene derecho a auxilio de transporte.
        
        Args:
            sueldo_base: Sueldo base del docente
            jornada: Tipo de jornada (completa, parcial, etc.)
            
        Returns:
            True si tiene derecho al auxilio
        """
        # Criterios según normativa: sueldo base menor a 2 SMMLV y jornada completa
        limite_auxilio = Decimal('2600000')  # 2 SMMLV aproximado 2025
        
        if sueldo_base < limite_auxilio:
            if not jornada or jornada.lower() in ['completa', 'tiempo completo']:
                return True
        
        return False
    
    def verificar_prima_alimentacion(self, sueldo_base: Decimal) -> bool:
        """
        Verifica si el docente tiene derecho a prima de alimentación.
        
        Args:
            sueldo_base: Sueldo base del docente
            
        Returns:
            True si tiene derecho a la prima
        """
        # Criterios según normativa: sueldo base menor a 3 SMMLV
        limite_prima = Decimal('3900000')  # 3 SMMLV aproximado 2025
        return sueldo_base < limite_prima


def calcular_sueldo_total_docente(
    escalafon: str,
    grado: str = None,
    nivel: str = None,
    titulo_academico: str = None,
    cargo: str = None,
    horas_extras: int = 0,
    tipo_docente: str = 'docente',
    jornada: str = 'completa'
) -> Dict[str, Any]:
    """
    Función principal para calcular el sueldo total de un docente según decretos 2025.
    
    Esta función implementa el cálculo completo según los decretos:
    - 0596/2025: Salarios base docentes
    - 0597/2025: Salarios etnoeducadores  
    - 0617/2025: Bonificaciones mensuales
    
    Args:
        escalafon: Grado de escalafón (A, B, 1-14)
        grado: Grado adicional (usado como fallback si escalafon no está definido)
        nivel: Nivel educativo (usado como fallback para título_academico)
        titulo_academico: Título académico más alto (doctorado, maestría, especialización)
        cargo: Cargo desempeñado (rector, coordinador, director rural, etc.)
        horas_extras: Número de horas extras trabajadas en el mes
        tipo_docente: Tipo de docente (docente, directivo, etnoeducador)
        jornada: Tipo de jornada (completa, parcial, etc.)
        
    Returns:
        Dict con el desglose completo del cálculo:
        {
            'sueldo_base': Decimal,
            'bonificacion_2025': Decimal,
            'bonificacion_titulo': Decimal,
            'horas_extras': Decimal,
            'asignacion_cargo': Decimal,
            'prima_alimentacion': Decimal,
            'auxilio_transporte': Decimal,
            'sueldo_total': Decimal,
            'desglose': Dict con detalles de cada componente,
            'decreto_aplicado': str,
            'observaciones': List[str]
        }
        
    Example:
        resultado = calcular_sueldo_total_docente(
            escalafon='12',
            titulo_academico='Maestría en Educación',
            cargo='Coordinador Académico',
            horas_extras=10,
            tipo_docente='docente',
            jornada='completa'
        )
        
        print(f"Sueldo total: ${resultado['sueldo_total']:,.0f}")
        print(f"Decreto aplicado: {resultado['decreto_aplicado']}")
    """
    
    calculadora = CalculadorSueldoDecretos()
    
    # Normalizar parámetros de entrada
    escalafon_final = escalafon or grado or 'A'
    titulo_final = titulo_academico or nivel or ''
    tipo_docente_final = tipo_docente.lower() if tipo_docente else 'docente'
    
    # Lista para observaciones del cálculo
    observaciones = []
    
    try:
        # 1. Calcular sueldo base según decreto correspondiente
        sueldo_base = calculadora.obtener_salario_base(escalafon_final, tipo_docente_final)
        
        if sueldo_base == 0:
            observaciones.append(f"No se encontró salario base para escalafón {escalafon_final}")
        
        decreto_aplicado = "Decreto 0597/2025" if tipo_docente_final == 'etnoeducador' else "Decreto 0596/2025"
        
        # 2. Calcular bonificación mensual 2025 (Decreto 0617)
        bonificacion_2025 = calculadora.obtener_bonificacion_2025(escalafon_final, titulo_final)
        
        # Separar bonificación por escalafón y por título
        bonif_escalafon = calculadora.BONIFICACIONES_2025.get(str(escalafon_final).upper(), Decimal('0'))
        bonif_titulo = bonificacion_2025 - bonif_escalafon
        
        # 3. Calcular horas extras
        valor_horas_extras = calculadora.calcular_horas_extras(horas_extras or 0, tipo_docente_final)
        
        # 4. Calcular asignación por cargo directivo
        asignacion_cargo = calculadora.calcular_asignacion_cargo_directivo(cargo or '', sueldo_base)
        
        # 5. Verificar y calcular prima de alimentación
        prima_alimentacion = Decimal('0')
        if calculadora.verificar_prima_alimentacion(sueldo_base):
            prima_alimentacion = calculadora.PRIMA_ALIMENTACION
            observaciones.append("Aplica prima de alimentación")
        
        # 6. Verificar y calcular auxilio de transporte
        auxilio_transporte = Decimal('0')
        if calculadora.verificar_auxilio_transporte(sueldo_base, jornada):
            auxilio_transporte = calculadora.AUXILIO_TRANSPORTE
            observaciones.append("Aplica auxilio de transporte")
        
        # 7. Calcular sueldo total
        sueldo_total = (
            sueldo_base + 
            bonificacion_2025 + 
            valor_horas_extras + 
            asignacion_cargo + 
            prima_alimentacion + 
            auxilio_transporte
        )
        
        # Crear desglose detallado
        desglose = {
            'salario_base': {
                'valor': sueldo_base,
                'descripcion': f'Salario base escalafón {escalafon_final}',
                'decreto': decreto_aplicado
            },
            'bonificacion_escalafon': {
                'valor': bonif_escalafon,
                'descripcion': f'Bonificación 2025 escalafón {escalafon_final}',
                'decreto': 'Decreto 0617/2025'
            },
            'bonificacion_titulo': {
                'valor': bonif_titulo,
                'descripcion': f'Bonificación por título: {titulo_final}',
                'decreto': 'Decreto 0617/2025'
            },
            'horas_extras': {
                'valor': valor_horas_extras,
                'descripcion': f'{horas_extras or 0} horas extras',
                'decreto': decreto_aplicado
            },
            'asignacion_cargo': {
                'valor': asignacion_cargo,
                'descripcion': f'Asignación cargo: {cargo or "Ninguno"}',
                'decreto': decreto_aplicado
            },
            'prima_alimentacion': {
                'valor': prima_alimentacion,
                'descripcion': 'Prima de alimentación',
                'decreto': 'Normativa general'
            },
            'auxilio_transporte': {
                'valor': auxilio_transporte,
                'descripcion': 'Auxilio de transporte',
                'decreto': 'Normativa general'
            }
        }
        
        # Agregar observaciones adicionales
        if horas_extras and horas_extras > 0:
            observaciones.append(f"Incluye {horas_extras} horas extras")
        
        if asignacion_cargo > 0:
            observaciones.append(f"Incluye asignación por cargo: {cargo}")
        
        return {
            'sueldo_base': sueldo_base,
            'bonificacion_2025': bonificacion_2025,
            'bonificacion_escalafon': bonif_escalafon,
            'bonificacion_titulo': bonif_titulo,
            'horas_extras': valor_horas_extras,
            'asignacion_cargo': asignacion_cargo,
            'prima_alimentacion': prima_alimentacion,
            'auxilio_transporte': auxilio_transporte,
            'sueldo_total': sueldo_total,
            'desglose': desglose,
            'decreto_aplicado': decreto_aplicado,
            'decretos_consultados': ['0596/2025', '0597/2025', '0617/2025'],
            'observaciones': observaciones,
            'parametros_entrada': {
                'escalafon': escalafon_final,
                'titulo_academico': titulo_final,
                'cargo': cargo,
                'horas_extras': horas_extras,
                'tipo_docente': tipo_docente_final,
                'jornada': jornada
            }
        }
        
    except Exception as e:
        logger.error(f"Error calculando sueldo: {e}")
        return {
            'sueldo_base': Decimal('0'),
            'bonificacion_2025': Decimal('0'),
            'bonificacion_escalafon': Decimal('0'),
            'bonificacion_titulo': Decimal('0'),
            'horas_extras': Decimal('0'),
            'asignacion_cargo': Decimal('0'),
            'prima_alimentacion': Decimal('0'),
            'auxilio_transporte': Decimal('0'),
            'sueldo_total': Decimal('0'),
            'desglose': {},
            'decreto_aplicado': 'Error en cálculo',
            'decretos_consultados': ['0596/2025', '0597/2025', '0617/2025'],
            'observaciones': [f'Error en el cálculo: {str(e)}'],
            'error': str(e)
        }


def calcular_sueldo_desde_bd(cedula: str, anio: int = 2025) -> Dict[str, Any]:
    """
    Calcula el sueldo de un docente usando los datos almacenados en la base de datos.
    
    Args:
        cedula: Cédula del afiliado
        anio: Año para el cálculo (por defecto 2025)
        
    Returns:
        Resultado del cálculo usando datos de la BD
    """
    try:
        from afiliados.models import Afiliado
        
        afiliado = Afiliado.objects.get(cedula=cedula)
        
        return calcular_sueldo_total_docente(
            escalafon=afiliado.grado_escalafon,
            titulo_academico=afiliado.titulo_posgrado,
            cargo=afiliado.cargo_desempenado,
            horas_extras=0,  # Este campo se podría agregar al modelo si es necesario
            tipo_docente='docente',  # Se podría inferir del cargo o agregar campo
            jornada='completa'  # Se podría agregar al modelo si es necesario
        )
        
    except Exception as e:
        return {
            'error': f'Error obteniendo datos del afiliado {cedula}: {str(e)}',
            'sueldo_total': Decimal('0')
        }


def generar_reporte_calculo(resultado: Dict[str, Any]) -> str:
    """
    Genera un reporte legible del cálculo de sueldo.
    
    Args:
        resultado: Resultado del cálculo de sueldo
        
    Returns:
        Reporte formateado como string
    """
    if 'error' in resultado:
        return f"ERROR EN CÁLCULO: {resultado['error']}"
    
    reporte = []
    reporte.append("=" * 60)
    reporte.append("CÁLCULO DE SUELDO DOCENTE - DECRETOS 2025")
    reporte.append("=" * 60)
    reporte.append(f"Decreto principal aplicado: {resultado['decreto_aplicado']}")
    reporte.append(f"Decretos consultados: {', '.join(resultado['decretos_consultados'])}")
    reporte.append("")
    
    reporte.append("PARÁMETROS DE ENTRADA:")
    params = resultado['parametros_entrada']
    reporte.append(f"  • Escalafón: {params['escalafon']}")
    reporte.append(f"  • Título académico: {params['titulo_academico'] or 'No especificado'}")
    reporte.append(f"  • Cargo: {params['cargo'] or 'Docente'}")
    reporte.append(f"  • Horas extras: {params['horas_extras']}")
    reporte.append(f"  • Tipo docente: {params['tipo_docente']}")
    reporte.append(f"  • Jornada: {params['jornada']}")
    reporte.append("")
    
    reporte.append("DESGLOSE DEL CÁLCULO:")
    for concepto, detalle in resultado['desglose'].items():
        if detalle['valor'] > 0:
            reporte.append(f"  • {detalle['descripcion']}: ${detalle['valor']:,.0f}")
            reporte.append(f"    ({detalle['decreto']})")
    
    reporte.append("")
    reporte.append(f"SUELDO TOTAL: ${resultado['sueldo_total']:,.0f}")
    reporte.append("")
    
    if resultado['observaciones']:
        reporte.append("OBSERVACIONES:")
        for obs in resultado['observaciones']:
            reporte.append(f"  • {obs}")
    
    reporte.append("=" * 60)
    
    return "\n".join(reporte)
