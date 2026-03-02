from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from django.http import HttpResponse
from typing import Dict, Any, List
from .base_exporter import BaseExporter


class PDFExporter(BaseExporter):
    """
    Exportador específico para archivos PDF profesional.

    Utiliza ReportLab para generar documentos PDF con formato profesional
    incluyendo encabezados, información estadística y tablas bien organizadas.
    """

    def __init__(self, data: List[Dict[str, Any]], filename: str = "export",
                 title: str = "Reporte de Datos", include_stats: bool = True,
                 logo_path: str = None):
        """
        Inicializa el exportador PDF.

        Args:
            data: Lista de diccionarios con los datos a exportar
            filename: Nombre base del archivo (sin extensión)
            title: Título del documento PDF
            include_stats: Si incluir estadísticas antes de la tabla
            logo_path: Ruta al archivo de logotipo (PNG) para incluir en el encabezado
        """
        super().__init__(data, filename)
        self.title = title
        self.include_stats = include_stats
        self.logo_path = logo_path

    def export(self) -> HttpResponse:
        """
        Genera y retorna un archivo PDF con los datos formateados profesionalmente.

        Returns:
            HttpResponse: Respuesta HTTP con el archivo PDF
        """
        # Crear respuesta HTTP
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="{self._format_filename("pdf")}"'

        # Crear documento PDF
        doc = SimpleDocTemplate(
            response,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )

        # Obtener estilos
        styles = getSampleStyleSheet()

        # Crear contenido del PDF
        content = []

        # Agregar logotipo si está disponible
        if self.logo_path:
            try:
                logo = Image(self.logo_path)
                # Redimensionar logotipo manteniendo proporción
                logo_width, logo_height = logo.wrap(0, 0)
                aspect_ratio = logo_height / logo_width if logo_width > 0 else 1
                max_width = 2 * inch  # Máximo 2 pulgadas de ancho
                if logo_width > max_width:
                    logo_width = max_width
                    logo_height = logo_width * aspect_ratio
                logo.drawWidth = logo_width
                logo.drawHeight = logo_height
                content.append(logo)
                content.append(Spacer(1, 10))  # Espacio después del logotipo
            except Exception as e:
                # Si hay error con el logotipo, continuar sin él
                print(f"Error al cargar logotipo: {e}")

        # Título del documento
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=20,
            alignment=TA_CENTER,
            textColor=colors.darkblue,
            fontName='Helvetica-Bold'
        )
        content.append(Paragraph(self.title, title_style))

        # Información estadística si está habilitada
        if self.include_stats:
            stats_content = self._create_stats_section(styles)
            content.extend(stats_content)

        # Crear tabla con los datos
        if self.data:
            table_content = self._create_data_table(styles)
            content.extend(table_content)

        # Generar PDF
        doc.build(content)

        return response

    def _create_stats_section(self, styles):
        """Crea la sección de estadísticas antes de la tabla."""
        content = []

        # Obtener estadísticas
        fieldnames = self._get_fieldnames()
        total_registros = len(self.data)

        # Información de estadísticas
        stats_style = ParagraphStyle(
            'Stats',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=8,
            textColor=colors.HexColor("#2E8B57"),  # Verde oscuro
            fontName='Helvetica-Bold'
        )

        # Estadísticas básicas
        stats_text = [
            f"<b>Total de Registros:</b> {total_registros}",
            f"<b>Campos Incluidos:</b> {len(fieldnames)}",
            f"<b>Fecha de Generación:</b> {self._get_current_date()}",
        ]

        for stat in stats_text:
            content.append(Paragraph(stat, stats_style))

        # Espacio antes de la tabla
        content.append(Spacer(1, 15))

        return content

    def _create_data_table(self, styles):
        """Crea la tabla con los datos formateada profesionalmente."""
        content = []

        if not self.data:
            return content

        # Obtener nombres de columnas
        fieldnames = self._get_fieldnames()

        # Crear encabezados de tabla
        headers = [self._format_header_name(field) for field in fieldnames]

        # Crear datos de tabla
        table_data = [headers]  # Primera fila: encabezados

        for record in self.data:
            row = []
            for field in fieldnames:
                value = record.get(field, '')
                if isinstance(value, bool):
                    value = 'Sí' if value else 'No'
                elif value is None or value == '':
                    value = '-'
                else:
                    value = str(value)

                # Usar Paragraph para la columna "Nombre Completo" para que haga wrap
                if field == 'nombre_completo':
                    # Crear estilo para texto que haga wrap
                    wrap_style = ParagraphStyle(
                        'WrapStyle',
                        parent=styles['Normal'],
                        fontSize=9,
                        leading=11,
                        wordWrap='CJK'  # Permite wrap de palabras largas
                    )
                    row.append(Paragraph(value, wrap_style))
                else:
                    row.append(value)

            table_data.append(row)

        # Crear tabla
        table = Table(table_data)

        # Estilos de tabla profesional mejorados
        table_style = TableStyle([
            # Estilo del encabezado
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#003366")),  # Azul oscuro profesional
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),

            # Estilo del cuerpo
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 10),
            ('TOPPADDING', (0, 1), (-1, -1), 10),

            # Líneas de la tabla
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#CCCCCC")),

            # Alternar colores de filas para mejor legibilidad
            ('BACKGROUND', (0, 1), (-1, 1), colors.HexColor("#F8F8F8")),
            ('BACKGROUND', (0, 3), (-1, 3), colors.HexColor("#F8F8F8")),
            ('BACKGROUND', (0, 5), (-1, 5), colors.HexColor("#F8F8F8")),
        ])

        table.setStyle(table_style)

        # Ajustar ancho de columnas basado en el tipo de contenido
        num_cols = len(fieldnames)
        # Anchos específicos para mejor distribución
        if num_cols <= 4:
            col_widths = [80, 60, 90, 250]  # Cédula, Estado, Municipio, Nombre Completo (más ancho)
        elif num_cols <= 6:
            col_widths = [70, 50, 80, 200, 80, 70]
        else:
            # Distribución automática más inteligente
            base_width = (A4[0] - 100) / num_cols
            col_widths = [base_width] * num_cols
            # Dar más espacio a columnas de texto largo
            for i, field in enumerate(fieldnames):
                if field in ['nombre_completo', 'titulo_pregrado', 'titulo_posgrado', 'direccion']:
                    col_widths[i] = base_width * 1.5
                elif field in ['cedula', 'telefono']:
                    col_widths[i] = base_width * 0.8

        table._argW = col_widths

        content.append(table)

        return content

    def _format_header_name(self, field_name: str) -> str:
        """Formatea nombres de campos para encabezados legibles."""
        # Convertir snake_case a Título
        words = field_name.replace('_', ' ').split()
        formatted = ' '.join(word.capitalize() for word in words)

        return formatted

    def _normalize_text_length(self, text: str, field_name: str) -> str:
        """Normaliza la longitud del texto para que quepa en la tabla."""
        # Límites más conservadores y realistas
        max_lengths = {
            'nombre_completo': 32,
            'titulo_pregrado': 25,
            'titulo_posgrado': 25,
            'estudios_posgrado': 25,
            'otros_titulos': 25,
            'cargo_desempenado': 22,
            'direccion': 32,
            'nombre_conyuge': 22,
            'nombre_hijos': 32,
        }

        max_length = max_lengths.get(field_name, 28)  # Más conservador pero mejor

        if len(text) > max_length:
            return text[:max_length-3] + '...'

        return text

    def _get_current_date(self) -> str:
        """Obtiene la fecha actual formateada."""
        from datetime import datetime
        return datetime.now().strftime('%d/%m/%Y %H:%M')
