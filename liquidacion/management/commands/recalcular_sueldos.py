"""
Comando de Django para recalcular los sueldos de los afiliados usando el nuevo sistema de cálculo.

Este comando permite recalcular sueldos de forma individual o masiva utilizando el
sistema automático de cálculo basado en parámetros como grado de escalafón, cargo
desempeñado, años de servicio y nivel educativo.

Ejemplos de uso:
    # Recalcular todos los sueldos del 2025
    python manage.py recalcular_sueldos --anio 2025

    # Recalcular sueldo de un afiliado específico
    python manage.py recalcular_sueldos --cedula 12345678 --verbose

    # Recalcular solo afiliados de grado 14
    python manage.py recalcular_sueldos --grado 14 --anio 2025

    # Modo de prueba sin guardar cambios
    python manage.py recalcular_sueldos --dry-run --verbose

Autor: Sistema SIGAA
Fecha: 2025
"""
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from afiliados.models import Afiliado
from liquidacion.services.calculo_sueldo import recalcular_sueldos_masivo, CalculadorSueldo


class Command(BaseCommand):
    """
    Comando de gestión Django para recalcular sueldos de afiliados.
    
    Implementa la funcionalidad para recalcular sueldos utilizando el nuevo
    sistema automático que considera múltiples parámetros para determinar
    el sueldo final de cada afiliado.
    
    Características:
    - Cálculo individual por cédula o masivo
    - Filtrado por grado de escalafón
    - Modo de prueba (dry-run) para validar antes de aplicar
    - Salida detallada con desglose de cálculos
    - Manejo de transacciones para integridad de datos
    """
    help = 'Recalcula los sueldos de los afiliados basado en sus parámetros (grado, cargo, etc.)'

    def add_arguments(self, parser):
        """
        Define los argumentos de línea de comandos disponibles.
        
        Args:
            parser: ArgumentParser de Django para definir opciones del comando
        """
        parser.add_argument(
            '--anio',
            type=int,
            default=2025,
            help='Año para el cálculo de sueldos (por defecto: 2025)'
        )
        parser.add_argument(
            '--cedula',
            type=str,
            help='Cédula específica de un afiliado para calcular solo su sueldo'
        )
        parser.add_argument(
            '--grado',
            type=str,
            help='Filtrar por grado de escalafón específico'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Ejecutar en modo de prueba sin guardar cambios'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Mostrar información detallada del proceso'
        )

    def handle(self, *args, **options):
        """
        Método principal que ejecuta el comando.
        
        Procesa los argumentos recibidos y ejecuta el cálculo de sueldos
        según los parámetros especificados (individual o masivo).
        
        Args:
            *args: Argumentos posicionales (no utilizados)
            **options: Diccionario con las opciones del comando
            
        Raises:
            CommandError: Si ocurre algún error durante el proceso
        """
        anio = options['anio']
        cedula = options['cedula']
        grado = options['grado']
        dry_run = options['dry_run']
        verbose = options['verbose']

        if dry_run:
            self.stdout.write(
                self.style.WARNING('MODO DE PRUEBA - No se guardarán cambios')
            )

        try:
            if cedula:
                # Calcular sueldo para un afiliado específico
                self._calcular_sueldo_individual(cedula, anio, dry_run, verbose)
            else:
                # Calcular sueldos masivamente
                filtros = {}
                if grado:
                    filtros['grado_escalafon'] = grado
                
                self._calcular_sueldos_masivo(anio, filtros, dry_run, verbose)

        except Exception as e:
            raise CommandError(f'Error durante el cálculo: {e}')

    def _calcular_sueldo_individual(self, cedula, anio, dry_run, verbose):
        """
        Calcula el sueldo de un afiliado específico por cédula.
        
        Busca el afiliado por cédula, realiza el cálculo de sueldo y
        opcionalmente guarda el resultado en la base de datos.
        
        Args:
            cedula (str): Cédula del afiliado a procesar
            anio (int): Año para el cálculo del sueldo
            dry_run (bool): Si True, no guarda cambios en la base de datos
            verbose (bool): Si True, muestra desglose detallado del cálculo
            
        Raises:
            CommandError: Si el afiliado no existe o hay errores en el cálculo
        """
        try:
            afiliado = Afiliado.objects.get(cedula=cedula)
        except Afiliado.DoesNotExist:
            raise CommandError(f'Afiliado con cédula {cedula} no encontrado')

        self.stdout.write(f'Calculando sueldo para: {afiliado.nombre_completo} ({cedula})')
        
        calculadora = CalculadorSueldo(afiliado, anio)
        calculo = calculadora.calcular_sueldo_neto()

        if 'error' in calculo:
            self.stdout.write(
                self.style.ERROR(f'Error: {calculo["error"]}')
            )
            return

        # Mostrar desglose
        self._mostrar_desglose_calculo(calculo, verbose)

        if not dry_run:
            with transaction.atomic():
                sueldo, created, _ = calculadora.crear_o_actualizar_sueldo()
                if sueldo:
                    accion = "creado" if created else "actualizado"
                    self.stdout.write(
                        self.style.SUCCESS(f'Sueldo {accion} exitosamente')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR('Error al guardar el sueldo')
                    )

    def _calcular_sueldos_masivo(self, anio, filtros, dry_run, verbose):
        """
        Calcula sueldos para múltiples afiliados de forma masiva.
        
        Procesa todos los afiliados activos que cumplan con los filtros
        especificados y recalcula sus sueldos usando el sistema automático.
        
        Args:
            anio (int): Año para el cálculo de sueldos
            filtros (dict): Filtros adicionales para el queryset de afiliados
            dry_run (bool): Si True, solo simula el proceso sin guardar cambios
            verbose (bool): Si True, muestra información detallada del proceso
        """
        self.stdout.write(f'Recalculando sueldos para el año {anio}...')
        
        if filtros:
            self.stdout.write(f'Filtros aplicados: {filtros}')

        if not dry_run:
            resultados = recalcular_sueldos_masivo(anio, filtros)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Proceso completado:\n'
                    f'  - Procesados: {resultados["procesados"]}\n'
                    f'  - Creados: {resultados["creados"]}\n'
                    f'  - Actualizados: {resultados["actualizados"]}\n'
                    f'  - Errores: {len(resultados["errores"])}'
                )
            )

            if resultados['errores'] and verbose:
                self.stdout.write('\nErrores encontrados:')
                for error in resultados['errores']:
                    self.stdout.write(
                        self.style.ERROR(f'  - {error["cedula"]}: {error["error"]}')
                    )
        else:
            # Modo de prueba - solo mostrar qué se haría
            queryset = Afiliado.objects.filter(activo=True)
            if filtros:
                queryset = queryset.filter(**filtros)
            
            count = queryset.count()
            self.stdout.write(f'Se procesarían {count} afiliados')
            
            if verbose and count <= 10:
                self.stdout.write('\nAfiliados que se procesarían:')
                for afiliado in queryset[:10]:
                    calculadora = CalculadorSueldo(afiliado, anio)
                    calculo = calculadora.calcular_sueldo_neto()
                    
                    if 'error' not in calculo:
                        self.stdout.write(
                            f'  - {afiliado.cedula} ({afiliado.nombre_completo}): '
                            f'${calculo["sueldo_neto"]:,.2f}'
                        )
                    else:
                        self.stdout.write(
                            self.style.ERROR(
                                f'  - {afiliado.cedula} ({afiliado.nombre_completo}): '
                                f'ERROR - {calculo["error"]}'
                            )
                        )

    def _mostrar_desglose_calculo(self, calculo, verbose):
        """
        Muestra el desglose detallado del cálculo de sueldo.
        
        Presenta la información del cálculo de forma organizada, mostrando
        el sueldo final y, si se solicita modo verbose, el desglose completo
        de todas las bonificaciones aplicadas.
        
        Args:
            calculo (dict): Diccionario con el resultado del cálculo de sueldo
            verbose (bool): Si True, muestra desglose detallado de bonificaciones
        """
        self.stdout.write(f'\nSueldo calculado: ${calculo["sueldo_neto"]:,.2f}')
        
        if verbose:
            self.stdout.write('\nDesglose:')
            self.stdout.write(f'  Salario base: ${calculo["salario_base"]:,.2f}')
            
            desglose = calculo['desglose']
            
            if calculo['bonificacion_cargo'] > 0:
                self.stdout.write(
                    f'  Bonificación cargo ({desglose["cargo"]["porcentaje"]}%): '
                    f'${calculo["bonificacion_cargo"]:,.2f}'
                )
            
            if calculo['bonificacion_antiguedad'] > 0:
                self.stdout.write(
                    f'  Bonificación antigüedad ({desglose["antiguedad"]["porcentaje"]}%): '
                    f'${calculo["bonificacion_antiguedad"]:,.2f}'
                )
            
            if calculo['bonificacion_educacion'] > 0:
                self.stdout.write(
                    f'  Bonificación educación ({desglose["educacion"]["porcentaje"]}%): '
                    f'${calculo["bonificacion_educacion"]:,.2f}'
                )
            
            if calculo['bonificaciones_adicionales'] > 0:
                self.stdout.write(
                    f'  Bonificaciones adicionales: ${calculo["bonificaciones_adicionales"]:,.2f}'
                )
                for concepto, info in desglose['adicionales'].items():
                    self.stdout.write(
                        f'    - {concepto} ({info["porcentaje"]}%): ${info["monto"]:,.2f}'
                    )
            
            self.stdout.write(f'  Sueldo bruto: ${calculo["sueldo_bruto"]:,.2f}')
