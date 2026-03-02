from typing import List, Dict, Any
from django.http import HttpResponse
from .base_exporter import BaseExporter
from .excel_exporter import ExcelExporter
from .pdf_exporter import PDFExporter


class ExportFormat:
    """Constantes para los formatos de exportación disponibles."""
    EXCEL = "excel"
    PDF = "pdf"  # Para futuras implementaciones


class ExporterFactory:
    """
    Factory para crear exportadores según el formato solicitado.

    Esta clase centraliza la creación de exportadores y facilita
    la extensión para nuevos formatos en el futuro.
    """

    @staticmethod
    def create_exporter(format_type: str, data: List[Dict[str, Any]],
                       filename: str = "export", **kwargs) -> BaseExporter:
        """
        Crea un exportador según el formato especificado.

        Args:
            format_type: Tipo de formato ("excel", "pdf", etc.)
            data: Lista de diccionarios con los datos a exportar
            filename: Nombre base del archivo
            **kwargs: Argumentos adicionales específicos del formato

        Returns:
            Instancia del exportador correspondiente

        Raises:
            ValueError: Si el formato no es soportado
        """
        format_type = format_type.lower()

        if format_type == ExportFormat.EXCEL:
            return ExcelExporter(data, filename, **kwargs)
        elif format_type == ExportFormat.PDF:
            return PDFExporter(data, filename, **kwargs)
        else:
            raise ValueError(f"Formato de exportación '{format_type}' no soportado")

    @staticmethod
    def get_available_formats() -> List[str]:
        """
        Retorna la lista de formatos de exportación disponibles.

        Returns:
            Lista de formatos soportados
        """
        return [ExportFormat.EXCEL, ExportFormat.PDF]

    @staticmethod
    def export_data(format_type: str, data: List[Dict[str, Any]],
                   filename: str = "export", **kwargs) -> HttpResponse:
        """
        Método conveniente que crea el exportador y ejecuta la exportación.

        Args:
            format_type: Tipo de formato de exportación
            data: Datos a exportar
            filename: Nombre del archivo
            **kwargs: Argumentos adicionales

        Returns:
            HttpResponse con el archivo generado
        """
        exporter = ExporterFactory.create_exporter(format_type, data, filename, **kwargs)
        return exporter.export()
