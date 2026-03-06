from afiliados.models import Afiliado, DatosOrganizacion
from django.db.models import Q

def comparar_afiliados_ademacor(municipio_filtro=None):
    """
    Compara los registros de Afiliados (General) con DatosAdemacor.
    Retorna un diccionario con las diferencias encontradas.
    """

    # Obtener querysets base
    afiliados_qs = Afiliado.objects.all()
    ademacor_qs = DatosOrganizacion.objects.all()

    if municipio_filtro:
        afiliados_qs = afiliados_qs.filter(municipio=municipio_filtro)
        ademacor_qs = ademacor_qs.filter(municipio=municipio_filtro)

    # Optimizar consultas obteniendo solo campos necesarios
    afiliados_data = {
        a.cedula: {
            'nombre': a.nombre_completo,
            'municipio': a.municipio,
            'origen': 'GENERAL'
        }
        for a in afiliados_qs.only('cedula', 'nombre_completo', 'municipio')
    }

    ademacor_data = {
        a.cedula: {
            'nombre': a.nombre_completo,
            'municipio': a.municipio,
            'origen': 'ADEMACOR'
        }
        for a in DatosOrganizacion.objects.only('cedula', 'nombre_completo', 'municipio')
    }

    # Identificar diferencias
    cedulas_general = set(afiliados_data.keys())
    cedulas_ademacor = set(ademacor_data.keys())

    solo_general = cedulas_general - cedulas_ademacor
    solo_ademacor = cedulas_ademacor - cedulas_general
    ambos = cedulas_general & cedulas_ademacor

    resultados = {
        'solo_general': [],
        'solo_ademacor': [],
        'diferencias_datos': [], # Están en ambos pero con datos diferentes (ej. municipio)
        'coincidencias': []
    }

    # Procesar Solo General
    for cedula in solo_general:
        resultados['solo_general'].append({
            'cedula': cedula,
            **afiliados_data[cedula]
        })

    # Procesar Solo Ademacor
    for cedula in solo_ademacor:
        resultados['solo_ademacor'].append({
            'cedula': cedula,
            **ademacor_data[cedula]
        })

    # Procesar Ambos
    for cedula in ambos:
        dato_gral = afiliados_data[cedula]
        dato_adem = ademacor_data[cedula]

        # Comparar municipio (normalizando a mayúsculas y quitando espacios)
        mun_gral = (dato_gral['municipio'] or '').strip().upper()
        mun_adem = (dato_adem['municipio'] or '').strip().upper()

        if mun_gral != mun_adem:
            resultados['diferencias_datos'].append({
                'cedula': cedula,
                'nombre_general': dato_gral['nombre'],
                'nombre_ademacor': dato_adem['nombre'],
                'municipio_general': dato_gral['municipio'],
                'municipio_ademacor': dato_adem['municipio']
            })
        else:
            resultados['coincidencias'].append({
                'cedula': cedula,
                'nombre': dato_gral['nombre'],
                'municipio': dato_gral['municipio']
            })

    return resultados
