from django.core.management.base import BaseCommand
from django.core.files.uploadedfile import SimpleUploadedFile
from afiliados.services.excel_import.core.importador_service import ExcelImportService
import os
import time
from django.db import connection, OperationalError

class Command(BaseCommand):
    help = 'Importa afiliados desde un archivo Excel'

    def add_arguments(self, parser):
        parser.add_argument('excel_file', type=str, help='Ruta al archivo Excel a importar')

    def ensure_connection(self):
        """Asegura que la conexión a BD esté activa"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Verificar si estamos dentro de una transacción atómica
                if hasattr(connection, 'in_atomic_block') and connection.in_atomic_block:
                    # Si estamos en una transacción atómica, no podemos ejecutar queries
                    return True

                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                return True
            except OperationalError as e:
                if attempt < max_retries - 1:
                    self.stdout.write(f"Reconectando a BD (intento {attempt + 1}/{max_retries})...")
                    if not (hasattr(connection, 'in_atomic_block') and connection.in_atomic_block):
                        connection.close()
                    time.sleep(1)
                else:
                    self.stderr.write(f"Error de conexión después de {max_retries} intentos: {e}")
                    return False
        return False

    def handle(self, *args, **options):
        excel_file_path = options['excel_file']

        if not os.path.exists(excel_file_path):
            self.stderr.write(f"Error: El archivo {excel_file_path} no existe")
            return

        try:
            # Crear un SimpleUploadedFile para simular la subida
            with open(excel_file_path, 'rb') as f:
                file_content = f.read()

            filename = os.path.basename(excel_file_path)
            uploaded_file = SimpleUploadedFile(filename, file_content, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

            # Inicializar el servicio de importación
            import_service = ExcelImportService()

            # Ejecutar la importación con manejo robusto de conexión
            self.stdout.write(f"Iniciando importación de {filename}...")
            result = import_service.import_from_excel(uploaded_file)

            # Mostrar resultados
            self.stdout.write("""
✅ Importación completada:""")
            self.stdout.write(f"   Filas procesadas: {result['rows_processed']}")
            self.stdout.write(f"   Total de filas: {result['total_rows']}")

            if result['errors']:
                self.stdout.write(f"   Errores encontrados: {len(result['errors'])}")
                if result['error_file']:
                    self.stdout.write(f"   Archivo de errores: {result['error_file']}")

                # Mostrar primeros errores
                for error in result['errors'][:5]:
                    self.stdout.write(f"   Fila {error['row']}: {error['error']}")

            if result['missing_columns']:
                self.stdout.write(f"   Columnas faltantes: {', '.join(result['missing_columns'])}")

        except Exception as e:
            self.stderr.write(f"Error durante la importación: {str(e)}")
            import traceback
            traceback.print_exc()
