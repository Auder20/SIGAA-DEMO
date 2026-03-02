"""
Comando para inicializar los parámetros de liquidación por defecto.

Ejecutar con:
    python manage.py inicializar_parametros
"""

from django.core.management.base import BaseCommand
from liquidacion.models import ParametroLiquidacion


class Command(BaseCommand):
    help = 'Inicializa los parámetros de liquidación con valores por defecto'

    def handle(self, *args, **options):
        self.stdout.write('Inicializando parámetros de liquidación...')
        
        # Parámetros de Aportes
        parametros = [
            # Aportes ADEMACOR (1% por defecto)
            {
                'codigo': 'APORTE_ADEMACOR',
                'nombre': 'Aporte ADEMACOR',
                'tipo': ParametroLiquidacion.TIPO_APORTE,
                'valor_numerico': 1.0,  # 1%
                'anio_vigencia': 0,  # Permanente
                'descripcion': 'Porcentaje de aporte a ADEMACOR sobre el sueldo neto',
            },
            
            # Aportes FAMICOR (0.2% por defecto)
            {
                'codigo': 'APORTE_FAMICOR',
                'nombre': 'Aporte FAMICOR',
                'tipo': ParametroLiquidacion.TIPO_APORTE,
                'valor_numerico': 0.2,  # 0.2%
                'anio_vigencia': 0,  # Permanente
                'descripcion': 'Porcentaje de aporte a FAMICOR sobre el sueldo neto',
            },
            
            # Otros parámetros pueden ir aquí
        ]
        
        creados = 0
        actualizados = 0
        
        for param_data in parametros:
            # Extraer la descripción si existe
            descripcion = param_data.pop('descripcion', '')
            
            # Buscar si ya existe un parámetro con el mismo código y año
            parametro, creado = ParametroLiquidacion.objects.update_or_create(
                codigo=param_data['codigo'],
                anio_vigencia=param_data['anio_vigencia'],
                defaults=param_data
            )
            
            # Actualizar la descripción si es necesario
            if not parametro.valor_texto and descripcion:
                parametro.valor_texto = descripcion
                parametro.save(update_fields=['valor_texto'])
            
            if creado:
                self.stdout.write(
                    self.style.SUCCESS(f'Creado parámetro: {parametro.codigo} ' 
                                     f'({parametro.anio_vigencia or "Permanente"})')
                )
                creados += 1
            else:
                self.stdout.write(
                    self.style.WARNING(f'Actualizado parámetro: {parametro.codigo} ' 
                                     f'({parametro.anio_vigencia or "Permanente"})')
                )
                actualizados += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\nProceso completado. Creados: {creados}, Actualizados: {actualizados}.'
            )
        )
        
        # Mostrar ayuda sobre cómo usar los parámetros
        self.stdout.write('\nPara modificar los parámetros, acceda a la sección de administración:')
        self.stdout.write('1. Inicie el servidor: python manage.py runserver')
        self.stdout.write('2. Acceda a http://127.0.0.1:8000/admin/liquidacion/parametroliquidacion/')
        self.stdout.write('3. Haga clic en un parámetro para editarlo o en "Añadir parámetro" para crear uno nuevo')
        self.stdout.write('\nPara aplicar un aumento porcentual a un parámetro existente:')
        self.stdout.write('1. Seleccione el parámetro')
        self.stdout.write('2. Haga clic en el botón "Aplicar Aumento Porcentual"')
        self.stdout.write('3. Ingrese el porcentaje de aumento y haga clic en "Aplicar Aumento"')
