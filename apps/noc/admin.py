from django.contrib import admin
from apps.infra.admin import Ocorrencia, OcorrenciaChecklistInLine
from apps.noc.forms import (ChechlistForm, ChechlistResponsaveisInlineForm,
                            ChecklistServidorNagiosServicoInlineForm)
from apps.noc.models import (Checklist, ChecklistEmail, ChecklistResponsaveis,
                             ChecklistServidorNagiosServico)


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



@admin.register(Checklist)
class ChecklistAdmin(admin.ModelAdmin):
    change_form_template = "noc/admin/change_form_checklist.html"
    search_fields = ["turno", "criado"]
    list_display = ["turno", "criado"]
    readonly_fields = ["criado", ]
    form = ChechlistForm
    inlines = [ResponsaveisInLine,ServidorNagiosInLine, OcorrenciaChecklistInLine]

    def add_view(self, request, form_url="", extra_context=None):
        usuario_logado = request.user
        ocorrencias_abertas = Ocorrencia.objects.all().exclude(status="Fechado")
        extra_context = dict( usuario_logado=usuario_logado, ocorrencias_abertas=ocorrencias_abertas)
        return super().add_view(request, form_url=form_url, extra_context=extra_context)

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if not obj.id: 
            obj.responsaveis.add(request.user)
            obj.save()

@admin.register(ChecklistEmail)
class ChecklistEmailAdmin(admin.ModelAdmin):
    search_fields = ["email"]
    list_display = ["email"]