#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script mejorado para validar TODOS los templates de Django"""
import os
import sys
import django
from pathlib import Path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sigaa.settings')
django.setup()

from django.template.loader import get_template
from django.template import TemplateSyntaxError

def find_all_templates():
    """Encuentra todos los archivos .html en los directorios de templates"""
    templates = []
    base_dir = Path(__file__).resolve().parent

    # Buscar en todos los directorios de templates
    template_dirs = [
        base_dir / 'templates',
        base_dir / 'afiliados' / 'templates',
        base_dir / 'liquidacion' / 'templates',
        base_dir / 'reportes' / 'templates',
        base_dir / 'users' / 'templates',
    ]

    for template_dir in template_dirs:
        if template_dir.exists():
            for html_file in template_dir.rglob('*.html'):
                # Obtener la ruta relativa al directorio de templates
                try:
                    rel_path = html_file.relative_to(template_dir)
                    template_name = str(rel_path).replace('\\', '/')
                    templates.append(template_name)
                except ValueError:
                    continue

    return sorted(set(templates))

print("=" * 80)
print("VALIDACIÓN COMPLETA DE TEMPLATES DE DJANGO")
print("=" * 80)
print("\nBuscando templates...")

all_templates = find_all_templates()
print(f"\nEncontrados {len(all_templates)} templates para validar\n")
print("=" * 80)

errors = []
success = []
skipped = []

# Templates que sabemos que son parciales o base y pueden no cargarse solos
skip_patterns = ['base.html', 'partial', 'component']

for template_name in all_templates:
    # Saltar templates base o parciales
    should_skip = any(pattern in template_name.lower() for pattern in skip_patterns)

    if should_skip:
        skipped.append(template_name)
        print(f"⊘ SKIP: {template_name} (template base/parcial)")
        continue

    try:
        template = get_template(template_name)
        success.append(template_name)
        print(f"✓ OK: {template_name}")
    except TemplateSyntaxError as e:
        errors.append((template_name, str(e)))
        print(f"✗ ERROR: {template_name}")
        print(f"  └─ Sintaxis: {str(e)[:100]}...")
    except Exception as e:
        errors.append((template_name, str(e)))
        print(f"✗ ERROR: {template_name}")
        print(f"  └─ {type(e).__name__}: {str(e)[:100]}...")

print("\n" + "=" * 80)
print(f"\n📊 RESUMEN DE RESULTADOS:")
print(f"  ✓ Exitosos: {len(success)}")
print(f"  ✗ Errores: {len(errors)}")
print(f"  ⊘ Omitidos: {len(skipped)}")
print(f"  📁 Total: {len(all_templates)}")

if errors:
    print("\n" + "=" * 80)
    print("❌ ERRORES ENCONTRADOS:")
    print("=" * 80)
    for i, (template_name, error) in enumerate(errors, 1):
        print(f"\n{i}. {template_name}")
        print(f"   Error: {error}")
        print("-" * 80)
    sys.exit(1)
else:
    print("\n" + "=" * 80)
    print("✅ ¡TODOS LOS TEMPLATES SE CARGARON EXITOSAMENTE!")
    print("=" * 80)

    if skipped:
        print(f"\nNota: {len(skipped)} templates base/parciales fueron omitidos (esto es normal)")

    sys.exit(0)
