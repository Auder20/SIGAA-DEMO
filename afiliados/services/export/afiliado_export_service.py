from typing import List, Dict, Any, Optional
from django.db.models import QuerySet
from django.http import HttpResponse
from afiliados.models import Afiliado
from .exporter_factory import ExporterFactory, ExportFormat


class AfiliadoExportService:
    """
    Servicio específico para exportar datos de afiliados.

    Esta clase se encarga de preparar los datos de afiliados
    y coordinar con los servicios de exportación.
    """

    def __init__(self, queryset: Optional[QuerySet] = None):
        """
        Inicializa el servicio de exportación de afiliados.

        Args:
            queryset: QuerySet de afiliados a exportar (opcional)
        """
        self.queryset = queryset or Afiliado.objects.all()

    def prepare_data(self, include_inactive: bool = True, fields: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Prepara los datos de afiliados para exportación.

        Args:
            include_inactive: Si incluir afiliados inactivos
            fields: Lista específica de campos a exportar (opcional)

        Returns:
            Lista de diccionarios con los datos formateados
        """
        if not include_inactive:
            self.queryset = self.queryset.filter(activo=True)

        data = []
        for afiliado in self.queryset.select_related():
            afiliado_data = {}

            # Campos disponibles en el modelo Afiliado
            available_fields = {
                'cedula': afiliado.cedula or '',
                'nombre_completo': afiliado.nombre_completo or '',
                'email': afiliado.email or '',
                'telefono': afiliado.telefono or '',
                'municipio': afiliado.municipio or '',
                'estado': 'Activo' if afiliado.activo else 'Inactivo',
                'fecha_nacimiento': afiliado.fecha_nacimiento.strftime('%Y-%m-%d') if afiliado.fecha_nacimiento else '',
                'sexo': afiliado.get_sexo_display() if afiliado.sexo else '',
                'nivel_educativo': afiliado.get_nivel_educativo_display() if afiliado.nivel_educativo else '',
                'cargo_desempenado': afiliado.cargo_desempenado or '',
                'grado_escalafon': afiliado.grado_escalafon or '',
                'anos_servicio': afiliado.anos_servicio or 0,
                'fecha_ingreso': afiliado.fecha_ingreso.strftime('%Y-%m-%d') if afiliado.fecha_ingreso else '',
                'fecha_retiro': afiliado.fecha_retiro.strftime('%Y-%m-%d') if afiliado.fecha_retiro else '',
                'observaciones': afiliado.observaciones or '',
            }

            # Si se especifican campos específicos, filtrar solo esos
            if fields:
                afiliado_data = {field: available_fields.get(field, '') for field in fields}
            else:
                afiliado_data = available_fields

            data.append(afiliado_data)

        return data

    def export_excel(self, filename: str = "afiliados_export",
                    include_inactive: bool = True,
                    fields: Optional[List[str]] = None,
                    logo_path: str = None) -> HttpResponse:
        """
        Exporta afiliados a Excel.

        Args:
            filename: Nombre del archivo Excel
            include_inactive: Si incluir afiliados inactivos
            fields: Lista específica de campos a exportar (opcional)
            logo_path: Ruta al archivo de logotipo para incluir en el encabezado

        Returns:
            HttpResponse con el archivo Excel
        """
        data = self.prepare_data(include_inactive, fields)
        return ExporterFactory.export_data(
            ExportFormat.EXCEL,
            data,
            filename,
            sheet_name="Afiliados",
            logo_path=logo_path
        )

    def export_pdf(self, filename: str = "afiliados_export",
                   include_inactive: bool = True,
                   fields: Optional[List[str]] = None,
                   logo_path: str = None) -> HttpResponse:
        """
        Exporta afiliados a PDF (método preparado para futura implementación).

        Args:
            filename: Nombre del archivo PDF
            include_inactive: Si incluir afiliados inactivos
            fields: Lista específica de campos a exportar (opcional)
            logo_path: Ruta al archivo de logotipo para incluir en el encabezado

        Returns:
            HttpResponse con el archivo PDF

        Raises:
            NotImplementedError: Hasta que se implemente el exportador PDF
        """
        data = self.prepare_data(include_inactive, fields)
        return ExporterFactory.export_data(
            ExportFormat.PDF,
            data,
            filename,
            logo_path=logo_path
        )

    def get_export_stats(self, include_inactive: bool = True, fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Obtiene estadísticas sobre los datos que se van a exportar.

        Args:
            include_inactive: Si incluir afiliados inactivos
            fields: Lista específica de campos a exportar (opcional)

        Returns:
            Diccionario con estadísticas
        """
        data = self.prepare_data(include_inactive, fields)

        stats = {
            'total_registros': len(data),
            'activos': len([a for a in data if a.get('estado') == 'Activo']),
            'inactivos': len([a for a in data if a.get('estado') == 'Inactivo']),
            'campos_exportados': len(data[0]) if data else 0,
            'campos_disponibles': list(data[0].keys()) if data else [],
        }

        return stats
