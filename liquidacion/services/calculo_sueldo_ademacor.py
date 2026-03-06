from decimal import Decimal
from datetime import date
from ..models import TablaSalarial, SueldoAdemacor, BonificacionPagoAdemacor

class CalculadorSueldoAdemacor:
    """
    Servicio para calcular el sueldo de un afiliado ADEMACOR.

    Encapsula toda la lógica de negocio para determinar el salario base
    y las bonificaciones correspondientes según la normativa vigente.
    """

    def __init__(self, afiliado_ademacor, anio=None):
        """
        Inicializa el calculador para un afiliado y año específicos.

        Args:
            afiliado_ademacor: Instancia de DatosAdemacor
            anio: Año para el cálculo (default: año actual)
        """
        self.afiliado = afiliado_ademacor
        self.anio = anio or date.today().year
        self.tabla_salarial = None
        self.errores = []

    def _obtener_tabla_salarial(self):
        """Obtiene la tabla salarial correspondiente al grado y año"""
        if not self.afiliado.grado_escalafon:
            self.errores.append("El afiliado no tiene grado de escalafón asignado")
            return None

        try:
            tabla = TablaSalarial.objects.get(
                anio=self.anio,
                grado=self.afiliado.grado_escalafon
            )
            return tabla
        except TablaSalarial.DoesNotExist:
            self.errores.append(f"No existe tabla salarial para el año {self.anio} y grado {self.afiliado.grado_escalafon}")
            return None

    def calcular_sueldo_neto(self, cargo_especifico=None, bonificaciones_adicionales=None):
        """
        Realiza el cálculo completo del sueldo.

        Returns:
            dict: Detalle del cálculo con sueldo neto y desglose
        """
        tabla = self._obtener_tabla_salarial()
        if not tabla:
            return {'error': '; '.join(self.errores), 'sueldo_neto': 0}

        self.tabla_salarial = tabla
        salario_base = tabla.salario_base

        # Inicializar desglose
        desglose = {
            'salario_base': salario_base,
            'bonificaciones': [],
            'total_bonificaciones': Decimal('0.00')
        }

        # 1. Bonificación por antigüedad (Años de servicio)
        # Por cada año de servicio se suma un porcentaje (ejemplo simplificado)
        # Ajustar según reglas de negocio reales
        if self.afiliado.anos_servicio:
            porcentaje_antiguedad = Decimal('0.02') * self.afiliado.anos_servicio # 2% por año
            monto_antiguedad = salario_base * porcentaje_antiguedad
            desglose['bonificaciones'].append({
                'descripcion': f'Antigüedad ({self.afiliado.anos_servicio} años)',
                'porcentaje': porcentaje_antiguedad * 100,
                'monto': monto_antiguedad
            })
            desglose['total_bonificaciones'] += monto_antiguedad

        # 2. Bonificación por Cargo (Rector, Coordinador, etc.)
        cargo = cargo_especifico or self.afiliado.cargo_desempenado
        if cargo:
            # Lógica simplificada de bonificación por cargo
            porcentaje_cargo = Decimal('0.00')
            if 'RECTOR' in cargo.upper():
                porcentaje_cargo = Decimal('0.30')
            elif 'COORDINADOR' in cargo.upper():
                porcentaje_cargo = Decimal('0.20')
            elif 'DIRECTOR' in cargo.upper():
                porcentaje_cargo = Decimal('0.25')

            if porcentaje_cargo > 0:
                monto_cargo = salario_base * porcentaje_cargo
                desglose['bonificaciones'].append({
                    'descripcion': f'Cargo Directivo ({cargo})',
                    'porcentaje': porcentaje_cargo * 100,
                    'monto': monto_cargo
                })
                desglose['total_bonificaciones'] += monto_cargo

        # 3. Bonificación por Estudios (Maestría, Doctorado)
        # Verificar títulos de posgrado
        porcentaje_estudios = Decimal('0.00')
        descripcion_estudios = ""

        titulo = (self.afiliado.titulo_posgrado or "").upper()
        estudios = (self.afiliado.estudios_posgrado or "").upper()

        if 'DOCTOR' in titulo or 'DOCTOR' in estudios:
            porcentaje_estudios = Decimal('0.15')
            descripcion_estudios = "Doctorado"
        elif 'MAESTR' in titulo or 'MAGISTER' in titulo or 'MAESTR' in estudios:
            porcentaje_estudios = Decimal('0.10')
            descripcion_estudios = "Maestría"
        elif 'ESPECIALI' in titulo or 'ESPECIALI' in estudios:
            porcentaje_estudios = Decimal('0.05')
            descripcion_estudios = "Especialización"

        if porcentaje_estudios > 0:
            monto_estudios = salario_base * porcentaje_estudios
            desglose['bonificaciones'].append({
                'descripcion': f'Título Posgrado ({descripcion_estudios})',
                'porcentaje': porcentaje_estudios * 100,
                'monto': monto_estudios
            })
            desglose['total_bonificaciones'] += monto_estudios

        # 4. Bonificaciones Adicionales (Manuales)
        if bonificaciones_adicionales:
            for desc, valor in bonificaciones_adicionales.items():
                monto = Decimal(str(valor))
                desglose['bonificaciones'].append({
                    'descripcion': desc,
                    'porcentaje': 0,
                    'monto': monto
                })
                desglose['total_bonificaciones'] += monto

        # Cálculo final
        sueldo_neto = salario_base + desglose['total_bonificaciones']
        desglose['sueldo_neto'] = sueldo_neto

        return desglose

    def crear_o_actualizar_sueldo(self, cargo_especifico=None, bonificaciones_adicionales=None):
        """
        Calcula y guarda el sueldo en la base de datos.

        Returns:
            tuple: (SueldoAdemacor, created, desglose)
        """
        desglose = self.calcular_sueldo_neto(cargo_especifico, bonificaciones_adicionales)

        if 'error' in desglose:
            return None, False, desglose

        # Crear o actualizar registro de SueldoAdemacor
        sueldo, created = SueldoAdemacor.objects.update_or_create(
            afiliado_ademacor=self.afiliado,
            anio=self.anio,
            defaults={
                'sueldo_neto': desglose['sueldo_neto'],
                'tabla_salarial': self.tabla_salarial
            }
        )

        # Actualizar bonificaciones (borrar anteriores y crear nuevas)
        sueldo.bonificaciones.all().delete()

        for bonif in desglose['bonificaciones']:
            BonificacionPagoAdemacor.objects.create(
                sueldo_ademacor=sueldo,
                anio=self.anio,
                descripcion=bonif['descripcion'],
                porcentaje=bonif['porcentaje'],
                monto=bonif['monto']
            )

        # Recalcular aportes automáticamente
        sueldo.recalculate_aportes()

        return sueldo, created, desglose


def recalcular_sueldos_ademacor_masivo(anio=None, filtros=None):
    """
    Recalcula los sueldos de múltiples afiliados ADEMACOR de forma masiva.

    Procesa todos los afiliados ADEMACOR activos (o los filtrados) y recalcula
    sus sueldos usando el sistema de cálculo automático. Útil para
    actualizaciones masivas cuando cambian las tablas salariales o
    las reglas de bonificación.

    Args:
        anio (int, optional): Año para el cálculo. Por defecto usa año actual
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
        resultado = recalcular_sueldos_ademacor_masivo(2025)

        # Solo afiliados de grado 14
        resultado = recalcular_sueldos_ademacor_masivo(2025, {'grado_escalafon': '14'})
    """
    from afiliados.models import DatosOrganizacion
    from datetime import date
    import logging

    logger = logging.getLogger(__name__)
    anio = anio or date.today().year

    # Aplicar filtros
    queryset = DatosOrganizacion.objects.filter(activo=True)
    if filtros:
        queryset = queryset.filter(**filtros)

    resultados = {
        'procesados': 0,
        'creados': 0,
        'actualizados': 0,
        'errores': []
    }

    for afiliado_ademacor in queryset:
        try:
            calculador = CalculadorSueldoAdemacor(afiliado_ademacor, anio)
            sueldo, created, desglose = calculador.crear_o_actualizar_sueldo()

            if sueldo:
                resultados['procesados'] += 1
                if created:
                    resultados['creados'] += 1
                else:
                    resultados['actualizados'] += 1
            else:
                resultados['errores'].append({
                    'cedula': afiliado_ademacor.cedula,
                    'error': desglose.get('error', 'Error desconocido')
                })

        except Exception as e:
            logger.exception(f"Error procesando afiliado ADEMACOR {afiliado_ademacor.cedula}: {e}")
            resultados['errores'].append({
                'cedula': afiliado_ademacor.cedula,
                'error': str(e)
            })

    return resultados
