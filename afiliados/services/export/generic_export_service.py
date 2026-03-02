from typing import List, Dict, Any, Optional, Type
from django.db.models import QuerySet, Model
from django.http import HttpResponse
from .exporter_factory import ExporterFactory, ExportFormat


class GenericExportService:
    """
    Servicio genérico para exportar datos de cualquier modelo Django.

    Esta clase permite exportar cualquier tabla/modelo del sistema
    de forma automática, adaptándose a los campos disponibles.
    """

    def __init__(self, model_class: Type[Model], queryset: Optional[QuerySet] = None):
        """
        Inicializa el servicio de exportación genérico.

        Args:
            model_class: Clase del modelo Django a exportar
            queryset: QuerySet específico a exportar (opcional)
        """
        self.model_class = model_class
        self.queryset = queryset or model_class.objects.all()

    def prepare_data(self,
                    fields: Optional[List[str]] = None,
                    exclude_fields: Optional[List[str]] = None,
                    include_inactive: bool = True) -> List[Dict[str, Any]]:
        """
        Prepara los datos para exportación desde cualquier modelo.

        Args:
            fields: Lista específica de campos a exportar (opcional)
            exclude_fields: Lista de campos a excluir (opcional)
            include_inactive: Si incluir registros inactivos (si aplica)

        Returns:
            Lista de diccionarios con los datos formateados
        """
        data = []

        # Obtener campos del modelo
        model_fields = self._get_model_fields()

        # Filtrar campos según parámetros
        if fields:
            export_fields = [f for f in model_fields if f in fields]
        else:
            export_fields = model_fields

        # Excluir campos específicos
        if exclude_fields:
            export_fields = [f for f in export_fields if f not in exclude_fields]

        # Aplicar filtros adicionales si el modelo tiene campo 'activo'
        if hasattr(self.model_class, 'activo') and not include_inactive:
            self.queryset = self.queryset.filter(activo=True)

        for instance in self.queryset.select_related():
            instance_data = {}

            for field_name in export_fields:
                value = self._get_field_value(instance, field_name)
                instance_data[field_name] = value

            data.append(instance_data)

        return data

    def _get_model_fields(self) -> List[str]:
        """
        Obtiene la lista de campos disponibles en el modelo.

        Returns:
            Lista de nombres de campos del modelo
        """
        # Excluir campos automáticos de Django
        exclude_fields = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']

        fields = []
        for field in self.model_class._meta.fields:
            field_name = field.name
            if field_name not in exclude_fields:
                fields.append(field_name)

        return fields

    def _get_field_value(self, instance, field_name: str) -> Any:
        """
        Obtiene el valor formateado de un campo específico.

        Args:
            instance: Instancia del modelo
            field_name: Nombre del campo

        Returns:
            Valor formateado del campo
        """
        value = getattr(instance, field_name, '')

        # Formatear diferentes tipos de campos
        if hasattr(value, 'strftime'):  # Campos de fecha
            return value.strftime('%Y-%m-%d') if value else ''
        elif hasattr(instance, f'get_{field_name}_display'):  # Campos de elección
            display_method = getattr(instance, f'get_{field_name}_display')
            return display_method() if value else ''
        elif value is None:
            return ''
        elif isinstance(value, bool):
            return 'Sí' if value else 'No'
        else:
            return str(value)

    def export_excel(self,
                    filename: str = "export",
                    fields: Optional[List[str]] = None,
                    exclude_fields: Optional[List[str]] = None,
                    include_inactive: bool = True) -> HttpResponse:
        """
        Exporta datos a Excel.

        Args:
            filename: Nombre del archivo Excel
            fields: Lista específica de campos a exportar (opcional)
            exclude_fields: Lista de campos a excluir (opcional)
            include_inactive: Si incluir registros inactivos

        Returns:
            HttpResponse con el archivo Excel
        """
        data = self.prepare_data(fields, exclude_fields, include_inactive)
        sheet_name = self.model_class._meta.verbose_name.title() or "Datos"
        return ExporterFactory.export_data(
            ExportFormat.EXCEL,
            data,
            filename,
            sheet_name=sheet_name
        )

    def export_pdf(self,
                  filename: str = "export",
                  fields: Optional[List[str]] = None,
                  exclude_fields: Optional[List[str]] = None,
                  include_inactive: bool = True) -> HttpResponse:
        """
        Exporta datos a PDF (método preparado para futura implementación).

        Args:
            filename: Nombre del archivo PDF
            fields: Lista específica de campos a exportar (opcional)
            exclude_fields: Lista de campos a excluir (opcional)
            include_inactive: Si incluir registros inactivos

        Returns:
            HttpResponse con el archivo PDF
        """
        data = self.prepare_data(fields, exclude_fields, include_inactive)
        return ExporterFactory.export_data(
            ExportFormat.PDF,
            data,
            filename
        )

    def get_export_stats(self,
                        fields: Optional[List[str]] = None,
                        exclude_fields: Optional[List[str]] = None,
                        include_inactive: bool = True) -> Dict[str, Any]:
        """
        Obtiene estadísticas sobre los datos que se van a exportar.

        Args:
            fields: Lista específica de campos a exportar (opcional)
            exclude_fields: Lista de campos a excluir (opcional)
            include_inactive: Si incluir registros inactivos

        Returns:
            Diccionario con estadísticas
        """
        data = self.prepare_data(fields, exclude_fields, include_inactive)

        stats = {
            'total_registros': len(data),
            'campos_exportados': len(data[0]) if data else 0,
            'campos_disponibles': list(data[0].keys()) if data else [],
            'modelo': self.model_class._meta.verbose_name.title(),
        }

        return stats
