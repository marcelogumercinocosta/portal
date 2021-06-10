# -*- coding: utf-8 -*-
from django.contrib import admin
from apps.monitoramento.models import Monitoramento, TipoMonitoramento, NagiosServicos

class MonitoramentoInLine(admin.TabularInline):
    model = Monitoramento
    fields = ("nome", "url", "prioridade", "target", "tipo")
    extra = 0

@admin.register(TipoMonitoramento)
class TipoMonitoramentoAdmin(admin.ModelAdmin):
    list_display = ("nome",)
    search_fields = ["nome"]
    inlines = (MonitoramentoInLine,)


@admin.register(NagiosServicos)
class NagiosServicosAdmin(admin.ModelAdmin):
    list_display = ["servico", "padrao"]
    search_fields = ["servico"]