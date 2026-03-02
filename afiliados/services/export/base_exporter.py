from abc import ABC, abstractmethod
from typing import List, Dict, Any
from django.http import HttpResponse
import io


class BaseExporter(ABC):
    """
    Clase base abstracta para servicios de exportación.

    Define la interfaz común que deben implementar todos los exportadores
    para mantener consistencia y facilitar la extensión del sistema.
    """

    def __init__(self, data: List[Dict[str, Any]], filename: str = "export"):
        """
        Inicializa el exportador con datos y nombre de archivo.

        Args:
            data: Lista de diccionarios con los datos a exportar
            filename: Nombre base del archivo (sin extensión)
        """
        self.data = data
        self.filename = filename
        self._validate_data()

    def _validate_data(self):
        """Valida que los datos sean válidos para exportar."""
        if not isinstance(self.data, list):
            raise ValueError("Los datos deben ser una lista")

        if not self.data:
            raise ValueError("No hay datos para exportar")

        if not all(isinstance(item, dict) for item in self.data):
            raise ValueError("Todos los elementos deben ser diccionarios")

    @abstractmethod
    def export(self) -> HttpResponse:
        """
        Método abstracto que debe ser implementado por cada exportador específico.

        Returns:
            HttpResponse: Respuesta HTTP con el archivo generado
        """
        pass

    def _get_fieldnames(self) -> List[str]:
        """
        Obtiene los nombres de campos únicos de todos los registros.

        Returns:
            Lista ordenada de nombres de campos únicos
        """
        fieldnames = set()
        for record in self.data:
            fieldnames.update(record.keys())

        # Ordenar los campos para consistencia
        return sorted(list(fieldnames))

    def _format_filename(self, extension: str) -> str:
        """
        Formatea el nombre del archivo con extensión.

        Args:
            extension: Extensión del archivo (ej: 'xlsx', 'pdf')

        Returns:
            Nombre completo del archivo
        """
        return f"{self.filename}.{extension}"
