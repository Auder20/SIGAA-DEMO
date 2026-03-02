import os
import sys
import django

# Configurar entorno Django
sys.path.append(os.getcwd())
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sigaa.settings')
django.setup()

try:
    print("Intentando importar diferencias_service...")
    from reportes.services import diferencias_service
    print("Importación de módulo exitosa.")

    print("Intentando importar exportar_diferencias_excel_multipage...")
    from reportes.services.diferencias_service import exportar_diferencias_excel_multipage
    print("Importación de función exitosa.")

except Exception as e:
    print(f"ERROR DE IMPORTACIÓN:\n{e}")
    import traceback
    traceback.print_exc()
