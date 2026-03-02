from django.db import models
from afiliados.models import Afiliado
from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator


class TablaSalarial(models.Model):
    """
    Tabla salarial que define los salarios base por grado de escalafón y año.
    
    Almacena los salarios base oficiales para cada grado del escalafón docente
    por año. Incluye lógica para calcular aumentos automáticos por grado y
    el sueldo total con bonificaciones.
    
    El sistema de grados va desde 'A', 'B' hasta '1'-'14', donde cada grado
    tiene un salario base y un aumento específico definido por normativa.
    """
    anio = models.IntegerField(
        help_text="Año de vigencia de la tabla salarial"
    )
    grado = models.CharField(
        max_length=10,
        help_text="Grado del escalafón docente (A, B, 1-14)"
    )
    salario_base = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        help_text="Salario base oficial para el grado y año"
    )
    
    # Sueldo calculado automáticamente
    sueldo_con_bonificacion = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Salario base + aumento por grado (calculado automáticamente)"
    )

    class Meta:
        unique_together = ('anio', 'grado')
        verbose_name = "Tabla Salarial"
        verbose_name_plural = "Tablas Salariales"
        ordering = ['anio', 'grado']

    def __str__(self):
        """
        Representación en cadena de la tabla salarial.
        
        Returns:
            str: Año y grado de la tabla salarial
        """
        return f"{self.anio} - Grado {self.grado}"

    def calcular_aumento_por_grado(self):
        """
        Calcula el aumento fijo por grado según normativa institucional.
        
        Cada grado del escalafón docente tiene un aumento fijo definido
        por la normativa institucional que se suma al salario base.
        
        Returns:
            Decimal: Monto del aumento correspondiente al grado
            
        Note:
            Los montos están definidos por resolución institucional y
            pueden requerir actualización periódica según normativa.
        """
        aumentos = {
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
        }
        return aumentos.get(self.grado.upper(), Decimal('0'))

    def calcular_sueldo_con_bonificacion(self):
        """
        Calcula el sueldo total sumando salario base + aumento por grado.
        
        Este es el sueldo base que se usa como referencia para calcular
        las bonificaciones adicionales por cargo, antigüedad y educación.
        
        Returns:
            Decimal: Sueldo base total (salario_base + aumento_por_grado)
        """
        salario_base = self.salario_base or Decimal('0')
        aumento = self.calcular_aumento_por_grado()
        return salario_base + aumento

    def save(self, *args, **kwargs):
        """
        Guarda la tabla salarial calculando automáticamente el sueldo con bonificación.
        
        Sobrescribe el método save para asegurar que siempre se calcule
        el sueldo_con_bonificacion antes de guardar el registro.
        """
        # Calcular automáticamente el sueldo_con_bonificacion
        if not self.sueldo_con_bonificacion:
            self.sueldo_con_bonificacion = self.calcular_sueldo_con_bonificacion()
        super().save(*args, **kwargs)


class Bonificacion(models.Model):
    """
    Modelo para definir bonificaciones generales por año.
    
    Almacena bonificaciones adicionales que pueden aplicarse
    a los sueldos según criterios específicos. Este modelo
    complementa las bonificaciones automáticas del sistema.
    """
    anio = models.IntegerField(
        help_text="Año de vigencia de la bonificación"
    )
    descripcion = models.CharField(
        max_length=100,
        help_text="Descripción de la bonificación (ej: Bonificación especial COVID)"
    )
    porcentaje = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        help_text="Porcentaje de bonificación a aplicar"
    )

    class Meta:
        verbose_name = "Bonificación"
        verbose_name_plural = "Bonificaciones"
        ordering = ['anio', 'descripcion']

    def __str__(self):
        """
        Representación en cadena de la bonificación.
        
        Returns:
            str: Descripción y año de la bonificación
        """
        return f"{self.descripcion} ({self.anio})"


class Sueldo(models.Model):
    """
    Registro del sueldo calculado para un afiliado en un año específico.
    
    Almacena el resultado final del cálculo de sueldo que incluye:
    - Salario base según grado de escalafón
    - Bonificaciones por cargo, antigüedad y educación
    - Bonificaciones adicionales si aplican
    
    Este modelo es el resultado del proceso de cálculo automático
    y sirve como base para generar aportes y reportes.
    """
    afiliado = models.ForeignKey(
        Afiliado, 
        on_delete=models.CASCADE,
        help_text="Afiliado al que pertenece este sueldo"
    )
    anio = models.IntegerField(
        help_text="Año del sueldo calculado"
    )
    sueldo_neto = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        help_text="Sueldo neto final calculado con todas las bonificaciones"
    )
    tabla_salarial = models.ForeignKey(
        TablaSalarial, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        help_text="Tabla salarial usada como base para el cálculo"
    )

    class Meta:
        unique_together = ('afiliado', 'anio')
        verbose_name = "Sueldo"
        verbose_name_plural = "Sueldos"
        ordering = ['-anio', 'afiliado__nombre_completo']

    def __str__(self):
        """
        Representación en cadena del sueldo.
        
        Returns:
            str: Afiliado y año del sueldo
        """
        return f"{self.afiliado} - {self.anio}"

   
    def recalculate_aportes(self):
        """
        Recalcula los aportes ADEMACOR y FAMECOR basados en el sueldo neto.
        
        Elimina los aportes existentes y crea nuevos registros con los
        porcentajes establecidos:
        - ADEMACOR: 1.00% del sueldo neto
        - FAMECOR: 0.20% del sueldo neto
        
        Este método se ejecuta automáticamente cuando se guarda un sueldo
        o puede llamarse manualmente para recalcular aportes.
        """
        from .models import Aporte  # local import para evitar circulares
        # Eliminar aportes anteriores
        Aporte.objects.filter(sueldo=self).delete()
        # Crear aportes nuevos usando Decimal para precisión monetaria
        value = Decimal(self.sueldo_neto)
        Aporte.objects.create(
            sueldo=self, 
            nombre='ADEMACOR', 
            porcentaje=Decimal('1.00'), 
            valor=(value * Decimal('0.01'))
        )
        Aporte.objects.create(
            sueldo=self, 
            nombre='FAMECOR', 
            porcentaje=Decimal('0.20'), 
            valor=(value * Decimal('0.002'))
        )


class Aporte(models.Model):
    """
    Registro de aportes calculados sobre el sueldo de un afiliado.
    
    Almacena los aportes obligatorios que se descuentan del sueldo:
    - ADEMACOR: Aporte a la asociación de docentes (1.00%)
    - FAMECOR: Aporte familiar (0.20%)
    
    Los aportes se calculan automáticamente cuando se crea o actualiza
    un registro de sueldo.
    """
    sueldo = models.ForeignKey(
        'Sueldo', 
        on_delete=models.CASCADE, 
        related_name='aportes',
        help_text="Sueldo sobre el cual se calcula el aporte"
    )
    nombre = models.CharField(
        max_length=50,
        help_text="Nombre del aporte (ADEMACOR o FAMECOR)"
    )
    porcentaje = models.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        default=0,
        help_text="Porcentaje del aporte sobre el sueldo neto"
    )
    valor = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        help_text="Valor calculado del aporte en pesos"
    )

    class Meta:
        verbose_name = "Aporte"
        verbose_name_plural = "Aportes"
        ordering = ['sueldo', 'nombre']

    def __str__(self):
        """
        Representación en cadena del aporte.
        
        Returns:
            str: Nombre del aporte y valor
        """
        return f"{self.nombre} - ${self.valor}"


class BonificacionPago(models.Model):
    """
    Registro histórico de bonificaciones aplicadas a un sueldo específico.
    
    Almacena el detalle de cada bonificación calculada y aplicada a un sueldo,
    incluyendo el porcentaje y monto exacto. Permite mantener un historial
    detallado de cómo se compuso cada sueldo para auditoría y reportes.
    
    Cada registro representa una bonificación específica (cargo, antigüedad,
    educación, etc.) aplicada a un sueldo en un año determinado.
    """
    sueldo = models.ForeignKey(
        Sueldo, 
        on_delete=models.CASCADE, 
        related_name='bonificaciones',
        help_text="Sueldo al que se aplica esta bonificación"
    )
    anio = models.IntegerField(
        help_text="Año en que se aplicó la bonificación"
    )
    descripcion = models.CharField(
        max_length=150, 
        null=True, 
        blank=True,
        help_text="Descripción del tipo de bonificación (cargo, antigüedad, educación, etc.)"
    )
    porcentaje = models.DecimalField(
        max_digits=6, 
        decimal_places=2, 
        default=0,
        help_text="Porcentaje de bonificación aplicado sobre el salario base"
    )
    monto = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        default=0,
        help_text="Monto calculado de la bonificación en pesos"
    )

    class Meta:
        verbose_name = "Bonificación de Pago"
        verbose_name_plural = "Bonificaciones de pago"
        unique_together = ('sueldo', 'descripcion')
        ordering = ['anio', 'sueldo__afiliado__nombre_completo']

    def __str__(self):
        """
        Representación en cadena de la bonificación de pago.
        
        Returns:
            str: Descripción, monto y año de la bonificación
        """
        return f"Bonificación {self.descripcion or 'Sin descripción'} - ${self.monto} ({self.anio})"


class ParametroLiquidacion(models.Model):
    """
    Parámetros configurables para los cálculos de liquidación.
    
    Permite modificar los porcentajes y valores utilizados en los cálculos
    de sueldos y aportes sin necesidad de modificar el código.
    """
    TIPO_APORTE = 'APORTE'
    TIPO_BONIFICACION = 'BONIF'
    TIPO_OTRO = 'OTRO'
    
    TIPO_CHOICES = [
        (TIPO_APORTE, 'Aporte'),
        (TIPO_BONIFICACION, 'Bonificación'),
        (TIPO_OTRO, 'Otro'),
    ]
    
    codigo = models.CharField(
        max_length=50,
        unique=True,
        help_text="Código único del parámetro (ej: APORTE_ADEMACOR, BONIF_ANTIGUEDAD)"
    )
    
    nombre = models.CharField(
        max_length=100,
        help_text="Nombre descriptivo del parámetro"
    )
    
    tipo = models.CharField(
        max_length=10,
        choices=TIPO_CHOICES,
        default=TIPO_OTRO,
        help_text="Tipo de parámetro"
    )
    
    valor_numerico = models.DecimalField(
        max_digits=10,
        decimal_places=4,
        null=True,
        blank=True,
        help_text="Valor numérico del parámetro (para porcentajes o valores fijos)"
    )
    
    valor_texto = models.TextField(
        null=True,
        blank=True,
        help_text="Valor de texto del parámetro (para descripciones o valores no numéricos)"
    )
    
    anio_vigencia = models.IntegerField(
        help_text="Año de vigencia del parámetro (0 para parámetros permanentes)",
        default=0
    )
    
    activo = models.BooleanField(
        default=True,
        help_text="Indica si el parámetro está activo y debe ser considerado en los cálculos"
    )
    
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.nombre} ({self.codigo}): {self.valor_numerico or self.valor_texto}"
    
    class Meta:
        verbose_name = "Parámetro de Liquidación"
        verbose_name_plural = "Parámetros de Liquidación"
        ordering = ['tipo', 'codigo']
    
    @classmethod
    def obtener_valor(cls, codigo, anio=None, default=0):
        """
        Obtiene el valor de un parámetro por su código y año.
        
        Args:
            codigo (str): Código del parámetro a buscar
            anio (int, optional): Año de vigencia. Si es None, busca parámetros sin año.
            default: Valor por defecto si no se encuentra el parámetro
            
        Returns:
            El valor del parámetro o el valor por defecto si no se encuentra
        """
        try:
            if anio is not None:
                # Buscar primero por año específico
                parametro = cls.objects.filter(
                    codigo=codigo, 
                    anio_vigencia=anio,
                    activo=True
                ).first()
                
                if parametro is not None:
                    return parametro.valor_numerico or parametro.valor_texto or default
            
            # Si no se especificó año o no se encontró con año, buscar sin año
            parametro = cls.objects.filter(
                codigo=codigo,
                anio_vigencia=0,  # Parámetro permanente
                activo=True
            ).first()
            
            if parametro is not None:
                return parametro.valor_numerico or parametro.valor_texto or default
                
            return default
            
        except (cls.DoesNotExist, Exception):
            return default
    
    @classmethod
    def aplicar_aumento_porcentual(cls, codigo, porcentaje, anio=None, actualizar_existente=True):
        """
        Aplica un aumento porcentual a un parámetro numérico.
        
        Args:
            codigo (str): Código del parámetro a actualizar
            porcentaje (float): Porcentaje de aumento (ej: 10 para 10%)
            anio (int, optional): Año de vigencia. Si es None, actualiza parámetros sin año.
            actualizar_existente (bool): Si es True, actualiza el parámetro existente. Si es False, crea uno nuevo.
            
        Returns:
            bool: True si se aplicó el aumento correctamente, False en caso contrario
        """
        try:
            if anio is None:
                anio = 0
                
            parametro = None
            if actualizar_existente:
                # Buscar parámetro existente
                parametro = cls.objects.filter(
                    codigo=codigo,
                    anio_vigencia=anio
                ).first()
            
            if parametro is None and actualizar_existente:
                return False
                
            if parametro is None:
                # Crear nuevo parámetro
                parametro = cls(
                    codigo=codigo,
                    nombre=f"{codigo.replace('_', ' ').title()}",
                    anio_vigencia=anio
                )
                
                # Si no existe, intentar copiar de un parámetro base (sin año)
                if anio != 0:
                    base = cls.objects.filter(
                        codigo=codigo,
                        anio_vigencia=0
                    ).first()
                    if base:
                        parametro.nombre = base.nombre
                        parametro.tipo = base.tipo
                        parametro.valor_numerico = base.valor_numerico
                        parametro.valor_texto = base.valor_texto
            
            if parametro.valor_numerico is not None:
                # Aplicar aumento porcentual al valor numérico
                aumento = 1 + (Decimal(str(porcentaje)) / 100)
                nuevo_valor = parametro.valor_numerico * aumento
                parametro.valor_numerico = nuevo_valor.quantize(Decimal('0.0001'))
            
            parametro.save()
            return True
            
        except Exception as e:
            print(f"Error al aplicar aumento porcentual: {str(e)}")
            return False


class SueldoAdemacor(models.Model):
    """
    Registro del sueldo calculado para un afiliado ADEMACOR en un año específico.
    
    Estructura paralela a Sueldo pero vinculada a DatosAdemacor.
    Almacena el resultado final del cálculo de sueldo que incluye:
    - Salario base según grado de escalafón
    - Bonificaciones por cargo, antigüedad y educación
    - Bonificaciones adicionales si aplican
    
    Este modelo permite mantener sueldos separados para ADEMACOR
    y comparar con los sueldos generales.
    """
    afiliado_ademacor = models.ForeignKey(
        'afiliados.DatosAdemacor',
        on_delete=models.CASCADE,
        related_name='sueldos_ademacor',
        help_text="Afiliado ADEMACOR al que pertenece este sueldo"
    )
    anio = models.IntegerField(
        help_text="Año del sueldo calculado"
    )
    sueldo_neto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Sueldo neto final calculado con todas las bonificaciones"
    )
    tabla_salarial = models.ForeignKey(
        TablaSalarial,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        help_text="Tabla salarial usada como base para el cálculo"
    )

    class Meta:
        unique_together = ('afiliado_ademacor', 'anio')
        verbose_name = "Sueldo ADEMACOR"
        verbose_name_plural = "Sueldos ADEMACOR"
        ordering = ['-anio', 'afiliado_ademacor__nombre_completo']

    def __str__(self):
        """
        Representación en cadena del sueldo ADEMACOR.
        
        Returns:
            str: Afiliado y año del sueldo
        """
        return f"{self.afiliado_ademacor} - {self.anio}"

    def recalculate_aportes(self):
        """
        Recalcula los aportes ADEMACOR y FAMECOR basados en el sueldo neto.
        
        Elimina los aportes existentes y crea nuevos registros con los
        porcentajes establecidos:
        - ADEMACOR: 1.00% del sueldo neto
        - FAMECOR: 0.20% del sueldo neto
        
        Este método se ejecuta automáticamente cuando se guarda un sueldo
        o puede llamarse manualmente para recalcular aportes.
        """
        # Eliminar aportes anteriores
        AporteAdemacor.objects.filter(sueldo_ademacor=self).delete()
        # Crear aportes nuevos usando Decimal para precisión monetaria
        value = Decimal(self.sueldo_neto)
        AporteAdemacor.objects.create(
            sueldo_ademacor=self,
            nombre='ADEMACOR',
            porcentaje=Decimal('1.00'),
            valor=(value * Decimal('0.01'))
        )
        AporteAdemacor.objects.create(
            sueldo_ademacor=self,
            nombre='FAMECOR',
            porcentaje=Decimal('0.20'),
            valor=(value * Decimal('0.002'))
        )


class AporteAdemacor(models.Model):
    """
    Registro de aportes calculados sobre el sueldo de un afiliado ADEMACOR.
    
    Estructura paralela a Aporte pero vinculada a SueldoAdemacor.
    Almacena los aportes obligatorios que se descuentan del sueldo:
    - ADEMACOR: Aporte a la asociación de docentes (1.00%)
    - FAMECOR: Aporte familiar (0.20%)
    
    Los aportes se calculan automáticamente cuando se crea o actualiza
    un registro de SueldoAdemacor.
    """
    sueldo_ademacor = models.ForeignKey(
        SueldoAdemacor,
        on_delete=models.CASCADE,
        related_name='aportes',
        help_text="Sueldo ADEMACOR sobre el cual se calcula el aporte"
    )
    nombre = models.CharField(
        max_length=50,
        help_text="Nombre del aporte (ADEMACOR o FAMECOR)"
    )
    porcentaje = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        help_text="Porcentaje del aporte sobre el sueldo neto"
    )
    valor = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Valor calculado del aporte en pesos"
    )

    class Meta:
        verbose_name = "Aporte ADEMACOR"
        verbose_name_plural = "Aportes ADEMACOR"
        ordering = ['sueldo_ademacor', 'nombre']

    def __str__(self):
        """
        Representación en cadena del aporte ADEMACOR.
        
        Returns:
            str: Nombre del aporte y valor
        """
        return f"{self.nombre} - ${self.valor}"


class BonificacionPagoAdemacor(models.Model):
    """
    Registro histórico de bonificaciones aplicadas a un sueldo ADEMACOR específico.
    
    Estructura paralela a BonificacionPago pero vinculada a SueldoAdemacor.
    Almacena el detalle de cada bonificación calculada y aplicada a un sueldo,
    incluyendo el porcentaje y monto exacto. Permite mantener un historial
    detallado de cómo se compuso cada sueldo para auditoría y reportes.
    """
    sueldo_ademacor = models.ForeignKey(
        SueldoAdemacor,
        on_delete=models.CASCADE,
        related_name='bonificaciones',
        help_text="Sueldo ADEMACOR al que se aplica esta bonificación"
    )
    anio = models.IntegerField(
        help_text="Año en que se aplicó la bonificación"
    )
    descripcion = models.CharField(
        max_length=150,
        null=True,
        blank=True,
        help_text="Descripción del tipo de bonificación (cargo, antigüedad, educación, etc.)"
    )
    porcentaje = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=0,
        help_text="Porcentaje de bonificación aplicado sobre el salario base"
    )
    monto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="Monto calculado de la bonificación en pesos"
    )

    class Meta:
        verbose_name = "Bonificación de Pago ADEMACOR"
        verbose_name_plural = "Bonificaciones de Pago ADEMACOR"
        unique_together = ('sueldo_ademacor', 'descripcion')
        ordering = ['anio', 'sueldo_ademacor__afiliado_ademacor__nombre_completo']

    def __str__(self):
        """
        Representación en cadena de la bonificación de pago ADEMACOR.
        
        Returns:
            str: Descripción, monto y año de la bonificación
        """
        return f"Bonificación {self.descripcion or 'Sin descripción'} - ${self.monto} ({self.anio})"