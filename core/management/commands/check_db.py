from django.core.management.base import BaseCommand
from django.db import connection
import subprocess
import sys

class Command(BaseCommand):
    help = 'Verifica la conexión a la base de datos MySQL'

    def handle(self, *args, **options):
        self.stdout.write("🔍 Verificando conexión a MySQL...")

        try:
            # Verificar si MySQL está corriendo
            if sys.platform == "win32":
                # Windows
                result = subprocess.run(['sc', 'query', 'mysql'],
                                      capture_output=True, text=True)
                if result.returncode != 0:
                    self.stdout.write("❌ MySQL no está instalado como servicio")
                    self.stdout.write("💡 Solución: Instala MySQL o XAMPP y asegúrate de que esté corriendo")
                    return
            else:
                # Linux/Mac
                result = subprocess.run(['systemctl', 'is-active', 'mysql'],
                                      capture_output=True, text=True)
                if result.returncode != 0:
                    self.stdout.write("❌ MySQL no está corriendo")
                    self.stdout.write("💡 Solución: Ejecuta 'sudo systemctl start mysql'")
                    return

            # Probar conexión Django
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1 as test")
                row = cursor.fetchone()
                if row and row[0] == 1:
                    self.stdout.write("✅ Conexión a MySQL exitosa")
                    self.stdout.write(f"📊 Base de datos: {connection.settings_dict['NAME']}")
                    self.stdout.write(f"🖥️  Host: {connection.settings_dict['HOST']}:{connection.settings_dict['PORT']}")
                else:
                    self.stdout.write("❌ Error en la consulta de prueba")

        except Exception as e:
            self.stdout.write(f"❌ Error de conexión: {e}")
            self.stdout.write("\n🔧 Posibles soluciones:")
            self.stdout.write("1. Asegúrate de que MySQL esté instalado y corriendo")
            self.stdout.write("2. Verifica que la base de datos 'sigaa_db' exista")
            self.stdout.write("3. Ejecuta las migraciones: python manage.py migrate")
            self.stdout.write("4. Si usas XAMPP, asegúrate de que MySQL esté iniciado")
