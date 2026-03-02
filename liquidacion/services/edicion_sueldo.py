"""
Servicio para editar el sueldo y bonificación de un afiliado desde la web.

Uso:
    from liquidacion.services.edicion_sueldo import actualizar_sueldo
    actualizar_sueldo(sueldo, nuevo_valor, nueva_bonificacion)
"""

def actualizar_sueldo(sueldo, nuevo_valor, nueva_bonificacion=None):
    """
    Actualiza el sueldo y la bonificación de un registro Sueldo.
    """
    sueldo.sueldo_neto = nuevo_valor
    sueldo.save()
    if nueva_bonificacion is not None:
        # Si el sueldo tiene bonificación relacionada, actualizarla
        bonificaciones = sueldo.afiliado.bonificacion_set.filter(anio=sueldo.anio)
        for bonificacion in bonificaciones:
            bonificacion.porcentaje = nueva_bonificacion
            bonificacion.save()
    return sueldo
