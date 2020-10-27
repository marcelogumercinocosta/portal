from django import template
from django.utils import formats
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(is_safe=True)
def echart_safe(value):
    return mark_safe(str(formats.localize(value, use_l10n=False))).replace("False", "false").replace("True", "true")
