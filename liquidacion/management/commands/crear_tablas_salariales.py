"""
Comando de gestión para crear tablas salariales para los grados faltantes.

Este comando crea entradas en la tabla TablaSalarial para los grados especificados
con un salario base predeterminado.

Ejemplo de uso:
    python manage.py crear_tablas_salariales --grados 3,10,12,13 --anio 2025
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
import logging

from liquidacion.models import TablaSalarial

logger = logging.getLogger(__name__)

# Salarios base por defecto según el grado (puedes ajustar estos valores)
SALARIOS_BASE_POR_GRADO = {
    '1': Decimal('2000000'),
    '2': Decimal('2200000'),
    '3': Decimal('2400000'),
    '4': Decimal('2600000'),
    '5': Decimal('2800000'),
    '6': Decimal('3000000'),
    '7': Decimal('3200000'),
    '8': Decimal('3400000'),
    '9': Decimal('3600000'),
    '10': Decimal('3800000'),
    '11': Decimal('4000000'),
    '12': Decimal('4200000'),
    '13': Decimal('4400000'),
    '14': Decimal('4600000'),
    'A': Decimal('1800000'),
    'B': Decimal('1900000'),
}

class Command(BaseCommand):
    help = 'Crea tablas salariales para los grados especificados'

    def add_arguments(self, parser):
        parser.add_argument(
            '--grados',
            type=str,
            help='Grados para los que crear tablas salariales (separados por comas, ej: 1,2,3,10). Si no se especifica, se crearán para todos los grados.',
            required=False,
            default=','.join([str(i) for i in range(1, 15)] + ['A', 'B'])
        )
        parser.add_argument(
            '--anio',
            type=int,
            help='Año para el que se crearán las tablas salariales (por defecto: 2025)',
            default=2025
        )
        parser.add_argument(
            '--forzar',
            action='store_true',
            help='Forzar la actualización de tablas existentes',
            default=False
        )

    def handle(self, *args, **options):
        # Obtener la lista de grados, eliminando cadenas vacías si las hay
        grados = [g.strip() for g in options['grados'].split(',') if g.strip()]
        anio = options['anio']
        forzar = options['forzar']
        
        self.stdout.write(self.style.SUCCESS(f'Grados a procesar: {grados}'))
        
        self.stdout.write(self.style.SUCCESS(f'Iniciando creación de tablas salariales para el año {anio}...'))
        
        creadas = 0
        actualizadas = 0
        
        for grado in grados:
            if grado not in SALARIOS_BASE_POR_GRADO:
                self.stdout.write(self.style.WARNING(f'No se encontró un salario base para el grado {grado}. Se usará un valor por defecto.'))
                salario_base = Decimal('2000000')  # Valor por defecto
            else:
                salario_base = SALARIOS_BASE_POR_GRADO[grado]
            
            try:
                with transaction.atomic():
                    # Verificar si ya existe una tabla para este grado y año
                    tabla, created = TablaSalarial.objects.get_or_create(
                        anio=anio,
                        grado=grado,
                        defaults={'salario_base': salario_base}
                    )
                    
                    if not created and forzar:
                        # Si la tabla ya existe y se especificó --forzar, actualizamos el salario
                        if tabla.salario_base != salario_base:
                            tabla.salario_base = salario_base
                            tabla.save()
                            actualizadas += 1
                            self.stdout.write(self.style.SUCCESS(f'Actualizada tabla salarial para grado {grado} - Año {anio}: ${salario_base:,.0f}'))
                        else:
                            self.stdout.write(self.style.NOTICE(f'Tabla salarial para grado {grado} - Año {anio} ya existe con el mismo salario base (${salario_base:,.0f})'))
                    elif created:
                        creadas += 1
                        self.stdout.write(self.style.SUCCESS(f'Creada tabla salarial para grado {grado} - Año {anio}: ${salario_base:,.0f}'))
                    else:
                        self.stdout.write(self.style.NOTICE(f'Tabla salarial para grado {grado} - Año {anio} ya existe (${tabla.salario_base:,.0f}). Usa --forzar para actualizar.'))
                        
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error al crear tabla salarial para grado {grado}: {str(e)}'))
                logger.exception(f'Error al crear tabla salarial para grado {grado}')
        
        self.stdout.write(self.style.SUCCESS(f'\nResumen:'))
        self.stdout.write(self.style.SUCCESS(f'- Tablas creadas: {creadas}'))
        self.stdout.write(self.style.SUCCESS(f'- Tablas actualizadas: {actualizadas}'))
        self.stdout.write(self.style.SUCCESS(f'Proceso completado.'))
