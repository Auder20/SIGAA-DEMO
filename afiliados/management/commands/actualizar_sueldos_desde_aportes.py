from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
from reportes.models import ReporteAportesTotales


class Command(BaseCommand):
    help = 'Actualiza los sueldos netos basándose en los valores de los aportes ADEMACOR (1%) y FAMECOR (0.2%)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--anio',
            type=int,
            help='Año específico para procesar (opcional, si no se especifica usa todos los años)'
        )
        parser.add_argument(
            '--mes',
            type=int,
            help='Mes específico para procesar (1-12, opcional)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Sobrescribe sueldos existentes (no solo los que son 0)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Simula la ejecución sin hacer cambios'
        )

    def handle(self, *args, **options):
        anio = options.get('anio')
        mes = options.get('mes')
        force = options.get('force')
        dry_run = options.get('dry_run')

        self.stdout.write(self.style.SUCCESS('🔧 Iniciando actualización de sueldos desde aportes...'))

        # Obtener reportes a procesar
        queryset = ReporteAportesTotales.objects.all()
        if anio:
            queryset = queryset.filter(anio=anio)
        if mes:
            queryset = queryset.filter(mes=mes)

        if not queryset.exists():
            self.stdout.write(self.style.WARNING('⚠️  No se encontraron reportes para los criterios especificados.'))
            return

        total_actualizados = 0
        total_no_actualizables = 0
        total_procesados = 0

        for reporte in queryset:
            self.stdout.write(f"\n📊 Procesando reporte: {reporte.get_nombre_mes()} {reporte.anio}")
            
            if dry_run:
                self.stdout.write(self.style.WARNING('   🔍 MODO SIMULACIÓN - No se harán cambios reales'))
            
            try:
                with transaction.atomic():
                    # Actualizar sueldos desde aportes
                    resultado = reporte.actualizar_sueldos_desde_aportes()
                    
                    if dry_run:
                        # En modo dry-run, solo mostramos qué se haría
                        from liquidacion.models import Aporte, Sueldo
                        aportes_periodo = Aporte.objects.filter(
                            sueldo__anio=reporte.anio
                        ).select_related('sueldo')
                        
                        sueldos_a_actualizar = 0
                        for aporte in aportes_periodo:
                            if not aporte.sueldo.sueldo_neto or aporte.sueldo.sueldo_neto == 0 or force:
                                sueldos_a_actualizar += 1
                        
                        self.stdout.write(f"   📈 Se actualizarían {sueldos_a_actualizar} sueldos")
                    else:
                        total_actualizados += resultado['sueldos_actualizados']
                        total_no_actualizables += resultado['sueldos_no_actualizables']
                        total_procesados += resultado['total_procesados']
                        
                        self.stdout.write(self.style.SUCCESS(f"   ✅ Actualizados: {resultado['sueldos_actualizados']}"))
                        self.stdout.write(f"   ⚠️  No actualizables: {resultado['sueldos_no_actualizables']}")
                        self.stdout.write(f"   📋 Total procesados: {resultado['total_procesados']}")
                        
                        # Recalcular totales del reporte
                        reporte.calcular_totales()
                        self.stdout.write(self.style.SUCCESS(f"   🔄 Totales del reporte recalculados"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"   ❌ Error procesando reporte: {str(e)}"))
                continue

        # Resumen final
        if not dry_run:
            self.stdout.write("\n" + "="*60)
            self.stdout.write(self.style.SUCCESS('📊 RESUMEN FINAL'))
            self.stdout.write(f"📈 Sueldos actualizados: {total_actualizados}")
            self.stdout.write(f"⚠️  No actualizables: {total_no_actualizables}")
            self.stdout.write(f"📋 Total procesados: {total_procesados}")
            
            if total_actualizados > 0:
                self.stdout.write(self.style.SUCCESS('\n✅ ¡Proceso completado exitosamente!'))
            else:
                self.stdout.write(self.style.WARNING('\n⚠️  No se actualizaron sueldos. Verifique que haya aportes con valores válidos.'))
        else:
            self.stdout.write("\n" + "="*60)
            self.stdout.write(self.style.SUCCESS('🔍 SIMULACIÓN COMPLETADA'))
            self.stdout.write(self.style.INFO('Ejecute sin --dry-run para aplicar los cambios reales'))

        # Ejemplos de uso
        if not anio and not mes:
            self.stdout.write("\n" + "="*60)
            self.stdout.write(self.style.INFO('💡 EJEMPLOS DE USO:'))
            self.stdout.write('  python manage.py actualizar_sueldos_desde_aportes')
            self.stdout.write('  python manage.py actualizar_sueldos_desde_aportes --anio 2024')
            self.stdout.write('  python manage.py actualizar_sueldos_desde_aportes --anio 2024 --mes 1')
            self.stdout.write('  python manage.py actualizar_sueldos_desde_aportes --force')
            self.stdout.write('  python manage.py actualizar_sueldos_desde_aportes --dry-run')
