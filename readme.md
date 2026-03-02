# SIGAA — Sistema de Gestión y Análisis de Aportes de Afiliados

Sistema web de gestión desarrollado en Django para centralizar, calcular y reportar la información salarial y de aportes de los afiliados de una organización docente. Integra importación masiva desde Excel, motor de cálculo salarial por escalafón y generación de reportes en múltiples formatos.

---

## Descripción General

SIGAA resuelve el problema de gestión manual de datos salariales en organizaciones con cientos de afiliados activos cuyos sueldos dependen de variables cruzadas: grado de escalafón docente, cargo, antigüedad y nivel académico.

El sistema recibe archivos Excel emitidos por entidades externas, los procesa automáticamente, calcula los sueldos y aportes correspondientes para cada afiliado y expone toda esta información a través de una interfaz web con filtros, edición y exportación de reportes.

Contexto de uso: organizaciones de educación con afiliados en múltiples municipios, dos fuentes de datos paralelas (Secretaría y ADEMACOR) y necesidad de cruzar y auditar diferencias entre ambas.

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
- **Cálculo automático de aportes**: al crear o actualizar un sueldo, se recalculan automáticamente los aportes ADEMACOR (1 %) y FAMECOR (0,20 %) mediante señales Django.
- **Gestión de afiliados**: registro, edición, búsqueda con filtros avanzados y gestión de desafiliados con motivo y fecha de baja.
- **Base de datos paralela ADEMACOR**: importación y gestión independiente de datos de afiliados ADEMACOR con motor de cálculo salarial propio.
- **Reporte de diferencias**: comparación cruzada entre la nómina de la Secretaría y la de ADEMACOR, con estadísticas de intersección y exportación a Excel multi-hoja.
- **Reportes de totales de aportes**: consolidado mensual de aportes ADEMACOR/FAMECOR, exportable a Excel (con hojas de resumen, detalle y metadatos) y PDF.
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

### 4. Configurar variables de entorno

Crear un archivo `.env` en la raíz del proyecto:

```env
DEBUG=True
SECRET_KEY=reemplazar_con_clave_segura

DB_NAME=sigaa_db
DB_USER=usuario_mysql
DB_PASSWORD=contraseña_mysql
DB_HOST=localhost
DB_PORT=3306
```

### 5. Crear la base de datos y aplicar migraciones

```bash
# Crear la base de datos en MySQL antes de continuar
python manage.py migrate
```

### 6. Crear superusuario

```bash
python manage.py createsuperuser
```

### 7. Iniciar el servidor de desarrollo

```bash
python manage.py runserver
```

La aplicación estará disponible en `http://127.0.0.1:8000`.

---

## Autor

**Auder González** — Desarrollador Backend/Fullstack
Python · Django · MySQL · pandas
