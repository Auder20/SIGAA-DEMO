# En liquidacion/management/commands/update_sueldo_con_bonificacion.py
from django.core.management.base import BaseCommand
from decimal import Decimal
from liquidacion.models import TablaSalarial

class Command(BaseCommand):
    help = 'Actualiza sueldo_con_bonificacion para todas las tablas salariales'

    def handle(self, *args, **options):
        # Recorrer todos los registros y calcular el valor
        for tabla in TablaSalarial.objects.all():
            aumento = {
                'A': Decimal('24767'),
                'B': Decimal('27469'),
                '1': Decimal('30785'),
                '2': Decimal('31910'),
                '3': Decimal('33863'),
                '4': Decimal('35200'),
                '5': Decimal('37420'),
                '6': Decimal('39582'),
                '7': Decimal('44297'),
                '8': Decimal('48658'),
                '9': Decimal('53903'),
                '10': Decimal('59020'),
                '11': Decimal('67392'),
                '12': Decimal('80167'),
                '13': Decimal('88738'),
                '14': Decimal('101064')
            }.get(tabla.grado.upper(), Decimal('0'))
            
            sueldo_total = tabla.salario_base + aumento
            tabla.sueldo_con_bonificacion = sueldo_total
            tabla.save(update_fields=['sueldo_con_bonificacion'])
        
        self.stdout.write(
            self.style.SUCCESS('Se actualizó correctamente el sueldo con bonificación')
        )