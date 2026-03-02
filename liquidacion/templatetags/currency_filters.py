from django import template
import locale

register = template.Library()

@register.filter
def cop(value):
    """Formatea un número como pesos colombianos: COP $ 1.234.567,89
    No cambia el valor, solo la presentación.
    """
    try:
        # Asegurar que sea float
        val = float(value or 0)
    except Exception:
        return value
    # Formatear con separador de miles '.' y decimales ','
    # No dependemos de locale para evitar configuraciones del sistema
    integer = int(abs(val))
    decimals = abs(val) - integer
    int_part = f"{integer:,}".replace(',', '.')
    dec_part = f"{decimals:.2f}"[1:].replace('.', ',')  # obtiene ',xx'
    sign = '-' if val < 0 else ''
    return f"COP {sign}${int_part}{dec_part}"
