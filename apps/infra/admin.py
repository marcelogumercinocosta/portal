from apps.infra.utils.xen_crud import XenCrud
from collections import OrderedDict
from distutils.command import clean
from distutils.command.clean import clean
from secrets import choice

from django.contrib import admin, messages
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404
from apps.core.utils.freeipa import FreeIPA
from apps.infra.forms import (AmbienteVirtualServidorInLineForm,
                              EquipamentoGrupoAcessoForm, EquipamentoParteForm,
                              HostnameIPForm, HostnameIPInLineForm,
                              OcorrenciaInLineForm, RackForm, ServidorForm, TemplateComandoInLineForm,
                              StorageAreaGrupoTrabalhoInLineForm)
from apps.infra.models import (AmbienteVirtual, 
                               EquipamentoGrupoAcesso, EquipamentoParte,
                               HostnameIP, Ocorrencia, Rack, Rede, Servidor,
                               ServidorHostnameIP, Storage, StorageArea,
                               StorageAreaGrupoTrabalho, Supercomputador, TemplateComando, TemplateHostnameIP, TemplateVM)
from apps.infra.utils.freeipa_location import Automount
from apps.infra.utils.history import HistoryInfra
from apps.infra.views import DataCenterMap


class OcorrenciaInLine(admin.TabularInline):
    model = Ocorrencia
    fields = ["ocorrencia", "descricao", "data"]
    extra = 0
    form = OcorrenciaInLineForm

    def get_readonly_fields(self, request, obj=None):
        fields = []
        fields.append("data")
        return fields

    def has_add_permission(self, request, obj=None):
        return False


class TemplateComandoInLine(admin.TabularInline):
    model = TemplateComando
    fields = ("comando", "configuracao","prioridade")
    extra = 0
    form = TemplateComandoInLineForm


class StorageAreaGrupoTrabalhoInLine(admin.TabularInline):
    model = StorageAreaGrupoTrabalho
    fields = ("storage_area", "quota")
    extra = 0
    form = StorageAreaGrupoTrabalhoInLineForm


class StorageAreaInLine(admin.TabularInline):
    model = StorageArea
    fields = ("area", "tipo",)
    extra = 0


class GrupoAcessoEquipamentoInLine(admin.TabularInline):
    model = EquipamentoGrupoAcesso
    extra = 0
    verbose_name = "Grupo de Acesso"
    verbose_name_plural = "Grupos de Acesso"
    form = EquipamentoGrupoAcessoForm

    def has_change_permission(self, request, obj=None):
        return False
    
    def formfield_for_foreignkey(self, db_field, request=None, **kwargs):
        field = super(GrupoAcessoEquipamentoInLine, self).formfield_for_foreignkey(db_field, request, **kwargs)
        field.queryset = field.queryset.filter(grupo_acesso__contains=request._obj_.tipo_uso).exclude(equipamento__id=request._obj_.id)
        return field



class GrupoAcessoEquipamentoInLineRead(admin.TabularInline):
    model = EquipamentoGrupoAcesso
    fields = ["equipamento_name","equipamento_descricao","equipamento_tipo"]
    readonly_fields = ["equipamento_name","equipamento_descricao","equipamento_tipo"]
    verbose_name = "Equipamento"
    verbose_name_plural = "Equipamentos"
    extra = 0

    def equipamento_name(self, obj):
        return obj.equipamento.nome()
    equipamento_name.short_description = "Equipamento"
    
    def equipamento_descricao(self, obj):
        return obj.equipamento.descricao
    equipamento_descricao.short_description = "Descrição"

    def equipamento_tipo(self, obj):
        return obj.equipamento.tipo
    equipamento_tipo.short_description = "Tipo"

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


class HostnameIPServidorInLine(admin.TabularInline):
    model = ServidorHostnameIP
    extra = 0
    form = HostnameIPInLineForm
    
    def has_change_permission(self, request, obj=None):
        return False

class HostnameIPTemplateInLine(admin.TabularInline):
    model = TemplateHostnameIP
    extra = 0
    form = HostnameIPInLineForm
    
    def has_change_permission(self, request, obj=None):
        return False

class EquipamentoRackInLine(admin.TabularInline):
    model = Servidor
    fields = ("nome", "rack_tamanho", "rack_posicao")
    ordering = ("-rack_posicao", "nome" )
    readonly_fields = (
        "nome",
        "rack_tamanho",
    )
    extra = 0

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


class EquipamentoParteRackInLine(admin.TabularInline):
    model = EquipamentoParte
    fields = ("name_inline", "rack_tamanho", "rack_posicao")
    readonly_fields = (
        "name_inline",
        "rack_tamanho",
    )
    extra = 0

    def name_inline(self, obj):
        return f"{obj.marca} {obj.modelo} - Patrimônio:{obj.patrimonio}"
    name_inline.short_description = "Equipamento"

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


class AmbienteVirtualServidorInLine(admin.TabularInline):
    model = AmbienteVirtual.servidor.through
    fields = ("servidor",)
    extra = 0
    verbose_name = "Servidor Físico"
    verbose_name_plural = "Servidores Físicos"
    form = AmbienteVirtualServidorInLineForm


@admin.register(HostnameIP)
class HostnameIPAdmin(admin.ModelAdmin):
    change_form_template = "infra/admin/change_form_hostnameip.html"
    search_fields = ["hostname", "ip"]
    list_display = ("hostname", "ip", "reservado")
    form = HostnameIPForm


@admin.register(Rack)
class RackAdmin(admin.ModelAdmin):
    change_form_template = "infra/admin/change_form_rack.html"
    list_display = ("rack", "equipamentos", "predio", "consumo", "equipamentos_consumo", "pdu1", "pdu2")
    list_filter = ["predio" ]
    search_fields = ("rack",)
    form = RackForm
    inlines = (EquipamentoRackInLine, EquipamentoParteRackInLine)

    def equipamentos(self, obj):
        return int(obj.equipamento_set.count())
    equipamentos.short_description = "Qtd. Equipamentos"

    def equipamentos_consumo(self, obj):
        return (obj.equipamento_set.aggregate(Sum("consumo"))['consumo__sum'])
    equipamentos_consumo.short_description = "Consumo dos Equipamentos"

    def add_view(self, request, form_url="", extra_context=None):
        self.readonly_fields = []
        return super().add_view(request, form_url=form_url, extra_context=extra_context)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        self.readonly_fields = ["predio"]
        return super().change_view(request, object_id, form_url=form_url, extra_context=extra_context)


@admin.register(Supercomputador)
class SupercomputadorAdmin(admin.ModelAdmin):
    search_fields = ["marca", "modelo"]
    list_display = ("marca", "modelo", "kafka_topico_realtime", "kafka_topico_historico", "status")
    exclude = ("rack", "rack_tamanho", "rack_posicao", "consumo", "grupos_acesso", "patrimonio", "serie", "descricao", "tipo_uso", "tipo", "status",)


@admin.register(Storage)
class StorageAdmin(admin.ModelAdmin):
    search_fields = ["marca", "modelo"]
    readonly_fields = ("atualizacao",)
    list_display = ("marca", "modelo", "descricao", "capacidade",)
    exclude = ("rack", "rack_tamanho", "rack_posicao", "consumo", "grupos_acesso", "patrimonio", "serie",  "tipo_uso", "tipo", "status",)
    inlines = (StorageAreaInLine,)


@admin.register(Servidor)
class ServidorAdmin(admin.ModelAdmin):
    change_form_template = "infra/admin/change_form_servidor.html"
    delete_confirmation_template = "infra/admin/delete_confirmation_servidor.html"
    change_list_template  = "infra/admin/change_list_servidor.html"
    search_fields = ["nome", "patrimonio", "marca", "modelo"]
    list_filter = ["tipo_uso","tipo" ]
    list_display = ("nome", "patrimonio", "tipo", "tipo_uso",  "predio",  "descricao", "grupo", "tipo_uso", "status")
    fields = ["nome", "tipo", "tipo_uso", "predio", "descricao", "marca", "modelo", "serie", "patrimonio", "garantia", "consumo", "rack", "rack_tamanho", "vinculado", "status", "conta", 'vm_remover']
    readonly_fields = ("status","conta")
    form = ServidorForm
    inlines = (HostnameIPServidorInLine,)

    def grupo(self, obj):
        return obj.grupo_acesso_name()
    grupo.short_description = "Grupo"

    def save_model(self, request, obj, form, change):
        hostname_str = obj.nome.split(" | ")
        obj.nome = hostname_str[0]
        hostname = HostnameIP.objects.get(hostname=obj.nome)
        if change:
            if "descricao" in form.changed_data and obj.conta == "FreeIPA":
                FreeIPA(request).host_mod(obj.freeipa_name, description=obj.descricao)
            super().save_model(request, obj, form, change)
        else:
            hostname.reservado = True
            hostname.save()
            super().save_model(request, obj, form, change)
            ServidorHostnameIP.objects.create(servidor=obj, hostnameip=hostname)

    def delete_model(self, request, obj):
        for server_hostnameip in ServidorHostnameIP.objects.filter(servidor__id=obj.pk):
            hostnameip = server_hostnameip.hostnameip
            hostnameip.reservado = False
            hostnameip.save()
            HistoryInfra(request).delete_servidor(servidor=obj, hostnameip=hostnameip)
        if obj.conta == "FreeIPA":
            client_feeipa = FreeIPA(request)
            client_feeipa.automountlocation_del(obj.freeipa_name_mount)
            client_feeipa.host_delete(obj.freeipa_name)
        if obj.vm_remover and obj.vm_ambiente_virtual:
            XenCrud(request, obj, obj.vm_ambiente_virtual).delete_vm()
        return super().delete_model(request, obj)

    def add_view(self, request, form_url="", extra_context=None):
        extra_context = dict( show_save=False, show_save_and_continue=True)
        self.readonly_fields = ("status","conta")
        self.fields = ["nome", "tipo", "tipo_uso", "predio", "descricao", "marca", "modelo", "serie", "patrimonio", "garantia", "consumo", "rack", "rack_tamanho", "vinculado", "status", "conta"]
        self.inlines = ()
        return super().add_view(request, form_url=form_url, extra_context=extra_context)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        servidor = get_object_or_404(Servidor, id=object_id)
        if servidor.tipo == 'Servidor Virtual' and  servidor.vm_ambiente_virtual:
            self.fields = ["nome", "tipo", "tipo_uso", "predio", "descricao", "status", "conta", "vm_remover"]
        elif servidor.tipo == 'Servidor Virtual':
            self.fields = ["nome", "tipo", "tipo_uso", "predio", "descricao", "status", "conta"]
        else:
            self.fields = ["nome", "tipo", "tipo_uso", "predio", "descricao", "marca", "modelo", "serie", "patrimonio", "garantia", "consumo", "rack", "rack_tamanho", "vinculado", "status", "conta", ]

        self.readonly_fields = ("nome", "status", "conta", "tipo", "tipo_uso", "predio")
        self.inlines = (HostnameIPServidorInLine, GrupoAcessoEquipamentoInLine, OcorrenciaInLine)
        return super().change_view(request, object_id, form_url=form_url, extra_context=extra_context)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, EquipamentoGrupoAcesso) and formset.instance.conta == "FreeIPA":
                Automount(FreeIPA(request), formset.instance, request).adicionar_grupos([instance.grupo_acesso])
                messages.add_message(request, messages.WARNING, "Precisa reiniciar o serviço de AUTOFS no Servidor!")
            if isinstance(instance, ServidorHostnameIP):
                hostnameip = instance.hostnameip
                hostnameip.reservado = True
                hostnameip.save()
                instance.save
        for obj in formset.deleted_objects:
            if isinstance(obj, EquipamentoGrupoAcesso) and formset.instance.conta == "FreeIPA":
                Automount(FreeIPA(request), formset.instance, request).remover_grupos([obj.grupo_acesso])
                messages.add_message(request, messages.WARNING, "Precisa reiniciar o serviço de AUTOFS no Servidor!")
            if isinstance(obj, ServidorHostnameIP):
                hostnameip = obj.hostnameip
                hostnameip.reservado = False
                hostnameip.save()
        return super().save_formset(request, form, formset, change)

    def get_form(self, request, obj=None, **kwargs):
            request._obj_ = obj
            return super(ServidorAdmin, self).get_form(request, obj, **kwargs)


@admin.register(TemplateVM)
class TemplateVMAdmin(admin.ModelAdmin):
    change_form_template = "infra/admin/change_form_template.html"
    search_fields = ["nome", "ambiente_virtual"]
    list_filter = ["ambiente_virtual"]
    list_display = ["nome", "configuracao", "ambiente_virtual" ]
    fields = ["nome", "configuracao", "ambiente_virtual"]
    readonly_fields = []
    inlines = (HostnameIPTemplateInLine,TemplateComandoInLine)

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            if isinstance(instance, TemplateHostnameIP):
                hostnameip = instance.hostnameip
                hostnameip.reservado = True
                hostnameip.save()
                instance.save
        for obj in formset.deleted_objects:
            if isinstance(obj, TemplateHostnameIP):
                hostnameip = obj.hostnameip
                hostnameip.reservado = False
                hostnameip.save()
        return super().save_formset(request, form, formset, change)

    def delete_model(self, request, obj):
        for template_hostnameip in TemplateHostnameIP.objects.filter(servidor__id=obj.pk):
            hostnameip = template_hostnameip.hostnameip
            hostnameip.reservado = False
            hostnameip.save()
        return super().delete_model(request, obj)

    def add_view(self, request, form_url="", extra_context=None):
        self.readonly_fields = []
        return super().add_view(request, form_url=form_url, extra_context=extra_context)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        self.readonly_fields = ['ambiente_virtual']
        return super().change_view(request, object_id, form_url=form_url, extra_context=extra_context)

@admin.register(EquipamentoParte)
class EquipamentoParteAdmin(admin.ModelAdmin):
    search_fields = ["patrimonio", "marca", "modelo"]
    list_display = ("patrimonio", "marca", "modelo", "vinculado", "status")
    readonly_fields = ("status",)
    form = EquipamentoParteForm
    inlines = (OcorrenciaInLine,)


@admin.register(AmbienteVirtual)
class AmbienteVirtualAdmin(admin.ModelAdmin):
    search_fields = ["nome"]
    list_display = ["nome", "virtualizador", "versao"]
    fields = ["nome", "virtualizador", "versao"]
    inlines = (AmbienteVirtualServidorInLine,)


@admin.register(Rede)
class RedeAdmin(admin.ModelAdmin):
    list_display = ("rede", "ip", "prioridade_montagem")
