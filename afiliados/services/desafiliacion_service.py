from django.db import transaction
from ..models import Afiliado, Desafiliado

class DesafiliacionService:
    """
    Servicio para manejar la desafiliación de un afiliado.
    Mueve los datos del modelo Afiliado al modelo Desafiliado.
    """
    
    @staticmethod
    @transaction.atomic
    def desafiliar_afiliado(afiliado_or_id, motivo_desafiliacion):
        """
        Desafilia a un afiliado moviendo sus datos a la tabla de desafiliados.
        
        Args:
            afiliado_or_id (int/Afiliado): ID del afiliado a desafiliar o instancia de Afiliado
            motivo_desafiliacion (str): Motivo por el cual se desafilia al afiliado
            
        Returns:
            tuple: (desafiliado_obj, success, message)
                - desafiliado_obj: El objeto Desafiliado creado
                - success (bool): True si la operación fue exitosa, False en caso contrario
                - message (str): Mensaje descriptivo del resultado
                
        Raises:
            Afiliado.DoesNotExist: Si no se encuentra el afiliado con el ID proporcionado
        """
        # Si se pasa un objeto Afiliado directamente
        if isinstance(afiliado_or_id, Afiliado):
            afiliado = afiliado_or_id
        else:
            # Si se pasa un ID, obtener el afiliado
            try:
                afiliado = Afiliado.objects.get(id=afiliado_or_id)
            except (Afiliado.DoesNotExist, ValueError):
                # Intentar buscar por cédula si el ID no es numérico
                try:
                    afiliado = Afiliado.objects.get(cedula=afiliado_or_id)
                except Afiliado.DoesNotExist:
                    return None, False, f"No se encontró un afiliado con ID o cédula {afiliado_or_id}."
        
        # Verificar si ya está desafiliado (activo=False) - aunque técnicamente no debería estar aquí si ya está desafiliado
        if not afiliado.activo:
            return None, False, f"El afiliado con ID {afiliado.id} ya está desafiliado."
        
        # Crear un nuevo registro en Desafiliado usando los datos del Afiliado
        desafiliado = Desafiliado(
            cedula=afiliado.cedula,
            nombre_completo=afiliado.nombre_completo,
            municipio=afiliado.municipio,
            ciudad_de_nacimiento=afiliado.ciudad_de_nacimiento,
            fecha_nacimiento=afiliado.fecha_nacimiento,
            edad=afiliado.edad,
            estado_civil=afiliado.estado_civil,
            nombre_conyuge=afiliado.nombre_conyuge,
            nombre_hijos=afiliado.nombre_hijos,
            direccion=afiliado.direccion,
            telefono=afiliado.telefono,
            email=afiliado.email,
            grado_escalafon=afiliado.grado_escalafon,
            cargo_desempenado=afiliado.cargo_desempenado,
            fecha_ingreso=afiliado.fecha_ingreso,
            anos_servicio=afiliado.anos_servicio,
            titulo_pregrado=afiliado.titulo_pregrado,
            titulo_posgrado=afiliado.titulo_posgrado,
            estudios_posgrado=afiliado.estudios_posgrado,
            otros_titulos=afiliado.otros_titulos,
            motivo_desafiliacion=motivo_desafiliacion,
            # activo es False por defecto
            # fecha_desafiliacion se establece automáticamente
        )
        
        # Guardar el nuevo desafiliado
        desafiliado.save()
        
        # Eliminar el afiliado original después de haberlo movido a Desafiliado
        afiliado.delete()
        
        return desafiliado, True, f"El afiliado '{afiliado.nombre_completo}' ha sido desafiliado exitosamente."
    
    @staticmethod
    @transaction.atomic
    def reafiliar_desafiliado(desafiliado_or_id):
        """
        Reafilia a un desafiliado moviendo sus datos de vuelta a la tabla de afiliados.
        
        Args:
            desafiliado_or_id (int/str/Desafiliado): ID, cédula o instancia del desafiliado a reafiliar
            
        Returns:
            tuple: (afiliado_obj, success, message)
        """
        # Si se pasa un objeto Desafiliado directamente
        if isinstance(desafiliado_or_id, Desafiliado):
            desafiliado = desafiliado_or_id
        else:
            # Si se pasa un ID o cédula
            try:
                # Primero intentar por ID
                try:
                    desafiliado = Desafiliado.objects.get(id=desafiliado_or_id)
                except (Desafiliado.DoesNotExist, ValueError):
                    # Si falla, intentar por cédula
                    desafiliado = Desafiliado.objects.get(cedula=desafiliado_or_id)
            except Desafiliado.DoesNotExist:
                return None, False, f"No se encontró un desafiliado con ID o cédula {desafiliado_or_id}."
            
        # Crear un nuevo registro en Afiliado usando los datos del Desafiliado
        afiliado = Afiliado(
            cedula=desafiliado.cedula,
            nombre_completo=desafiliado.nombre_completo,
            municipio=desafiliado.municipio,
            ciudad_de_nacimiento=desafiliado.ciudad_de_nacimiento,
            fecha_nacimiento=desafiliado.fecha_nacimiento,
            edad=desafiliado.edad,
            estado_civil=desafiliado.estado_civil,
            nombre_conyuge=desafiliado.nombre_conyuge,
            nombre_hijos=desafiliado.nombre_hijos,
            direccion=desafiliado.direccion,
            telefono=desafiliado.telefono,
            email=desafiliado.email,
            grado_escalafon=desafiliado.grado_escalafon,
            cargo_desempenado=desafiliado.cargo_desempenado,
            fecha_ingreso=desafiliado.fecha_ingreso,
            anos_servicio=desafiliado.anos_servicio,
            titulo_pregrado=desafiliado.titulo_pregrado,
            titulo_posgrado=desafiliado.titulo_posgrado,
            estudios_posgrado=desafiliado.estudios_posgrado,
            otros_titulos=desafiliado.otros_titulos,
            activo=True, # Marcar como activo nuevamente
        )
        
        afiliado.save()
        
        # Guardar el ID o cédula para el mensaje antes de eliminar
        identificador = f"{desafiliado.nombre_completo} (ID: {desafiliado.id}, Cédula: {desafiliado.cedula})"
        
        # Eliminar el desafiliado original
        desafiliado.delete()
        
        return afiliado, True, f"El desafiliado '{identificador}' ha sido reafiliado exitosamente."