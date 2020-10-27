import datetime
import locale
import math
from django import template
from django.utils import formats
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def to_replace_dot(value):
    return value.replace(".", "_")


@register.filter
def get_size_human(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = float(math.pow(1024, i))
    s = int(size_bytes) / p
    locale.setlocale(locale.LC_ALL, "pt_BR")
    return locale.format_string("%.1f %s", (s, size_name[i]))


@register.filter
def get_size_human_size(size_bytes):
    if size_bytes == 0:
        return "B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    return size_name[i]


@register.filter
def get_size_human_number(size_bytes):
    if size_bytes == 0:
        return "0"
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = float(math.pow(1024, i))
    s = int(size_bytes) / p
    locale.setlocale(locale.LC_ALL, "pt_BR")
    return locale.format_string("%.1f", s)


@register.filter
def get_size_human_TB(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = 4
    p = float(math.pow(1024, i))
    s = int(size_bytes) / p
    locale.setlocale(locale.LC_ALL, "pt_BR")
    return locale.format_string("%.1f %s", (s, size_name[i]))


@register.filter()
def add_days(days):
    new_date = datetime.date.today() + datetime.timedelta(days=days)
    return new_date


@register.filter(is_safe=True)
def echart_safe(value):
    return mark_safe(str(formats.localize(value, use_l10n=False))).replace("False", "false").replace("True", "true")
