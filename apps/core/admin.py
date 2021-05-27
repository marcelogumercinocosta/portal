from django.contrib import admin
from apps.core.forms import GrupoTrabalhoForm, ResponsavelGrupoTrabalhoInLineForm, DivisaoForm
from apps.core.models import GrupoTrabalho, GrupoAcesso, Divisao, GrupoPortal, ResponsavelGrupoTrabalho, ColaboradorGrupoAcesso, Predio
from apps.core.utils.freeipa import FreeIPA
from apps.infra.admin import StorageAreaGrupoTrabalhoInLine, GrupoAcessoEquipamentoInLineRead
from django.contrib.auth.models import Group


class GroupInLine(admin.TabularInline):
    model = Group.user_set.through
    extra = 0
    verbose_name = "Grupo no Portal"
    verbose_name_plural = "Grupos no Portal"

    def get_formset(self, request, obj=None, **kwargs):
        formset = super(GroupInLine, self).get_formset(request, obj, **kwargs)
        formset.form.base_fields["group"].label = "Grupo no Portal"
        return formset

    def formfield_for_foreignkey(self, db_field, request, **kwargs):    
        formfield = super().formfield_for_foreignkey(db_field, request, **kwargs)
        cache = getattr(request, 'db_field_cache', {})
        formfield.cache_choices = True
        if db_field.name in cache:
            formfield.choices = cache[db_field.name]
        else:
            formfield.choice_cache = [
                formfield.choices.choice(obj) for obj in formfield.choices.queryset.all()
            ]
            request.db_field_cache = cache
            request.db_field_cache[db_field.name] = formfield.choices
        return formfield


class ResponsavelGrupoTrabalhoInLine(admin.TabularInline):
    model = ResponsavelGrupoTrabalho
    fields = ("responsavel",)
    extra = 0
    form = ResponsavelGrupoTrabalhoInLineForm


class GrupoAcessoInLine(admin.TabularInline):
    model = GrupoAcesso
    fields = ("grupo_acesso", "data")
    readonly_fields = ("grupo_acesso", "data")
    verbose_name = "Grupo de Acesso"
    verbose_name_plural = "Grupos de Acesso"
    extra = 0

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


class ColaboradorGrupoAcessoInLineRead(admin.TabularInline):
    model = ColaboradorGrupoAcesso
    fields = ("grupo_acesso", "status", "atualizacao")
    readonly_fields = ("grupo_acesso", "status", "atualizacao")
    extra = 0
    can_delete = False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

class GrupoAcessoColaboradorInLineRead(admin.TabularInline):
    model = ColaboradorGrupoAcesso
    fields = ("nome", "username", "ramal", "email", "status")
    readonly_fields = ("nome", "username", "ramal", "email", "status")
    can_delete = False
    extra = 0
    verbose_name = "Colaborador"
    verbose_name_plural = "Colaboradores"

    def nome(self, obj):
        return obj.colaborador.full_name

    nome.short_description = "colaborador"

    def username(self, obj):
        return obj.colaborador.username

    username.short_description = "user"

    def ramal(self, obj):
        return obj.colaborador.ramal

    ramal.short_description = "ramal"

    def email(self, obj):
        return obj.colaborador.email

    email.short_description = "email"

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Divisao)
class DivisaoAdmin(admin.ModelAdmin):
    search_fields = ["divisao"]
    list_display = ["divisao", "email", "chefe", "chefe_ativo", "chefe_substituto", "chefe_substituto_ativo"]
    fields = ["divisao", "divisao_completo", "email", "coordenacao", "chefe", "chefe_ativo", 'chefe_substituto', 'chefe_substituto_ativo']
    readonly_fields = []
    form = DivisaoForm

    def change_view(self, request, object_id, form_url="", extra_context=None):
        if request.user.is_superuser:
            self.readonly_fields = []
        else:
            self.readonly_fields = ["divisao", 'divisao_completo','coordenacao']
        return super(DivisaoAdmin, self).change_view(request, object_id, form_url, extra_context)



@admin.register(Predio)
class PredioAdmin(admin.ModelAdmin):
    search_fields = ["predio"]
    list_display = ("predio", "predio_sistema", "linhas","colunas", "sensores")


@admin.register(GrupoAcesso)
class GrupoAcessoAdmin(admin.ModelAdmin):
    search_fields = ["grupo_acesso"]
    list_display = (
        "grupo_acesso",
        "grupo_trabalho",
        "hbac_freeipa",
        "tipo",
        "data",
    )
    list_filter = ("tipo",)
    readonly_fields = ("grupo_acesso", "grupo_trabalho", "hbac_freeipa", "tipo", "data")
    inlines = (GrupoAcessoColaboradorInLineRead, GrupoAcessoEquipamentoInLineRead)
    change_form_template = "core/admin/change_form_grupo_acesso.html"

    def has_add_permission(self, request):
        return False


@admin.register(GrupoTrabalho)
class GrupoTrabalhoAdmin(admin.ModelAdmin):
    model = GrupoTrabalho
    change_form_template = "core/admin/change_form_grupo_trabalho.html"
    list_display = ("grupo", "divisao", "oper", "dev", "pesq", "doc", "share", "data_criado", "confirmacao")
    readonly_fields = ["data_criado","confirmacao"]
    list_filter = ("divisao",)
    search_fields = ["grupo"]
    ordering = ("grupo", "divisao")

    form = GrupoTrabalhoForm
    inlines = (ResponsavelGrupoTrabalhoInLine, StorageAreaGrupoTrabalhoInLine, GrupoAcessoInLine)

    def oper(self, obj):
        return obj.operacional
    oper.short_description = "oper"
    oper.boolean = True

    def dev(self, obj):
        return obj.desenvolvimento
    dev.short_description = "dev"
    dev.boolean = True

    def pesq(self, obj):
        return obj.pesquisa
    pesq.short_description = "pesq"
    pesq.boolean = True

    def doc(self, obj):
        return obj.documento
    doc.short_description = "doc"
    doc.boolean = True

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        self.readonly_fields = ["data_criado","confirmacao"]
        if GrupoTrabalho.objects.get(pk=object_id).data_criado:
            self.readonly_fields = ["grupo_sistema", "gid", "divisao", "data_criado","confirmacao"]
        return super(GrupoTrabalhoAdmin, self).change_view(request, object_id, form_url, extra_context)

    def delete_model(self, request, obj):
        client_feeipa = FreeIPA(request)
        if obj.data_criado and client_feeipa.group_find_count(cn=obj.grupo_sistema) == 1:
            grupos_acesso = GrupoAcesso.objects.filter(grupo_trabalho__id=obj.id)
            for grupo_acesso  in grupos_acesso:
                client_feeipa.remove_hbac_group_rule(grupo_acesso)
            client_feeipa.remove_grupo(obj)
        super(GrupoTrabalhoAdmin, self).delete_model(request, obj)

    def add_view(self, request, form_url="", extra_context=None):
        self.readonly_fields = ["data_criado","confirmacao"]
        return super(GrupoTrabalhoAdmin, self).add_view(request, form_url, extra_context)



@admin.register(GrupoPortal)
class GrupoPortalAdmin(admin.ModelAdmin):
    model = GrupoPortal
    search_fields = ("name",)
    ordering = ("name",)
    filter_horizontal = ("permissions",)

admin.site.unregister(Group)