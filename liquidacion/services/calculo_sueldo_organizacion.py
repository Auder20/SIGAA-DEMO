from decimal import Decimal
from afiliados.models import DatosOrganizacion
from liquidacion.models import (
    TablaSalarial, SueldoOrganizacion, BonificacionPagoOrganizacion, ParametroLiquidacion
)


class CalculadorSueldoOrganizacion:
    """
    Calculadora de sueldos para afiliados de organización externa.
    
    Utiliza la misma lógica que CalculadorSueldo pero opera sobre
    el modelo DatosOrganizacion en lugar de Afiliado.
    """
    
    def __init__(self, afiliado_organizacion, anio=2025):
        """
        Inicializa la calculadora con un afiliado de organización externa y año.
        
        Args:
            afiliado_organizacion (DatosOrganizacion): Afiliado de organización externa
            anio (int): Año para el cálculo (por defecto 2025)
        """
        self.afiliado = afiliado_organizacion
        self.anio = anio
        self.errores = []
        
    def calcular_sueldo_neto(self, cargo_especifico=None, bonificaciones_adicionales=None):
        """
        Calcula el sueldo neto completo para un afiliado de organización externa.
        
        Args:
            cargo_especifico (str, optional): Cargo específico para bonificación
            bonificaciones_adicionales (dict, optional): Bonificaciones extra {concepto: porcentaje}
            
        Returns:
            dict: Resultado completo del cálculo con desglose
        """
        resultado = {
            'sueldo_base': Decimal('0'),
            'bonificaciones': {},
            'total_bonificaciones': Decimal('0'),
            'sueldo_neto': Decimal('0'),
            'detalles': {},
            'errores': []
        }
        
        try:
            # 1. Obtener salario base según grado de escalafón
            salario_base = self._obtener_salario_base()
            if not salario_base:
                self.errores.append(f"No se encontró tabla salarial para grado {self.afiliado.grado_escalafon}")
                resultado['errores'] = self.errores
                return resultado
                
            resultado['sueldo_base'] = salario_base
            resultado['detalles']['salario_base'] = salario_base
            
            # 2. Calcular bonificaciones automáticas
            bonificaciones = self._calcular_bonificaciones_automaticas(cargo_especifico)
            resultado['bonificaciones'].update(bonificaciones)
            
            # 3. Agregar bonificaciones adicionales si se proporcionan
            if bonificaciones_adicionales:
                for concepto, porcentaje in bonificaciones_adicionales.items():
                    monto = salario_base * Decimal(str(porcentaje)) / Decimal('100')
                    resultado['bonificaciones'][concepto] = {
                        'porcentaje': Decimal(str(porcentaje)),
                        'monto': monto
                    }
            
            # 4. Calcular total de bonificaciones
            total_bonificaciones = sum(
                bon['monto'] for bon in resultado['bonificaciones'].values()
            )
            resultado['total_bonificaciones'] = total_bonificaciones
            
            # 5. Calcular sueldo neto
            sueldo_neto = salario_base + total_bonificaciones
            resultado['sueldo_neto'] = sueldo_neto
            resultado['detalles']['sueldo_neto'] = sueldo_neto
            
            resultado['errores'] = self.errores
            
        except Exception as e:
            self.errores.append(f"Error en cálculo: {str(e)}")
            resultado['errores'] = self.errores
            
        return resultado
    
    def _obtener_salario_base(self):
        """
        Obtiene el salario base desde la tabla salarial.
        
        Returns:
            Decimal: Salario base con aumento por grado incluido
        """
        try:
            tabla = TablaSalarial.objects.get(
                anio=self.anio,
                grado=self.afiliado.grado_escalafon
            )
            return tabla.calcular_sueldo_con_bonificacion()
        except TablaSalarial.DoesNotExist:
            return Decimal('0')
    
    def _calcular_bonificaciones_automaticas(self, cargo_especifico=None):
        """
        Calcula bonificaciones automáticas según antigüedad, educación y cargo.
        
        Args:
            cargo_especifico (str, optional): Cargo específico para bonificación
            
        Returns:
            dict: Diccionario de bonificaciones {concepto: {porcentaje, monto}}
        """
        bonificaciones = {}
        salario_base = self._obtener_salario_base()
        
        if salario_base == 0:
            return bonificaciones
        
        # Bonificación por antigüedad
        bonif_antiguedad = self._calcular_bonificacion_antiguedad(salario_base)
        if bonif_antiguedad:
            bonificaciones.update(bonif_antiguedad)
        
        # Bonificación por educación
        bonif_educacion = self._calcular_bonificacion_educacion(salario_base)
        if bonif_educacion:
            bonificaciones.update(bonif_educacion)
        
        # Bonificación por cargo
        cargo = cargo_especifico or self.afiliado.cargo_desempenado
        if cargo:
            bonif_cargo = self._calcular_bonificacion_cargo(cargo, salario_base)
            if bonif_cargo:
                bonificaciones.update(bonif_cargo)
        
        return bonificaciones
    
    def _calcular_bonificacion_antiguedad(self, salario_base):
        """
        Calcula bonificación por años de servicio.
        
        Args:
            salario_base (Decimal): Salario base para cálculo
            
        Returns:
            dict: Bonificación por antigüedad si aplica
        """
        anos_servicio = self.afiliado.anos_servicio or 0
        
        # Obtener parámetros de bonificación por antigüedad
        bonificaciones = []
        
        if anos_servicio >= 15:
            porcentaje = ParametroLiquidacion.obtener_valor('bonif_anticiguedad_15', default=15.00)
            bonificaciones.append(('antiguedad_15_anos', porcentaje))
        elif anos_servicio >= 10:
            porcentaje = ParametroLiquidacion.obtener_valor('bonif_anticiguedad_10', default=10.00)
            bonificaciones.append(('antiguedad_10_anos', porcentaje))
        elif anos_servicio >= 5:
            porcentaje = ParametroLiquidacion.obtener_valor('bonif_anticiguedad_5', default=5.00)
            bonificaciones.append(('antiguedad_5_anos', porcentaje))
        
        resultado = {}
        for concepto, porcentaje in bonificaciones:
            monto = salario_base * Decimal(str(porcentaje)) / Decimal('100')
            resultado[concepto] = {
                'porcentaje': Decimal(str(porcentaje)),
                'monto': monto
            }
        
        return resultado
    
    def _calcular_bonificacion_educacion(self, salario_base):
        """
        Calcula bonificación por nivel educativo.
        
        Args:
            salario_base (Decimal): Salario base para cálculo
            
        Returns:
            dict: Bonificación por educación si aplica
        """
        resultado = {}
        estudios = self.afiliado.estudios_posgrado or ''
        titulo_posgrado = self.afiliado.titulo_posgrado or ''
        
        # Detectar doctorado
        if any(palabra in estudios.lower() or palabra in titulo_posgrado.lower() 
               for palabra in ['doctorado', 'phd', 'doctor']):
            porcentaje = ParametroLiquidacion.obtener_valor('bonif_educacion_doctorado', default=12.00)
            monto = salario_base * Decimal(str(porcentaje)) / Decimal('100')
            resultado['educacion_doctorado'] = {
                'porcentaje': Decimal(str(porcentaje)),
                'monto': monto
            }
        # Detectar maestría
        elif any(palabra in estudios.lower() or palabra in titulo_posgrado.lower() 
                 for palabra in ['maestría', 'maestria', 'magister', 'master']):
            porcentaje = ParametroLiquidacion.obtener_valor('bonif_educacion_maestria', default=8.00)
            monto = salario_base * Decimal(str(porcentaje)) / Decimal('100')
            resultado['educacion_maestria'] = {
                'porcentaje': Decimal(str(porcentaje)),
                'monto': monto
            }
        
        return resultado
    
    def _calcular_bonificacion_cargo(self, cargo, salario_base):
        """
        Calcula bonificación por cargo desempeñado.
        
        Args:
            cargo (str): Cargo del afiliado
            salario_base (Decimal): Salario base para cálculo
            
        Returns:
            dict: Bonificación por cargo si aplica
        """
        cargo_lower = cargo.lower()
        
        # Mapeo de cargos a parámetros
        mapeo_cargos = {
            'rector': 'bonif_cargo_rector',
            'vicerrector': 'bonif_cargo_rector',  # Misma bonificación que rector
            'decano': 'bonif_cargo_decano',
            'director': 'bonif_cargo_director',
            'coordinador': 'bonif_cargo_coordinador',
        }
        
        resultado = {}
        for cargo_key, parametro in mapeo_cargos.items():
            if cargo_key in cargo_lower:
                porcentaje = ParametroLiquidacion.obtener_valor(parametro, default=0)
                if porcentaje > 0:
                    monto = salario_base * Decimal(str(porcentaje)) / Decimal('100')
                    resultado[f'cargo_{cargo_key}'] = {
                        'porcentaje': Decimal(str(porcentaje)),
                        'monto': monto
                    }
                break  # Solo una bonificación por cargo
        
        return resultado
    
    def crear_o_actualizar_sueldo(self, cargo_especifico=None, bonificaciones_adicionales=None):
        """
        Crea o actualiza el registro de sueldo en la base de datos.
        
        Args:
            cargo_especifico (str, optional): Cargo específico para bonificación
            bonificaciones_adicionales (dict, optional): Bonificaciones extra
            
        Returns:
            tuple: (SueldoOrganizacion instance, created boolean, calculo dict)
        """
        # Realizar cálculo
        calculo = self.calcular_sueldo_neto(cargo_especifico, bonificaciones_adicionales)
        
        if calculo['errores']:
            return None, False, calculo
        
        # Crear o actualizar sueldo
        sueldo, created = SueldoOrganizacion.objects.update_or_create(
            afiliado_organizacion=self.afiliado,
            anio=self.anio,
            defaults={
                'sueldo_neto': calculo['sueldo_neto']
            }
        )
        
        # Obtener tabla salarial para referencia
        try:
            tabla = TablaSalarial.objects.get(
                anio=self.anio,
                grado=self.afiliado.grado_escalafon
            )
            sueldo.tabla_salarial = tabla
            sueldo.save()
        except TablaSalarial.DoesNotExist:
            pass
        
        # Guardar bonificaciones detalladas
        self._guardar_bonificaciones(sueldo, calculo['bonificaciones'])
        
        # Recalcular aportes automáticamente
        sueldo.recalculate_aportes()
        
        return sueldo, created, calculo
    
    def _guardar_bonificaciones(self, sueldo, bonificaciones):
        """
        Guarda el detalle de bonificaciones en la base de datos.
        
        Args:
            sueldo (SueldoOrganizacion): Instancia de sueldo
            bonificaciones (dict): Bonificaciones calculadas
        """
        # Eliminar bonificaciones anteriores
        BonificacionPagoOrganizacion.objects.filter(sueldo_organizacion=sueldo).delete()
        
        # Crear nuevas bonificaciones
        for concepto, datos in bonificaciones.items():
            BonificacionPagoOrganizacion.objects.create(
                sueldo_organizacion=sueldo,
                anio=self.anio,
                descripcion=concepto,
                porcentaje=datos['porcentaje'],
                monto=datos['monto']
            )
