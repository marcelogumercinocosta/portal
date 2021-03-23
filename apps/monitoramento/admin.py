# -*- coding: utf-8 -*-
from django.contrib import admin
from apps.monitoramento.models import Monitoramento, TipoMonitoramento

class MonitoramentoInLine(admin.TabularInline):
    model = Monitoramento
    fields = ("nome", "url", "prioridade", "target", "tipo")
    extra = 0


@admin.register(TipoMonitoramento)
class TipoMonitoramentoAdmin(admin.ModelAdmin):
    list_display = ("nome",)
    search_fields = ["nome"]
    inlines = (MonitoramentoInLine,)
