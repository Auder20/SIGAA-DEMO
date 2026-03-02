from django.db import models

class Afiliado(models.Model):
    """
    Modelo principal para gestión de afiliados del sistema SIGAA.
    
    Almacena información personal, profesional y académica de los afiliados.
    Incluye métodos para cálculo automático de sueldos basado en parámetros
    como grado de escalafón, cargo desempeñado, años de servicio y educación.
    
    El modelo está diseñado para importación flexible desde Excel y
    cálculo automático de sueldos sin dependencia de datos externos.
    """
    # Información de identificación
    cedula = models.CharField(
        max_length=20, 
        unique=True,
        help_text="Número de cédula de identidad único del afiliado"
    )
    nombre_completo = models.CharField(
        max_length=100,
        help_text="Nombre completo del afiliado (nombres y apellidos)"
    )
    
    # Información geográfica y personal
    municipio = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Municipio de residencia o trabajo del afiliado"
    )
    ciudad_de_nacimiento = models.CharField(
        max_length=100,
        help_text="Ciudad donde nació el afiliado"
    )
    fecha_nacimiento = models.DateField(
        null=True, 
        blank=True,
        help_text="Fecha de nacimiento del afiliado"
    )
    edad = models.IntegerField(
        null=True, 
        blank=True,
        help_text="Edad actual del afiliado (calculada o importada)"
    )
    estado_civil = models.CharField(
        max_length=20, 
        null=True, 
        blank=True,
        help_text="Estado civil: soltero, casado, divorciado, viudo, etc."
    )
    nombre_conyuge = models.CharField(
        max_length=100, 
        null=True, 
        blank=True,
        help_text="Nombre completo del cónyuge si aplica"
    )
    nombre_hijos = models.CharField(
        max_length=200, 
        null=True, 
        blank=True,
        help_text="Nombres de los hijos separados por comas"
    )
    
    # Información de contacto
    direccion = models.CharField(
        max_length=200, 
        null=True, 
        blank=True,
        help_text="Dirección de residencia completa"
    )
    telefono = models.CharField(
        max_length=20, 
        null=True, 
        blank=True,
        help_text="Número de teléfono de contacto"
    )
    email = models.EmailField(
        null=True, 
        blank=True,
        help_text="Correo electrónico de contacto"
    )
    
    # Información profesional (crítica para cálculo de sueldos)
    grado_escalafon = models.CharField(
        max_length=10, 
        null=True, 
        blank=True,
        help_text="Grado en el escalafón docente (1-14). Determina el salario base"
    )
    cargo_desempenado = models.CharField(
        max_length=100, 
        null=True, 
        blank=True,
        help_text="Cargo actual: rector, decano, director, coordinador, docente, etc. Afecta bonificaciones"
    )
    fecha_ingreso = models.DateField(
        null=True, 
        blank=True,
        help_text="Fecha de ingreso a la institución. Usado para calcular años de servicio"
    )
    anos_servicio = models.IntegerField(
        null=True, 
        blank=True,
        help_text="Años de servicio en la institución. Determina bonificación por antigüedad"
    )
    
    # Información académica (afecta bonificaciones por educación)
    titulo_pregrado = models.CharField(
        max_length=100, 
        null=True, 
        blank=True,
        help_text="Título de pregrado obtenido"
    )
    titulo_posgrado = models.CharField(
        max_length=100, 
        null=True, 
        blank=True,
        help_text="Título de posgrado principal. Usado para detectar maestría/doctorado"
    )
    estudios_posgrado = models.CharField(
        max_length=200, 
        null=True, 
        blank=True,
        help_text="Descripción detallada de estudios de posgrado realizados"
    )
    otros_titulos = models.CharField(
        max_length=200, 
        null=True, 
        blank=True,
        help_text="Otros títulos, certificaciones o estudios adicionales"
    )
    
    # Campos de control
    activo = models.BooleanField(
        default=True,
        help_text="Indica si el afiliado está activo en el sistema"
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        null=True,
        help_text="Fecha y hora de creación del registro"
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        help_text="Fecha y hora de la última actualización del registro"
    )

    def __str__(self):
        """
        Representación en cadena del afiliado.
        
        Returns:
            str: Nombre completo y cédula del afiliado, o ID si no hay datos
        """
        if hasattr(self, 'nombre_completo') and self.nombre_completo:
            if self.cedula:
                return f"{self.nombre_completo} ({self.cedula})"
            return self.nombre_completo
        # Fallback si no hay nombre
        return str(self.pk)
    
    class Meta:
        """
        Metadatos del modelo Afiliado.
        """
        verbose_name = "Afiliado"
        verbose_name_plural = "Afiliados"
        ordering = ['nombre_completo']
        indexes = [
            models.Index(fields=['cedula']),
            models.Index(fields=['grado_escalafon']),
            models.Index(fields=['activo']),
        ]
    
    def calcular_sueldo_neto(self, anio=None, cargo_especifico=None, bonificaciones_adicionales=None):
        """
        Calcula el sueldo neto del afiliado usando el servicio de cálculo automático.
        
        Utiliza la clase CalculadorSueldo para determinar el sueldo basado en:
        - Grado de escalafón (salario base)
        - Cargo desempeñado (bonificación por cargo)
        - Años de servicio (bonificación por antigüedad)
        - Nivel educativo (bonificación por títulos)
        - Bonificaciones adicionales opcionales
        
        Args:
            anio (int, optional): Año para el cálculo. Por defecto usa 2025
            cargo_especifico (str, optional): Cargo específico para bonificación.
                                            Si no se especifica, usa self.cargo_desempenado
            bonificaciones_adicionales (dict, optional): Bonificaciones extra 
                                                        {concepto: porcentaje}
            
        Returns:
            dict: Resultado completo del cálculo con desglose de montos y porcentajes
            
        Example:
            resultado = afiliado.calcular_sueldo_neto(2025)
            print(f"Sueldo neto: ${resultado['sueldo_neto']}")
        """
        from liquidacion.services.calculo_sueldo import CalculadorSueldo
        calculadora = CalculadorSueldo(self, anio)
        return calculadora.calcular_sueldo_neto(cargo_especifico, bonificaciones_adicionales)
    
    def crear_o_actualizar_sueldo(self, anio=None, cargo_especifico=None, bonificaciones_adicionales=None):
        """
        Crea o actualiza el registro de sueldo del afiliado en la base de datos.
        
        Realiza el cálculo del sueldo y luego persiste el resultado en la tabla
        Sueldo. Si ya existe un registro para el afiliado y año, lo actualiza.
        Los aportes asociados se recalculan automáticamente via signals.
        
        Args:
            anio (int, optional): Año para el cálculo. Por defecto usa 2025
            cargo_especifico (str, optional): Cargo específico para bonificación
            bonificaciones_adicionales (dict, optional): Bonificaciones extra
            
        Returns:
            tuple: (Sueldo instance, created boolean, calculo dict)
                - Sueldo instance: El objeto Sueldo creado o actualizado
                - created boolean: True si se creó nuevo, False si se actualizó
                - calculo dict: El desglose completo del cálculo
                
        Example:
            sueldo, created, calculo = afiliado.crear_o_actualizar_sueldo(2025)
            if created:
                print("Nuevo sueldo creado")
            else:
                print("Sueldo actualizado")
        """
        from liquidacion.services.calculo_sueldo import CalculadorSueldo
        calculadora = CalculadorSueldo(self, anio)
        return calculadora.crear_o_actualizar_sueldo(cargo_especifico, bonificaciones_adicionales)




class DatosAdemacor(models.Model):
    """
    Modelo para almacenar datos completos de afiliados ADEMACOR.

    Contiene la misma estructura que el modelo Afiliado, permitiendo
    mantener una base de datos paralela para ADEMACOR con información
    completa de identificación, profesional, académica y personal.
    """
    # Información de identificación
    cedula = models.CharField(
        max_length=20,
        unique=True,
        help_text="Número de cédula de identidad único del afiliado"
    )
    nombre_completo = models.CharField(
        max_length=100,
        help_text="Nombre completo del afiliado (nombres y apellidos)"
    )
    
    # Información geográfica y personal
    municipio = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Municipio de residencia o trabajo del afiliado"
    )
    ciudad_de_nacimiento = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Ciudad donde nació el afiliado"
    )
    fecha_nacimiento = models.DateField(
        null=True,
        blank=True,
        help_text="Fecha de nacimiento del afiliado"
    )
    edad = models.IntegerField(
        null=True,
        blank=True,
        help_text="Edad actual del afiliado (calculada o importada)"
    )
    estado_civil = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Estado civil: soltero, casado, divorciado, viudo, etc."
    )
    nombre_conyuge = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Nombre completo del cónyuge si aplica"
    )
    nombre_hijos = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text="Nombres de los hijos separados por comas"
    )
    
    # Información de contacto
    direccion = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text="Dirección de residencia completa"
    )
    telefono = models.CharField(
        max_length=20,
        null=True,
        blank=True,
        help_text="Número de teléfono de contacto"
    )
    email = models.EmailField(
        null=True,
        blank=True,
        help_text="Correo electrónico de contacto"
    )
    
    # Información profesional (crítica para cálculo de sueldos)
    grado_escalafon = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        help_text="Grado en el escalafón docente (1-14). Determina el salario base"
    )
    cargo_desempenado = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Cargo actual: rector, decano, director, coordinador, docente, etc. Afecta bonificaciones"
    )
    fecha_ingreso = models.DateField(
        null=True,
        blank=True,
        help_text="Fecha de ingreso a la institución. Usado para calcular años de servicio"
    )
    anos_servicio = models.IntegerField(
        null=True,
        blank=True,
        help_text="Años de servicio en la institución. Determina bonificación por antigüedad"
    )
    
    # Información académica (afecta bonificaciones por educación)
    titulo_pregrado = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Título de pregrado obtenido"
    )
    titulo_posgrado = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Título de posgrado principal. Usado para detectar maestría/doctorado"
    )
    estudios_posgrado = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text="Descripción detallada de estudios de posgrado realizados"
    )
    otros_titulos = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text="Otros títulos, certificaciones o estudios adicionales"
    )

    # Campo constante para identificación del tipo de datos
    descripcion = models.CharField(
        max_length=50,
        default="ademacor",
        help_text="Tipo de datos - constante: ademacor"
    )
    
    # Campos de control
    activo = models.BooleanField(
        default=True,
        help_text="Indica si el afiliado ADEMACOR está activo en el sistema"
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        null=True,
        help_text="Fecha y hora de creación del registro"
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        help_text="Fecha y hora de la última actualización del registro"
    )

    def __str__(self):
        """
        Representación en cadena del registro de ADEMACOR.

        Returns:
            str: Nombre completo y cédula, o ID si no hay datos
        """
        if self.nombre_completo:
            if self.cedula:
                return f"ADEMACOR: {self.nombre_completo} ({self.cedula})"
            return f"ADEMACOR: {self.nombre_completo}"
        return f"ADEMACOR ID: {self.pk}"

    class Meta:
        """
        Metadatos del modelo DatosAdemacor.
        """
        verbose_name = "Dato de ADEMACOR"
        verbose_name_plural = "Datos de ADEMACOR"
        ordering = ['nombre_completo']
        indexes = [
            models.Index(fields=['cedula']),
            models.Index(fields=['grado_escalafon']),
            models.Index(fields=['activo']),
        ]
    
    def calcular_sueldo_neto(self, anio=None, cargo_especifico=None, bonificaciones_adicionales=None):
        """
        Calcula el sueldo neto del afiliado ADEMACOR usando el servicio de cálculo.
        
        Similar a la función en Afiliado, permite calcular sueldos para afiliados ADEMACOR
        basado en su grado de escalafón, cargo, años de servicio y nivel educativo.
        
        Args:
            anio (int, optional): Año para el cálculo. Por defecto usa 2025
            cargo_especifico (str, optional): Cargo específico para bonificación
            bonificaciones_adicionales (dict, optional): Bonificaciones extra
            
        Returns:
            dict: Resultado completo del cálculo con desglose de montos y porcentajes
        """
        from liquidacion.services.calculo_sueldo_ademacor import CalculadorSueldoAdemacor
        calculadora = CalculadorSueldoAdemacor(self, anio)
        return calculadora.calcular_sueldo_neto(cargo_especifico, bonificaciones_adicionales)
    
    def crear_o_actualizar_sueldo(self, anio=None, cargo_especifico=None, bonificaciones_adicionales=None):
        """
        Crea o actualiza el registro de sueldo ADEMACOR en la base de datos.
        
        Realiza el cálculo del sueldo y luego persiste el resultado en la tabla
        SueldoAdemacor. Si ya existe un registro para el afiliado y año, lo actualiza.
        
        Args:
            anio (int, optional): Año para el cálculo
            cargo_especifico (str, optional): Cargo específico para bonificación
            bonificaciones_adicionales (dict, optional): Bonificaciones extra
            
        Returns:
            tuple: (SueldoAdemacor instance, created boolean, calculo dict)
        """
        from liquidacion.services.calculo_sueldo_ademacor import CalculadorSueldoAdemacor
        calculadora = CalculadorSueldoAdemacor(self, anio)
        return calculadora.crear_o_actualizar_sueldo(cargo_especifico, bonificaciones_adicionales)




class Desafiliado(models.Model):
    """
    Modelo para gestión de afiliados desafiliados del sistema SIGAA.
    
    Almacena la misma información que Afiliado pero con el estado 'activo' 
    en False y un motivo de desafiliación.
    """
    # Información de identificación
    cedula = models.CharField(
        max_length=20, 
        unique=True,
        help_text="Número de cédula de identidad único del desafiliado"
    )
    nombre_completo = models.CharField(
        max_length=100,
        help_text="Nombre completo del desafiliado (nombres y apellidos)"
    )
    
    # Información geográfica y personal
    municipio = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        help_text="Municipio de residencia o trabajo del desafiliado"
    )
    ciudad_de_nacimiento = models.CharField(
        max_length=100,
        help_text="Ciudad donde nació el desafiliado"
    )
    fecha_nacimiento = models.DateField(
        null=True, 
        blank=True,
        help_text="Fecha de nacimiento del desafiliado"
    )
    edad = models.IntegerField(
        null=True, 
        blank=True,
        help_text="Edad actual del desafiliado (calculada o importada)"
    )
    estado_civil = models.CharField(
        max_length=20, 
        null=True, 
        blank=True,
        help_text="Estado civil: soltero, casado, divorciado, viudo, etc."
    )
    nombre_conyuge = models.CharField(
        max_length=100, 
        null=True, 
        blank=True,
        help_text="Nombre completo del cónyuge si aplica"
    )
    nombre_hijos = models.CharField(
        max_length=200, 
        null=True, 
        blank=True,
        help_text="Nombres de los hijos separados por comas"
    )
    
    # Información de contacto
    direccion = models.CharField(
        max_length=200, 
        null=True, 
        blank=True,
        help_text="Dirección de residencia completa"
    )
    telefono = models.CharField(
        max_length=20, 
        null=True, 
        blank=True,
        help_text="Número de teléfono de contacto"
    )
    email = models.EmailField(
        null=True, 
        blank=True,
        help_text="Correo electrónico de contacto"
    )
    
    # Información profesional (crítica para cálculo de sueldos)
    grado_escalafon = models.CharField(
        max_length=10, 
        null=True, 
        blank=True,
        help_text="Grado en el escalafón docente (1-14). Determina el salario base"
    )
    cargo_desempenado = models.CharField(
        max_length=100, 
        null=True, 
        blank=True,
        help_text="Cargo desempeñado al momento de la desafiliación"
    )
    fecha_ingreso = models.DateField(
        null=True, 
        blank=True,
        help_text="Fecha de ingreso a la institución. Usado para calcular años de servicio"
    )
    anos_servicio = models.IntegerField(
        null=True, 
        blank=True,
        help_text="Años de servicio en la institución al momento de la desafiliación"
    )
    
    # Información académica (afecta bonificaciones por educación)
    titulo_pregrado = models.CharField(
        max_length=100, 
        null=True, 
        blank=True,
        help_text="Título de pregrado obtenido"
    )
    titulo_posgrado = models.CharField(
        max_length=100, 
        null=True, 
        blank=True,
        help_text="Título de posgrado principal. Usado para detectar maestría/doctorado"
    )
    estudios_posgrado = models.CharField(
        max_length=200, 
        null=True, 
        blank=True,
        help_text="Descripción detallada de estudios de posgrado realizados"
    )
    otros_titulos = models.CharField(
        max_length=200, 
        null=True, 
        blank=True,
        help_text="Otros títulos, certificaciones o estudios adicionales"
    )
    
    # Campo adicional para desafiliados
    motivo_desafiliacion = models.TextField(
        help_text="Motivo de la desafiliación del sistema"
    )
    
    # Campos de control
    activo = models.BooleanField(
        default=False,
        help_text="Indica si el desafiliado está activo en el sistema (siempre False)"
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        null=True,
        help_text="Fecha y hora de creación del registro"
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        help_text="Fecha y hora de la última actualización del registro"
    )
    fecha_desafiliacion = models.DateField(
        auto_now_add=True,
        help_text="Fecha en que se registró la desafiliación"
    )

    def __str__(self):
        """
        Representación en cadena del desafiliado.
        
        Returns:
            str: Nombre completo y cédula del desafiliado, o ID si no hay datos
        """
        if hasattr(self, 'nombre_completo') and self.nombre_completo:
            if self.cedula:
                return f"{self.nombre_completo} ({self.cedula}) - Desafiliado"
            return f"{self.nombre_completo} - Desafiliado"
        # Fallback si no hay nombre
        return f"Desafiliado ID: {self.pk}"
    
    class Meta:
        """
        Metadatos del modelo Desafiliado.
        """
        verbose_name = "Desafiliado"
        verbose_name_plural = "Desafiliados"
        ordering = ['nombre_completo']
        indexes = [
            models.Index(fields=['cedula']),
            models.Index(fields=['activo']),
        ]
