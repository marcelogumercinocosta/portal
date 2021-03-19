from apps.colaborador.forms import ColaboradorBaseForm
from functools import update_wrapper

from django.contrib import admin

from apps.colaborador.models import (Colaborador, Vinculo)
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
    form = ColaboradorBaseForm
    fieldsets = [
            ("Informações Pessoais", {"fields": ["first_name", "last_name",  "data_nascimento", "email", "telefone"  ]}),
            ("Informações Profissionais", {"fields": ["vinculo", "predio", "divisao", "ramal", "responsavel", "registro_inpe", "empresa", "data_inicio", "data_fim", "externo"]}),
            ("Informações Portal", {"fields": [ "is_active",  "date_joined"]}),
        ]
    readonly_fields =  [ "first_name", "last_name", "email", "data_nascimento", "telefone", "cpf", "documento_tipo", "documento", "vinculo", "predio", "divisao", "ramal", "responsavel", "data_inicio", "data_fim", "registro_inpe", "empresa", "externo", "username", "uid", "is_superuser", "is_staff", "is_active", "last_login", "data_inicio", "data_fim", "date_joined"]
    
    def change_view(self, request, object_id, form_url="", extra_context=None):
        colaborador = Colaborador.objects.get(pk=object_id)
        if (not colaborador.is_active):
            self.fieldsets = [
                ("Informações Pessoais", {"fields": ["first_name", "last_name",  "data_nascimento", "email", "telefone"  ]}),
                ("Informações Profissionais", {"fields": ["vinculo", "predio", "divisao", "ramal", "responsavel", "registro_inpe", "empresa", "data_inicio", "data_fim", "externo"]}),
                ("Informações Portal", {"fields": [ "is_active",  "date_joined"]}),
            ]
            self.readonly_fields =  [ "first_name", "last_name", "email", "data_nascimento", "nacionalidade","telefone", "cpf", "documento_tipo", "documento",  "vinculo", "predio", "divisao", "ramal","responsavel", "data_inicio", "data_fim", "registro_inpe", "empresa", "externo", "username", "uid", "is_superuser", "is_staff", "is_active", "last_login", "date_joined"]
            self.inlines = []
        elif request.user.is_superuser:
            self.fieldsets = [
                ("Informações Pessoais", {"fields": ["first_name", "last_name", "email", "data_nascimento",  "telefone", "cpf", "documento_tipo", "documento"]}),
                ("Informações Profissionais", {"fields": ["vinculo", "predio", "divisao", "ramal", "responsavel", "registro_inpe", "empresa", "data_inicio", "data_fim", "externo"]}),
                ("Informações Portal", {"fields": ["username", "uid", "is_superuser", "is_staff", "is_active", "last_login", "date_joined"]}),
            ]
            self.inlines = [GroupInLine, ColaboradorGrupoAcessoInLineRead]
            self.readonly_fields = ["username", "uid", "is_staff", "is_active", "last_login", "date_joined", "data_inicio", "registro_inpe", "data_fim", "vinculo"]
        else:
            if request.user.has_perm("colaborador.secretaria_colaborador"):
                self.fieldsets = [
                    ("Informações Pessoais", {"fields": ["first_name", "last_name", "email", "data_nascimento", "telefone",  "cpf", "documento_tipo", "documento"]}),
                    ("Informações Profissionais", {"fields": ["vinculo", "predio", "divisao", "ramal", "responsavel", "registro_inpe", "empresa", "data_inicio", "data_fim", "externo"]}),
                ]
                self.readonly_fields = ["username", "uid", "is_staff", "is_active", "last_login", "date_joined", "data_inicio", "registro_inpe", "data_fim", "vinculo"]
            else:
                self.fieldsets = [
                    ("Informações Pessoais", {"fields": ["first_name", "last_name", "data_nascimento", "email", "telefone",]}),
                    ("Informações Profissionais", {"fields": ["vinculo", "predio", "divisao", "ramal", "responsavel", "registro_inpe", "empresa", "data_inicio", "data_fim", "externo"]}),
                    ("Informações Portal", {"fields": ["username", "uid", "is_superuser", "is_staff", "is_active", "last_login", "date_joined"]}),
                ]
                self.readonly_fields = [ "first_name", "last_name",  "data_nascimento", "username", "uid", "is_staff", "registro_inpe", "is_active", "last_login", "date_joined", "vinculo", "predio", "divisao", "responsavel", "registro_inpe", "empresa", "data_inicio", "data_fim", "vinculo", "is_superuser"]
            self.inlines = [GroupInLine, ColaboradorGrupoAcessoInLineRead]
        self.fieldsets = self._corrigir_fieldsets(colaborador, self.fieldsets)
        return super(ColaboradorAdmin, self).change_view(request, object_id, form_url, extra_context)

    def _corrigir_fieldsets(self, colaborador, fieldsets_puro):
        fields_exclude_colaborador = {
            "Administrador":["cpf", "data_nascimento", "registro_inpe", "empresa", "data_fim", "responsavel", ],
            "Servidor":["responsavel", "empresa", "data_fim", "externo"],
            "Bolsista":["empresa", "registro_inpe",],
            "Estagiário":["empresa", "registro_inpe",],
            "Terceiro":["registro_inpe",]
        }
        fields_exclude = fields_exclude_colaborador[colaborador.vinculo.vinculo]
        if colaborador.externo:
            fields_exclude.append('ramal')
            fields_exclude.append('predio')
        fields = []
        for key, value in fieldsets_puro:
            fields.append( (key, {"fields": [item for item in value['fields'] if item not in set(fields_exclude)] }) )
        return fields


    def save_model(self, request, obj, form, change):
        if change and ("ramal" in form.changed_data or "email" in form.changed_data):
            FreeIPA(request).user_mod(obj.username, email=obj.email, ramal=obj.ramal)
        super().save_model(request, obj, form, change)
