"""
Backup of tablas.models before consolidation into liquidacion.models
"""
from django.db import models

class TablaSalarial(models.Model):
    anio = models.IntegerField()
    grado = models.CharField(max_length=10)
    salario_base = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        unique_together = ('anio', 'grado')

    def __str__(self):
        return f"{self.anio} - {self.grado}"

class Bonificacion(models.Model):
    anio = models.IntegerField()
    descripcion = models.CharField(max_length=100)
    porcentaje = models.DecimalField(max_digits=5, decimal_places=2)

    def __str__(self):
        return f"{self.descripcion} ({self.anio})"
