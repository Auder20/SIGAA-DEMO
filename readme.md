# SIGAA — Sistema de Gestión y Análisis de Aportes de Afiliados

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-3.2-092E20?style=flat&logo=django&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8-4479A1?style=flat&logo=mysql&logoColor=white)
![DRF](https://img.shields.io/badge/Django_REST_Framework-3.14-red?style=flat&logo=django&logoColor=white)
![pandas](https://img.shields.io/badge/pandas-2.3-150458?style=flat&logo=pandas&logoColor=white)
![Render](https://img.shields.io/badge/Deploy-Render-46E3B7?style=flat&logo=render&logoColor=white)

**🎯 VERSIÓN DEMO — Datos ficticios para portafolio**

Sistema web de gestión en Django para centralizar, calcular y reportar la información salarial y de aportes de afiliados. Incluye importación masiva desde Excel, motor de cálculo configurable y exportación de reportes a Excel y PDF.

---

## ¿Qué problema resuelve?

Las organizaciones gremiales y educativas suelen gestionar aportes y sueldos en hojas de Excel desconectadas, propensas a errores y difíciles de auditar. SIGAA centraliza ese proceso: automatiza los cálculos salariales según escalafón, cargo y antigüedad, y genera reportes consolidados con un clic, eliminando el trabajo manual repetitivo.

---

## Screenshots

screenshots/

---

## ⚡ Demo Rápida
```bash
pip install -r requirements.txt
python manage.py setup_demo
python manage.py runserver
# Acceder a http://localhost:8000
```

| Rol | Email | Password |
|-----|-------|----------|
| Administrador | admin@demo.com | admin123 |
| Analista | analista@demo.com | analista123 |
| Consultor | consultor@demo.com | consultor123 |

---

## Funcionalidades Principales

- **Importación masiva desde Excel:** multi-hoja con detección automática de encabezados, mapeo inteligente de columnas y bulk operations por lotes de hasta 5.000 registros
- **Motor de cálculo salarial:** sueldo neto según escalafón (A, B, 1–14), cargo, años de servicio y nivel de posgrado
- **Cálculo automático de aportes:** señales Django recalculan aportes institucionales y de fondo al guardar un sueldo
- **Gestión de afiliados:** CRUD, búsqueda con filtros avanzados y gestión de desafiliados con motivo y fecha de baja
- **Reporte de diferencias:** comparación cruzada entre nómina interna y organización externa, exportable a Excel multi-hoja
- **Reportes de aportes:** consolidado mensual exportable a Excel y PDF con formato corporativo
- **Parámetros configurables:** porcentajes ajustables desde base de datos sin modificar código
- **Tablas salariales versionadas:** historial de salarios base por grado y año
- **Sistema de roles:** Administrador, Analista y Consultor con permisos diferenciados
- **Caché de vistas:** `cache_page` en vistas de alto tráfico para optimizar tiempos de respuesta

---

## Arquitectura
```
sigaa/
├── sigaa/          # Settings, URLs, WSGI/ASGI
├── core/           # Lógica transversal
├── users/          # Auth · AbstractUser · 3 roles
├── afiliados/      # CRUD afiliados · importación Excel
├── liquidacion/    # Motor de cálculo salarial y aportes
├── tablas/         # Tablas salariales configurables
├── reportes/       # Exportación Excel y PDF
└── custom_admin/   # Extensiones del admin Django
```

**Patrones aplicados:** Service Layer · Django Signals · Bulk Operations · Model Methods

---

## Tecnologías

| Capa | Tecnología |
|------|-----------|
| Framework | Django 3.2 |
| API REST | Django REST Framework 3.14 |
| Base de datos | MySQL · Django ORM |
| Datos | pandas 2.3 · numpy 2.3 · openpyxl 3.1 |
| PDF | ReportLab 4.0 · WeasyPrint 61.2 |
| Estáticos | WhiteNoise 6.6 + Brotli |
| Servidor | Gunicorn |
| Lenguaje | Python 3.11+ |
---

## Instalación Local

**Requisitos:** Python 3.11+, MySQL 8.0+, Git
```bash
git clone https://github.com/Auder20/SIGAA-DEMO.git
cd SIGAA
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py setup_demo
python manage.py runserver
```

**.env para producción:**
```env
DEBUG=True
SECRET_KEY=django-insecure-demo-key-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=sigaa_demo.db
```

---

## Comandos Útiles
```bash
python manage.py setup_demo          # Cargar datos ficticios
python manage.py setup_demo --reset  # Limpiar y regenerar
python manage.py collectstatic       # Estáticos para producción
gunicorn sigaa.wsgi:application      # Servidor producción
```

---

## Parámetros Configurables

Ajustables desde **Admin → Parámetros de Liquidación** sin tocar código:

- `aporte_institucional` — defecto: 1.00%
- `aporte_fondo` — defecto: 0.20%
- `bonif_antiguedad_5` — defecto: 5.00%
- `bonif_antiguedad_10` — defecto: 10.00%
- `bonif_educacion_maestria` — defecto: 8.00%
- `bonif_educacion_doctorado` — defecto: 12.00%

---

## Lo que Demuestra este Proyecto

- Backend Django multi-app con Service Layer y separación clara de responsabilidades
- Modelado de datos complejo con señales, métodos de modelo y lógica de negocio encapsulada
- Procesamiento de archivos Excel reales con estructuras variables usando pandas y heurísticas
- Exportación programática de reportes Excel multipágina y PDF con formato corporativo
- Configuración lista para producción: WhiteNoise, Gunicorn, Brotli, variables de entorno

---

## Autor

**Auder González** — Fullstack Developer
Python · Django · MySQL · pandas · Django REST Framework

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Auder%20González-0A66C2?style=flat&logo=linkedin&logoColor=white)](https://www.linkedin.com/in/auder-gonzalez-martinez)
[![GitHub](https://img.shields.io/badge/GitHub-Auder20-181717?style=flat&logo=github&logoColor=white)](https://github.com/Auder20)