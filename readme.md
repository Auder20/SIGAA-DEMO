# SIGAA — Sistema de Gestión y Análisis de Aportes de Afiliados

**🎯 VERSIÓN DEMO - Datos Ficticios para Portafolio**

Sistema web de gestión desarrollado en Django para centralizar, calcular y reportar la información salarial y de aportes de afiliados. Esta versión de demostración utiliza datos completamente ficticios y nombres genéricos para ser utilizada como proyecto de portafolio público.

---

## ⚡ Demo Rápida

```bash
# 1. Instalar dependencias
pip install -r requirements.txt

# 2. Configurar y ejecutar demo
python manage.py setup_demo

# 3. Iniciar servidor
python manage.py runserver

# 4. Acceder a http://localhost:8000
```

### 👤 Usuarios de Demostración

| Rol | Email | Password | Permisos |
|-----|-------|----------|----------|
| **Administrador** | admin@demo.com | admin123 | Superusuario |
| **Analista** | analista@demo.com | analista123 | Staff |
| **Consultor** | consultor@demo.com | consultor123 | Usuario regular |

---

## 📋 Descripción General

SIGAA es un sistema de gestión salarial diseñado para organizaciones educativas que necesita procesar información de afiliados con cálculos complejos basados en múltiples variables:

- **Grado de escalafón docente** (A, B, 1-14)
- **Cargo desempeñado** (rector, decano, director, coordinador, docente)
- **Años de servicio** y **antigüedad**
- **Nivel educativo** (pregrado, maestría, doctorado)

### 🔄 Sistema Genérico

Esta versión de demostración ha sido refactorizada para eliminar referencias empresariales específicas:

- ✅ **ADEMACOR** → **Organización** (fuente externa genérica)
- ✅ **FAMECOR** → **Fondo** (aporte de fondo genérico)
- ✅ **Secretaría** → **Sistema Externo** (fuente de datos externa)
- ✅ **Aportes configurables** mediante parámetros en base de datos
- ✅ **Datos totalmente ficticios** para demostración

---

## 🎯 Características de la Versión Demo

### 📊 Datos de Ejemplo Incluidos

- **75 afiliados ficticios** con información realista
- **25 afiliados de organización externa** para comparación
- **Sueldos calculados** automáticamente según reglas salariales
- **Aportes generados** con porcentajes configurables
- **3 reportes de ejemplo** listos para consultar

### ⚙️ Configuración Flexible

- **Base de datos SQLite** por defecto (fácil para demo local)
- **Configuración por variables de entorno** (.env)
- **Porcentajes de aportes configurables** desde admin
- **Sistema listo para producción** con MySQL/PostgreSQL

### 🎨 Interfaz Limpia

- **Diseño genérico** sin logos empresariales
- **Modo dark/light** soportado
- **Mensajes amigables** para usuarios
- **Dashboard funcional** con contadores reales

---

## Rol en el Proyecto

Sistema desarrollado individualmente, abarcando todas las capas del stack:

- **Diseño del modelo de datos**: definición de entidades, relaciones, índices y validaciones en Django ORM.
- **Backend y lógica de negocio**: motor de cálculo salarial por grado/cargo/antigüedad/educación, motor de aportes automáticos por señales Django.
- **Procesamiento de archivos**: importador de Excel con detección automática de encabezados, mapeo inteligente de columnas y operaciones bulk para alto rendimiento.
- **API REST**: exposición de endpoints con Django REST Framework.
- **Generación de reportes**: exportación a Excel multipágina con `openpyxl`/`pandas` y a PDF con `ReportLab` y `WeasyPrint`.
- **Autenticación y roles**: modelo de usuario personalizado con tres niveles de acceso (Administrador, Analista, Consultor).
- **Configuración de despliegue**: middleware de compresión GZip, archivos estáticos con WhiteNoise, parámetros de entorno con `python-decouple`.

---

## Funcionalidades Principales

- **Importación masiva desde Excel**: procesamiento de archivos multi-hoja con detección automática de encabezados y posiciones de columnas, usando `bulk_create` y `bulk_update` por lotes de hasta 5 000 registros.
- **Motor de cálculo salarial**: calcula el sueldo neto de cada afiliado en función de: grado de escalafón (A, B, 1–14), cargo desempeñado (rector, decano, director, coordinador, docente…), años de servicio y nivel de posgrado.
- **Cálculo automático de aportes**: al crear o actualizar un sueldo, se recalculan automáticamente los aportes institucionales y de fondo mediante señales Django.
- **Gestión de afiliados**: registro, edición, búsqueda con filtros avanzados y gestión de desafiliados con motivo y fecha de baja.
- **Base de datos paralela de organización**: importación y gestión independiente de datos de afiliados externos con motor de cálculo salarial propio.
- **Reporte de diferencias**: comparación cruzada entre la nómina del sistema y la de organización externa, con estadísticas de intersección y exportación a Excel multi-hoja.
- **Reportes de totales de aportes**: consolidado mensual de aportes institucionales y de fondo, exportable a Excel (con hojas de resumen, detalle y metadatos) y PDF.
- **Parámetros configurables**: módulo `ParametroLiquidacion` que permite ajustar porcentajes y valores de cálculo desde la base de datos sin modificar código.
- **Tablas salariales versionadas**: registro histórico de salarios base por grado y año, con cálculo automático del aumento por grado al guardar.
- **Panel de administración personalizado**: app `custom_admin` con vistas extendidas del admin Django.
- **Sistema de roles**: tres perfiles de acceso (Administrador, Analista, Consultor) con flag `is_staff` asignado automáticamente a administradores.
- **Caché de vistas**: decorador `cache_page` aplicado a vistas de alto tráfico para optimizar tiempos de respuesta.

---

## Arquitectura del Sistema

Proyecto Django organizado en siete aplicaciones con responsabilidades bien definidas:

```
sigaa/                          # Configuración central del proyecto
│
├── sigaa/                      # Settings, URLs globales, WSGI/ASGI
│   ├── settings.py             # Config: MySQL, DRF, WhiteNoise, caché
│   └── urls.py                 # Enrutamiento principal
│
├── core/                       # Lógica transversal y componentes base
│
├── users/                      # Autenticación y gestión de usuarios
│   ├── models.py               # User (AbstractUser) + UserProfile + 3 roles
│   └── views.py                # Login, logout, perfil, cambio de contraseña
│
├── afiliados/                  # Entidades principales de afiliados
│   ├── models.py               # Afiliado, DatosAdemacor, Desafiliado
│   ├── views.py                # CRUD, búsqueda, filtros, importación Excel
│   └── services/
│       ├── excel_import/       # Motor de importación (ExcelImportClean)
│       ├── desafiliacion_service.py
│       └── ademacor_comparison.py
│
├── liquidacion/                # Cálculo salarial y de aportes
│   ├── models.py               # TablaSalarial, Bonificacion, Sueldo,
│   │                           # Aporte, BonificacionPago, SueldoAdemacor,
│   │                           # AporteAdemacor, ParametroLiquidacion
│   └── services/
│       ├── calculo_sueldo.py           # Motor principal (CalculadorSueldo)
│       ├── calculo_sueldo_ademacor.py  # Motor ADEMACOR
│       ├── calculo_sueldo_decretos.py  # Reglas por decreto
│       ├── calculo_aportes.py
│       └── calculo_bonificacion.py
│
├── tablas/                     # Tablas de referencia y bonificaciones
│   └── models.py               # Tablas salariales configurables
│
├── reportes/                   # Generación y almacenamiento de reportes
│   ├── models.py               # Reporte, ReporteAportesTotales
│   ├── views.py                # Exportación a Excel y PDF
│   └── services/
│       └── diferencias_service.py
│
└── custom_admin/               # Extensiones del panel de administración
```

**Patrones arquitectónicos aplicados:**
- **Service Layer**: lógica de negocio extraída de vistas hacia clases de servicio independientes.
- **Django Signals**: recálculo automático de aportes al guardar un registro `Sueldo`.
- **Bulk operations**: inserciones y actualizaciones masivas para alto rendimiento en carga de Excel.
- **Model methods**: lógica de cálculo encapsulada en métodos del modelo (`calcular_sueldo_neto`, `crear_o_actualizar_sueldo`).

---

## Tecnologías Utilizadas

| Capa | Tecnología |
|------|-----------|
| Framework web | Django 3.2 |
| API REST | Django REST Framework 3.14 |
| Base de datos | MySQL (vía `mysqlclient`) |
| ORM | Django ORM |
| Procesamiento de datos | pandas 2.3, numpy 2.3 |
| Lectura/escritura Excel | openpyxl 3.1 |
| Generación de PDF | ReportLab ≥ 4.0, WeasyPrint 61.2 |
| Archivos estáticos | WhiteNoise 6.6 + Brotli |
| Variables de entorno | python-decouple 3.8 |
| Servidor WSGI | Gunicorn |
| Lenguaje | Python 3.11+ |

---

## Procesamiento de Datos

El sistema cuenta con un pipeline de importación diseñado para manejar archivos Excel de diversas estructuras:

1. **Lectura multi-hoja**: se leen todas las hojas del archivo con `pandas.read_excel`, forzando tipos string en columnas críticas para evitar inferencia automática incorrecta.

2. **Detección de encabezados**: el módulo `ExcelImportClean` analiza la primera fila con heurísticas de texto para determinar si el archivo tiene encabezados o no.

3. **Mapeo inteligente de columnas**: si hay encabezados, se aplica un mapeo basado en patrones (`cédula`, `documento`, `dni` → campo `cedula`; `nombre`, `apellido` → `nombre_completo`; etc.). Si no hay encabezados, se detecta la posición de cada columna analizando el contenido de una muestra de filas (longitud numérica para cédulas, texto con espacios y mayúsculas para nombres).

4. **Procesamiento por lotes**: los registros se procesan en bloques de hasta 5 000 filas usando `bulk_create` y `bulk_update`, reduciendo significativamente el número de queries a la base de datos.

5. **Manejo de conflictos**: se comparan los valores existentes en BD con los del archivo. Los registros sin cambios se marcan como `ignored`; los registros modificados se actualizan; los nuevos se crean. Todo dentro de una transacción atómica por lote.

6. **Estadísticas de resultado**: al finalizar, el importador devuelve un resumen con conteo de registros creados, actualizados, ignorados y con error.

Para la importación de **aportes desde archivos externos**, existe un módulo dedicado (`aportes_import.py`) que cruza los datos del archivo con los afiliados ya registrados y actualiza los valores de sueldo de forma inversa.

---

## Lo que Demuestra este Proyecto

- **Backend Django estructurado**: aplicación multi-app con separación clara entre modelos, vistas y capa de servicio.
- **Modelado de datos complejo**: entidades interrelacionadas con lógica de negocio encapsulada en métodos del modelo y señales.
- **Automatización de procesos**: eliminación de cálculos manuales mediante un motor configurable de sueldos y aportes.
- **Procesamiento y transformación de datos**: manejo de archivos Excel reales con estructuras variables usando pandas y detección heurística.
- **Exportación de informes**: generación programática de reportes Excel multipágina y PDF con formato corporativo.
- **Diseño orientado a la mantenibilidad**: parámetros de liquidación configurables desde base de datos, índices de BD en campos clave, caché de vistas para rendimiento.
- **Autenticación y control de acceso**: modelo de usuario personalizado con roles diferenciados y perfil extendido.
- **Configuración para producción**: uso de WhiteNoise, Gunicorn, compresión Brotli y separación de variables de entorno.

---

## Instalación para Entorno Local

### Requisitos previos

- Python 3.11+
- MySQL 8.0+ (local o remoto)
- Git

### 1. Clonar el repositorio

```bash
git clone https://github.com/Auder20/SIGAA.git
cd SIGAA
```

### 2. Crear y activar entorno virtual

```bash
python -m venv venv

# Linux / macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno (Opcional)

Para demo local con SQLite, no se requiere configuración. Para producción, crear un archivo `.env`:

```env
# Configuración Demo (por defecto)
DEBUG=True
SECRET_KEY=django-insecure-demo-key-change-in-production
ALLOWED_HOSTS=localhost,127.0.0.1

# Base de datos SQLite (por defecto para demo)
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=sigaa_demo.db

# Para producción con MySQL/PostgreSQL
# DB_ENGINE=django.db.backends.mysql
# DB_NAME=sigaa_prod
# DB_USER=usuario_db
# DB_PASSWORD=contraseña_db
# DB_HOST=localhost
# DB_PORT=3306
```

### 5. Ejecutar configuración de demo

```bash
# Configurar sistema con datos ficticios
python manage.py setup_demo

# Para limpiar y regenerar datos
python manage.py setup_demo --reset
```

### 6. Iniciar el servidor de desarrollo

```bash
python manage.py runserver
```

La aplicación estará disponible en `http://127.0.0.1:8000`.

---

## 📚 Comandos Útiles

### Comandos de Demostración

```bash
# Configurar demo completa
python manage.py setup_demo

# Limpiar y regenerar demo
python manage.py setup_demo --reset

# Crear superusuario manualmente
python manage.py createsuperuser

# Ver estadísticas de demo
python manage.py shell
>>> from afiliados.models import Afiliado
>>> from liquidacion.models import Sueldo, Aporte
>>> print(f"Afiliados: {Afiliado.objects.count()}")
>>> print(f"Sueldos: {Sueldo.objects.count()}")
>>> print(f"Aportes: {Aporte.objects.count()}")
```

### Comandos de Producción

```bash
# Migraciones
python manage.py makemigrations
python manage.py migrate

# Recolectar archivos estáticos
python manage.py collectstatic --noinput

# Servidor de producción
gunicorn sigaa.wsgi:application
```

---

## 🔧 Configuración Avanzada

### Parámetros Configurables

Los porcentajes de aportes y bonificaciones se pueden ajustar desde el admin Django en:

**Parámetros de Liquidación → Parámetro Liquidacion**

Parámetros principales:
- `aporte_institucional`: Porcentaje de aporte institucional (defecto: 1.00%)
- `aporte_fondo`: Porcentaje de aporte al fondo (defecto: 0.20%)
- `bonif_anticiguedad_5`: Bonificación 5 años (defecto: 5.00%)
- `bonif_anticiguedad_10`: Bonificación 10 años (defecto: 10.00%)
- `bonif_educacion_maestria`: Bonificación maestría (defecto: 8.00%)
- `bonif_educacion_doctorado`: Bonificación doctorado (defecto: 12.00%)

### Configuración de Base de Datos

#### SQLite (Demo)
```env
DB_ENGINE=django.db.backends.sqlite3
DB_NAME=sigaa_demo.db
```

#### MySQL (Producción)
```env
DB_ENGINE=django.db.backends.mysql
DB_NAME=sigaa_prod
DB_USER=sigaa_user
DB_PASSWORD=secure_password
DB_HOST=localhost
DB_PORT=3306
```

#### PostgreSQL (Producción)
```env
DB_ENGINE=django.db.backends.postgresql
DB_NAME=sigaa_prod
DB_USER=sigaa_user
DB_PASSWORD=secure_password
DB_HOST=localhost
DB_PORT=5432
```

---

## Autor

**Auder González** — Desarrollador Backend/Fullstack
Python · Django · MySQL · pandas
