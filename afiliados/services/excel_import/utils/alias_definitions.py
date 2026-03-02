from typing import Dict, List


class AliasDefinitions:
    """
    Definiciones de alias para mapeo de columnas.
    """
    
    @staticmethod
    def get_column_aliases() -> Dict[str, List[str]]:
        """Devuelve un diccionario: canonical_name -> lista de alias posibles."""
        return {
            'cedula': ['cedula', 'identificacion', 'dni', 'id', 'documento'],
            'nombre_completo': ['nombre_completo', 'nombre completo', 'nombre', 'nombres', 
                              'nombre_apellidos', 'nombre_com', 'bre_com', 'nombrecompleto'],
            'ciudad_de_nacimiento': ['ciudad_de_nacimiento', 'ciudad nacimiento', 'ciudad', 
                                   'ciudad_de_naci', 'ciudad_nacimiento', 'lugar_nacimiento'],
            'fecha_nacimiento': ['fecha_nacimiento', 'fecha de nacimiento', 'nacimiento', 
                               'fecha_naci', 'fech_nacimiento'],
            'edad': ['edad'],
            'estado_civil': ['estado_civil', 'estado civil', 'estado_c', 'estadocivil'],
            'nombre_conyuge': ['nombre_conyuge', 'nombre conyuge', 'nombre_cony', 'conyuge', 
                             'nombre_conyugue', 'conyugue'],
            'nombre_hijos': ['numero_hijos', 'num_hijos', 'n_hijos', 'numero de hijos', 
                           'nombre_hijos', 'nombres_hijos', 'nombre de los hijos', 'hijos'],
            'direccion': ['direccion', 'direccion_vivienda', 'direccion_viv', 'dir'],
            'telefono': ['telefono', 'telefono_cel', 'telefono_celular', 'celular', 'tel'],
            'email': ['email', 'correo', 'correo_electronico', 'email_address', 'mail'],
            'institucion': ['institucion', 'institucion_educativa', 'institucion_lab', 'inst'],
            'municipio': ['municipio', 'municipio_labora', 'municipio_lab', 'ciudad', 'mpio'],
            'titulo_posgrado': ['titulo_posgrado', 'titulo posgrado', 'titulo_pos', 
                              'titulos_posgrados', 'posgrado'],
            'estudios_posgrado': ['estudios_posgrado', 'estudios posgrado', 'estudios_posgrados', 
                                'estudios_pregrado', 'estudios'],
            'otros_titulos': ['otros_titulos', 'otros titulos', 'otros_titulos', 'titulos_adicionales'],
            'años_de_servicio_docente': ['años_de_servicio_docente', 'anos_de_servicio_docente', 
                                       'anos servicio', 'anos_de_servicio', 'anios_servicio', 
                                       'servicio_docente'],
            'ultimo_cargo': ['ultimo_cargo', 'ultimo cargo', 'ultimo_carg', 'cargo_actual'],
            'experiencia_docente': ['experiencia_docente', 'experiencia docente', 
                                  'experiencia_doc', 'experiencia'],
            'cargos_desempenñados': ['cargos_desempenñados', 'cargos_desempenados', 
                                   'cargos desempeñados', 'cargos', 'cargos_anteriores'],
            'grado_escalafon': ['grado_escalafon', 'grado escalafon', 'grado', 'escalafon'],
            'fecha_ingreso': ['fecha_ingreso', 'fecha de ingreso', 'ingreso', 
                            'fecha_ingreso', 'fech_ingreso'],
            'activo': ['activo', 'activo_', 'estado', 'vigente'],
            'bonificacion': ['bonificacion', 'bonificación', 'bonificacion_descripcion', 
                           'bonificacion_valor', 'bonificacion_porcentaje'],
            'anio': ['anio', 'año', 'year', 'periodo'],
            'sueldo_neto': ['sueldo_neto', 'sueldo', 'salario', 'salario_neto', 'sueldo_mensual'],
        }
    
    @staticmethod
    def get_no_header_column_mapping() -> Dict[int, str]:
        """
        Mapeo de columnas para Excel sin encabezados.
        La numeración comienza desde 0 (primera columna = 0)
        """
        return {
            0: 'cedula',        # Primera columna: Cédula
            1: 'nombre_completo', # Segunda columna: Nombre completo
            2: 'municipio'      # Tercera columna: Municipio
        }
