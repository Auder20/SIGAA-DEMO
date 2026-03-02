from typing import List, Dict, Any
from django.http import HttpResponse
from afiliados.services.export.exporter_factory import ExporterFactory, ExportFormat


class DynamicExportService:
    """
    Servicio completamente dinámico para exportar cualquier conjunto de datos.

    Este servicio recibe datos ya formateados y solo exporta las columnas
    que están presentes en los datos recibidos, sin asumir campos predefinidos.
    """

    def __init__(self, data: List[Dict[str, Any]], model_name: str = "Datos"):
        """
        Inicializa el servicio de exportación dinámica.

        Args:
            data: Lista de diccionarios con los datos a exportar
            model_name: Nombre del modelo para el nombre de hoja (opcional)
        """
        self.data = data
        self.model_name = model_name
        self._validate_data()

    def _validate_data(self):
        """Valida que los datos sean válidos para exportar."""
        if not isinstance(self.data, list):
            raise ValueError("Los datos deben ser una lista")

        if not self.data:
            raise ValueError("No hay datos para exportar")

        if not all(isinstance(item, dict) for item in self.data):
            raise ValueError("Todos los elementos deben ser diccionarios")

    def export_excel(self, filename: str = "export", logo_path: str = None) -> HttpResponse:
        """
        Exporta datos a Excel de forma completamente dinámica.

        Args:
            filename: Nombre del archivo Excel
            logo_path: Ruta al archivo de logotipo para incluir en el encabezado

        Returns:
            HttpResponse con el archivo Excel
        """
        return ExporterFactory.export_data(
            ExportFormat.EXCEL,
            self.data,
            filename,
            sheet_name=self.model_name,
            logo_path=logo_path
        )

    def export_pdf(self, filename: str = "export", logo_path: str = None) -> HttpResponse:
        """
        Exporta datos a PDF (preparado para futura implementación).

        Args:
            filename: Nombre del archivo PDF
            logo_path: Ruta al archivo de logotipo para incluir en el encabezado

        Returns:
            HttpResponse con el archivo PDF
        """
        return ExporterFactory.export_data(
            ExportFormat.PDF,
            self.data,
            filename,
            logo_path=logo_path
        )

    def get_export_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas sobre los datos que se van a exportar.

        Returns:
            Diccionario con estadísticas
        """
        if not self.data:
            return {
                'total_registros': 0,
                'columnas_exportadas': 0,
                'columnas_disponibles': [],
            }

        # Obtener todas las columnas disponibles
        all_columns = set()
        for record in self.data:
            all_columns.update(record.keys())

        columnas_ordenadas = sorted(list(all_columns))

        return {
            'total_registros': len(self.data),
            'columnas_exportadas': len(columnas_ordenadas),
            'columnas_disponibles': columnas_ordenadas,
        }
