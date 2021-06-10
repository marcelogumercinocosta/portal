from apps.infra.admin import OcorrenciaChecklistInLine
from apps.noc.forms import ChechlistForm, ChechlistResponsaveisInlineForm, ChecklistServidorNagiosServicoInlineForm
from apps.noc.models import Checklist, ChecklistResponsaveis, ChecklistServidorNagiosServico
from django.contrib import admin

class ServidorNagiosInLine(admin.TabularInline):
    model = ChecklistServidorNagiosServico
    extra = 0
    verbose_name = "Alerta no Nagios"
    verbose_name_plural =  "Alerta no Nagios"
    form = ChecklistServidorNagiosServicoInlineForm


class ServidorNagiosInLine(admin.TabularInline):
    model = ChecklistServidorNagiosServico
    extra = 0
    verbose_name = "Alerta no Nagios"
    verbose_name_plural =  "Alertas no Nagios"
    form = ChecklistServidorNagiosServicoInlineForm

class ResponsaveisInLine(admin.TabularInline):
    model = ChecklistResponsaveis
    extra = 0
    verbose_name = "Responsável pelo turno"
    verbose_name_plural =  "Responsáveis pelo turno"
    form = ChechlistResponsaveisInlineForm

    def get_form(self, request, obj=None, **kwargs):
        form = super(ResponsaveisInLine, self).get_form(request, obj, **kwargs)
        form.base_fields['responsavel'].initial = request.user
        return form

@admin.register(Checklist)
class ChecklistAdmin(admin.ModelAdmin):
    search_fields = ["turno", "criado"]
    list_display = ["turno", "criado"]
    readonly_fields = ["criado", ]
    form = ChechlistForm
    inlines = [ResponsaveisInLine,ServidorNagiosInLine, OcorrenciaChecklistInLine]

