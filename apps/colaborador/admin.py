from functools import update_wrapper

from django.contrib import admin
from django.shortcuts import get_object_or_404

from apps.colaborador.forms import ColaboradorBaseForm
from apps.colaborador.models import (Colaborador, Conta, Vinculo)
from apps.core.admin import ColaboradorGrupoAcessoInLineRead, GroupInLine
from apps.core.utils.freeipa import FreeIPA

@admin.register(Vinculo)
class VinculoAdmin(admin.ModelAdmin):
    search_fields = ["vinculo"]


@admin.register(Colaborador)
class ColaboradorAdmin(admin.ModelAdmin):
    change_form_template = "colaborador/admin/change_form_colaborador.html"
    change_list_template = "colaborador/admin/change_list_colaborador.html"
    list_display = ("username", "full_name", "email", "ramal", "vinculo", "is_active")
    search_fields = ["username","first_name", "last_name", "email"]
    list_filter = ["is_active"]
    inlines = [GroupInLine, ColaboradorGrupoAcessoInLineRead]
    fieldsets = [
            ("Informações Pessoais", {"fields": ["first_name", "last_name",  "data_nascimento", "email", ]}),
            ("Informações Portal", {"fields": ["username", "uid", "is_staff", "is_active", "last_login", "date_joined"]}),
            ("Informações Profissionais", {"fields": ["vinculo", "predio", "divisao", "ramal", "responsavel", "registro_inpe", "empresa", "data_inicio", "data_fim"]}),
        ]
    readonly_fields = [ "first_name", "last_name",  "data_nascimento", "username", "uid", "is_staff", "is_active", "last_login", "date_joined", "vinculo", "predio", "divisao", "responsavel", "registro_inpe", "empresa", "data_inicio", "data_fim"]

    def change_view(self, request, object_id, form_url="", extra_context=None):
        colaborador = Colaborador.objects.get(pk=object_id)
        if not request.user.is_superuser:
            if (not colaborador.is_active):
                self.readonly_fields = [ "username", "uid", "last_login", "date_joined", "vinculo", "predio", "divisao", "ramal", "responsavel", "registro_inpe", "empresa", "data_inicio", "data_fim", "first_name", "last_name", "email", "data_nascimento", "nacionalidade", "sexo", "estado_civil", "telefone", "area_formacao", "cpf", "documento_tipo", "documento", "cep", "endereco", "numero", "bairro", "cidade", "estado", "contato_de_emergencia_nome", "contato_de_emergencia_parentesco", "contato_de_emergencia_telefone" ]
            else:
                if request.user.has_perm("colaborador.secretaria_colaborador"):
                    self.fieldsets = [
                        ("Informações Pessoais", {"fields": ["first_name", "last_name", "email", "data_nascimento", "nacionalidade", "sexo", "estado_civil", "telefone", "area_formacao", "cpf", "documento_tipo", "documento"]}),
                        ("Informações Residenciais", {"fields": ["cep", "endereco", "numero", "bairro", "cidade", "estado"]}),
                        ("Contato de Emergência", {"fields": ["contato_de_emergencia_nome", "contato_de_emergencia_parentesco", "contato_de_emergencia_telefone"]}),
                        ("Informações Profissionais", {"fields": ["vinculo", "predio", "divisao", "ramal", "responsavel", "registro_inpe", "empresa", "data_inicio", "data_fim"]}),
                    ]
                else:
                    self.readonly_fields = ["username", "uid", "email" , "is_staff", "is_active", "last_login", "date_joined", "data_fim"]
            self.inlines = [ColaboradorGrupoAcessoInLineRead]
        else:
            self.fieldsets = [
                ("Informações Pessoais", {"fields": ["first_name", "last_name", "email", "data_nascimento", "nacionalidade", "sexo", "estado_civil", "telefone", "area_formacao", "cpf", "documento_tipo", "documento"]}),
                ("Informações Residenciais", {"fields": ["cep", "endereco", "numero", "bairro", "cidade", "estado"]}),
                ("Contato de Emergência", {"fields": ["contato_de_emergencia_nome", "contato_de_emergencia_parentesco", "contato_de_emergencia_telefone"]}),
                ("Informações Profissionais", {"fields": ["vinculo", "predio", "divisao", "ramal", "responsavel", "registro_inpe", "empresa", "data_inicio", "data_fim"]}),
                ("Informações Portal", {"fields": ["username", "uid", "is_superuser", "is_staff", "is_active", "last_login", "date_joined"]}),
            ]
            inlines = [GroupInLine, ColaboradorGrupoAcessoInLineRead]
            self.readonly_fields = ["username", "uid", "is_staff", "is_active", "last_login", "date_joined"]
        return super(ColaboradorAdmin, self).change_view(request, object_id, form_url, extra_context)


    def save_model(self, request, obj, form, change):
        if change and ("ramal" in form.changed_data or "email" in form.changed_data):
            FreeIPA(request).user_mod(obj.username, email=obj.email, ramal=obj.ramal)
        super().save_model(request, obj, form, change)


@admin.register(Conta)
class ContaAdmin(admin.ModelAdmin):
    change_form_template = "colaborador/admin/change_form_conta.html"
    fieldsets = [
        ("Informações Portal", {"fields": ["username", "uid", "last_login", "date_joined"]}),
        ("Informações Profissionais", {"fields": ["vinculo", "predio", "divisao", "ramal", "responsavel", "registro_inpe", "empresa", "data_inicio", "data_fim"]}),
        ("Informações Pessoais", {"fields": ["first_name", "last_name", "email", "data_nascimento", "nacionalidade", "sexo", "estado_civil", "telefone", "area_formacao", "cpf", "documento_tipo", "documento"]}),
        ("Informações Residenciais", {"fields": ["cep", "endereco", "numero", "bairro", "cidade", "estado"]}),
        ("Contato de Emergência", {"fields": ["contato_de_emergencia_nome", "contato_de_emergencia_parentesco", "contato_de_emergencia_telefone"]}),
    ]
    readonly_fields = [ "username", "uid", "last_login", "date_joined", "vinculo", "predio", "divisao", "ramal", "responsavel", "registro_inpe", "empresa", "data_inicio", "data_fim", "first_name", "last_name", "email", "data_nascimento", "nacionalidade", "sexo", "estado_civil", "telefone", "area_formacao", "cpf", "documento_tipo", "documento", "cep", "endereco", "numero", "bairro", "cidade", "estado", "contato_de_emergencia_nome", "contato_de_emergencia_parentesco", "contato_de_emergencia_telefone"
    ]
    inlines = [ColaboradorGrupoAcessoInLineRead]

    def get_urls(self):
        from django.urls import path

        info = self.model._meta.app_label, self.model._meta.model_name
        urlpatterns = [
            path("", self.admin_site.admin_view(self.change_view), name="%s_%s_changelist" % info),
            path("", self.admin_site.admin_view(self.change_view), name="%s_%s_conta" % info),
        ]
        return urlpatterns

    def change_view(self, request, form_url="", extra_context=None):
        object_id = str(request.user.id)
        return super().change_view(request, object_id, form_url=form_url, extra_context=extra_context)
