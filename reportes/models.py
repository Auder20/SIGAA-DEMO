from django.db import models
from users.models import User
from decimal import Decimal

class Reporte(models.Model):
    """
    Modelo para gestión de reportes generados en el sistema SIGAA.
    
    Almacena información sobre reportes creados por los usuarios, incluyendo
    el tipo de reporte, fecha de generación, usuario que lo generó y el
    archivo resultante. Permite mantener un historial de reportes para
    auditoría y reutilización.
    
    Los reportes pueden ser de diferentes tipos (Excel, PDF, etc.) y se
    almacenan en el directorio 'reportes/' del sistema de archivos.
    """
    
    # Tipos de reportes disponibles
    TIPOS_REPORTE = [
        ('excel', 'Excel'),
        ('pdf', 'PDF'),
        ('csv', 'CSV'),
        ('sueldos', 'Reporte de Sueldos'),
        ('aportes', 'Reporte de Aportes'),
        ('afiliados', 'Reporte de Afiliados'),
        ('diferencias_secretaria_organizacion', 'Diferencias Secretaría vs Organización'),
    ]
    
    tipo = models.CharField(
        max_length=50,
        choices=TIPOS_REPORTE,
        help_text="Tipo de reporte generado (Excel, PDF, CSV, etc.)"
    )
    fecha_generado = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha y hora de generación del reporte"
    )
    generado_por = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        help_text="Usuario que generó el reporte"
    )
    archivo = models.FileField(
        upload_to='reportes/', 
        null=True, 
        blank=True,
        help_text="Archivo del reporte generado"
    )
    # Nuevos campos para almacenar ambos archivos en la misma fila
    archivo_excel = models.FileField(
        upload_to='reportes/',
        null=True,
        blank=True,
        help_text="Archivo Excel del reporte (si aplica)"
    )
    archivo_pdf = models.FileField(
        upload_to='reportes/',
        null=True,
        blank=True,
        help_text="Archivo PDF del reporte (si aplica)"
    )
    descripcion = models.TextField(
        null=True, 
        blank=True,
        help_text="Descripción adicional del contenido del reporte"
    )
    activo = models.BooleanField(
        default=True,
        help_text="Indica si el reporte está activo (visible)"
    )

    class Meta:
        verbose_name = "Reporte"
        verbose_name_plural = "Reportes"
        ordering = ['-fecha_generado']

    def __str__(self):
        """
        Representación en cadena del reporte.
        
        Returns:
            str: Tipo de reporte y fecha de generación
        """
        return f"{self.get_tipo_display()} - {self.fecha_generado.strftime('%Y-%m-%d %H:%M')}"
    
    def get_nombre_archivo(self):
        """
        Obtiene el nombre del archivo sin la ruta completa.
        
        Returns:
            str: Nombre del archivo o 'Sin archivo' si no existe
        """
        if self.archivo:
            return self.archivo.name.split('/')[-1]
        return 'Sin archivo'

    def get_nombre_archivo_excel(self):
        """Devuelve el nombre de `archivo_excel` o un marcador si no existe."""
        if self.archivo_excel:
            return self.archivo_excel.name.split('/')[-1]
        return 'Sin archivo Excel'

    def get_nombre_archivo_pdf(self):
        """Devuelve el nombre de `archivo_pdf` o un marcador si no existe."""
        if self.archivo_pdf:
            return self.archivo_pdf.name.split('/')[-1]
        return 'Sin archivo PDF'


class ReporteAportesTotales(models.Model):
    """
    Modelo para almacenar los totales de aportes de Organización y Fondo.
    
    Este modelo calcula y almacena los totales de aportes para reportes
    periódicos, permitiendo exportación a Excel y PDF.
    """
    
    # Período del reporte
    anio = models.IntegerField(
        help_text="Año del reporte"
    )
    mes = models.IntegerField(
        help_text="Mes del reporte (1-12)"
    )
    
    # Totales calculados
    total_organizacion = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Total de aportes de Organización del período"
    )
    total_famecor = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Total de aportes FAMECOR del período"
    )
    total_general = models.DecimalField(
        max_digits=15, 
        decimal_places=2, 
        default=Decimal('0.00'),
        help_text="Total general de todos los aportes"
    )
    
    # Contadores
    cantidad_afiliados = models.IntegerField(
        default=0,
        help_text="Cantidad de afiliados con aportes en el período"
    )
    cantidad_aportes_organizacion = models.IntegerField(
        default=0,
        help_text="Cantidad de aportes de Organización procesados"
    )
    cantidad_aportes_famecor = models.IntegerField(
        default=0,
        help_text="Cantidad de aportes FAMECOR procesados"
    )
    
    # Control
    fecha_calculo = models.DateTimeField(
        auto_now_add=True,
        help_text="Fecha y hora cuando se calcularon los totales"
    )
    calculado_por = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True,
        help_text="Usuario que generó el cálculo"
    )
    
    # Archivos generados
    archivo_excel = models.FileField(
        upload_to='reportes/aportes_totales/',
        null=True,
        blank=True,
        help_text="Archivo Excel con el reporte detallado"
    )
    archivo_pdf = models.FileField(
        upload_to='reportes/aportes_totales/',
        null=True,
        blank=True,
        help_text="Archivo PDF con el reporte detallado"
    )
    
    class Meta:
        verbose_name = "Reporte de Totales de Aportes"
        verbose_name_plural = "Reportes de Totales de Aportes"
        ordering = ['-anio', '-mes', '-fecha_calculo']
        unique_together = ['anio', 'mes']
        
    def __str__(self):
        """
        Representación en cadena del reporte de totales.
        
        Returns:
            str: Período y totales formateados
        """
        return f"Reporte {self.mes:02d}/{self.anio} - Organización: ${self.total_organizacion:,.2f}, Fondo: ${self.total_famecor:,.2f}"
    
    def calcular_totales(self):
        """
        Calcula los totales de aportes para el período especificado.
        
        Este método consulta todos los aportes del período y calcula
        los totales por tipo y el gran total.
        """
        from liquidacion.models import Aporte, Sueldo
        
        # Reiniciar contadores
        self.total_organizacion = Decimal('0.00')
        self.total_famecor = Decimal('0.00')
        self.cantidad_afiliados = 0
        self.cantidad_aportes_organizacion = 0
        self.cantidad_aportes_famecor = 0
        
        # Obtener sueldos del período
        sueldos_periodo = Sueldo.objects.filter(
            anio=self.anio
        ).prefetch_related('aportes')
        
        # Procesar cada sueldo y sus aportes
        for sueldo in sueldos_periodo:
            self.cantidad_afiliados += 1
            
            for aporte in sueldo.aportes.all():
                if aporte.nombre.upper() == 'ORGANIZACION':
                    self.total_organizacion += aporte.valor
                    self.cantidad_aportes_organizacion += 1
                elif aporte.nombre.upper() == 'FONDO':
                    self.total_famecor += aporte.valor
                    self.cantidad_aportes_famecor += 1
        
        # Calcular total general
        self.total_general = self.total_organizacion + self.total_famecor
        
        # Guardar cambios
        self.save()
    
    def get_nombre_mes(self):
        """
        Obtiene el nombre del mes en español.
        
        Returns:
            str: Nombre del mes
        """
        meses = {
            1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
            5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
            9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
        }
        return meses.get(self.mes, f'Mes {self.mes}')
    
    @staticmethod
    def calcular_sueldo_desde_aportes(organizacion_valor=None, fondo_valor=None):
        """
        Calcula el sueldo neto a partir de los valores de los aportes.
        
        Fórmulas:
        - Sueldo desde Organización: sueldo = organizacion_valor / 0.01
        - Sueldo desde Fondo: sueldo = fondo_valor / 0.002
        - Si ambos valores están disponibles, usa el promedio
        
        Args:
            organizacion_valor (Decimal/float): Valor del aporte Organización (1% del sueldo)
            fondo_valor (Decimal/float): Valor del aporte Fondo (0.2% del sueldo)
            
        Returns:
            Decimal: Sueldo neto calculado o None si no hay datos
        """
        from decimal import Decimal, InvalidOperation
        
        sueldo_organizacion = None
        sueldo_fondo = None
        
        # Calcular sueldo desde Organización (1% = 0.01)
        if organizacion_valor and organizacion_valor > 0:
            try:
                sueldo_organizacion = Decimal(str(organizacion_valor)) / Decimal('0.01')
            except (InvalidOperation, TypeError, ZeroDivisionError):
                sueldo_organizacion = None
        
        # Calcular sueldo desde Fondo (0.2% = 0.002)
        if fondo_valor and fondo_valor > 0:
            try:
                sueldo_fondo = Decimal(str(fondo_valor)) / Decimal('0.002')
            except (InvalidOperation, TypeError, ZeroDivisionError):
                sueldo_fondo = None
        
        # Determinar el sueldo final
        if sueldo_organizacion and sueldo_fondo:
            # Si ambos valores están disponibles, usar promedio
            return (sueldo_organizacion + sueldo_fondo) / Decimal('2')
        elif sueldo_organizacion:
            return sueldo_organizacion
        elif sueldo_fondo:
            return sueldo_fondo
        else:
            return None
    
    def actualizar_sueldos_desde_aportes(self):
        """
        Actualiza los sueldos de los afiliados basándose en sus aportes.
        
        Este método recorre todos los aportes del período y calcula/actualiza
        el sueldo neto correspondiente cuando es 0 o None.
        
        Optimizado para procesar en batch y reducir consultas a la base de datos.
        """
        from liquidacion.models import Aporte, Sueldo
        from django.db import transaction
        from decimal import Decimal
        
        # Obtener todos los sueldos del período que necesitan actualización
        sueldos_a_actualizar = Sueldo.objects.filter(
            anio=self.anio
        ).filter(
            models.Q(sueldo_neto__isnull=True) | models.Q(sueldo_neto=0)
        ).prefetch_related('aportes')
        
        sueldos_actualizados = 0
        sueldos_no_actualizables = 0
        
        # Preparar lista para actualización en batch
        sueldos_para_guardar = []
        
        for sueldo in sueldos_a_actualizar:
            # Obtener aportes Organización y Fondo de este sueldo
            organizacion_valor = Decimal('0')
            fondo_valor = Decimal('0')
            
            for aporte in sueldo.aportes.all():
                if aporte.nombre.upper() == 'ORGANIZACION':
                    organizacion_valor = aporte.valor
                elif aporte.nombre.upper() == 'FONDO':
                    fondo_valor = aporte.valor
            
            # Calcular sueldo desde aportes
            sueldo_calculado = self.calcular_sueldo_desde_aportes(
                organizacion_valor=organizacion_valor,
                fondo_valor=fondo_valor
            )
            
            if sueldo_calculado and sueldo_calculado > 0:
                sueldo.sueldo_neto = sueldo_calculado
                sueldos_para_guardar.append(sueldo)
                sueldos_actualizados += 1
            else:
                sueldos_no_actualizables += 1
        
        # Actualizar en batch para mayor eficiencia
        if sueldos_para_guardar:
            with transaction.atomic():
                Sueldo.objects.bulk_update(sueldos_para_guardar, ['sueldo_neto'], batch_size=100)
        
        return {
            'sueldos_actualizados': sueldos_actualizados,
            'sueldos_no_actualizables': sueldos_no_actualizables,
            'total_procesados': len(sueldos_a_actualizar)
        }
    
    def get_porcentaje_organizacion(self):
        """
        Calcula el porcentaje que representa Organización del total.
        
        Returns:
            Decimal: Porcentaje de Organización
        """
        if self.total_general > 0:
            return (self.total_organizacion / self.total_general) * 100
        return Decimal('0.00')
    
    def get_porcentaje_famecor(self):
        """
        Calcula el porcentaje que representa FAMECOR del total.
        
        Returns:
            Decimal: Porcentaje de FAMECOR
        """
        if self.total_general > 0:
            return (self.total_famecor / self.total_general) * 100
        return Decimal('0.00')
