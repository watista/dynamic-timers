from django import template

register = template.Library()

@register.filter
def format_minutes(value):
    try:
        return f"{float(value):.1f}".replace(",", ".")
    except:
        return value
