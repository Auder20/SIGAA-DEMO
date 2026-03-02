from django.core.management.base import BaseCommand
import os

class Command(BaseCommand):
    help = 'Muestra las variables de entorno de base de datos (sin mostrar contraseñas)'

    def handle(self, *args, **options):
        self.stdout.write("🔍 Variables de entorno de base de datos:")
        self.stdout.write(f"DB_HOST: {os.getenv('DB_HOST', 'No configurado')}")
        self.stdout.write(f"DB_PORT: {os.getenv('DB_PORT', 'No configurado')}")
        self.stdout.write(f"DB_NAME: {os.getenv('DB_NAME', 'No configurado')}")
        self.stdout.write(f"DB_USER: {os.getenv('DB_USER', 'No configurado')}")

        # Mostrar contraseña como asteriscos para seguridad
        password = os.getenv('DB_PASSWORD', 'No configurado')
        masked_password = '*' * len(password) if password != 'No configurado' else password
        self.stdout.write(f"DB_PASSWORD: {masked_password}")

        self.stdout.write("\n💡 Si alguna variable dice 'No configurado', revisa tu archivo .env")
