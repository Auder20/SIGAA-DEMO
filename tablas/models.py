from django.db import models

class TablaSalarial(models.Model):
    """
    Tabla salarial alternativa en el app 'tablas'.
    
    NOTA: Este modelo parece ser una duplicación del modelo TablaSalarial
    en liquidacion.models. Se recomienda revisar si es necesario mantener
    ambos modelos o consolidar en uno solo para evitar inconsistencias.
    
    Almacena salarios base por grado y año de forma simplificada.
    """
    anio = models.IntegerField(
        help_text="Año de vigencia de la tabla salarial"
    )
    grado = models.CharField(
        max_length=10,
        help_text="Grado del escalafón docente"
    )
    salario_base = models.DecimalField(
        max_digits=12, 
        decimal_places=2,
        help_text="Salario base para el grado y año especificado"
    )

    class Meta:
        unique_together = ('anio', 'grado')
        verbose_name = "Tabla Salarial (Tablas)"
        verbose_name_plural = "Tablas Salariales (Tablas)"
        ordering = ['anio', 'grado']

    def __str__(self):
        """
        Representación en cadena de la tabla salarial.
        
        Returns:
            str: Año y grado de la tabla salarial
        """
        return f"{self.anio} - Grado {self.grado}"

class Bonificacion(models.Model):
    """
    Bonificaciones generales por año en el app 'tablas'.
    
    NOTA: Este modelo parece ser una duplicación del modelo Bonificacion
    en liquidacion.models. Se recomienda revisar la arquitectura para
    evitar duplicación de funcionalidad.
    
    Define bonificaciones adicionales que pueden aplicarse por año.
    """
    anio = models.IntegerField(
        help_text="Año de vigencia de la bonificación"
    )
    descripcion = models.CharField(
        max_length=100,
        help_text="Descripción de la bonificación"
    )
    porcentaje = models.DecimalField(
        max_digits=5, 
        decimal_places=2,
        help_text="Porcentaje de bonificación a aplicar"
    )

    class Meta:
        verbose_name = "Bonificación (Tablas)"
        verbose_name_plural = "Bonificaciones (Tablas)"
        ordering = ['anio', 'descripcion']

    def __str__(self):
        """
        Representación en cadena de la bonificación.
        
        Returns:
            str: Descripción y año de la bonificación
        """
        return f"{self.descripcion} ({self.anio})"
