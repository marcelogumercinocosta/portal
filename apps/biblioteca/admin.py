from django.contrib import admin
from apps.biblioteca.models import Documento
from django.db.models import Q


class GroupInLine(admin.TabularInline):
    model = Documento.grupo.through
    fields = ("group",)
    extra = 0
    verbose_name = "Acesso por Grupo no portal"
    verbose_name_plural =  "Acesso por Grupos no Portal"

    def get_formset(self, request, obj=None, **kwargs):
        formset = super(GroupInLine, self).get_formset(request, obj, **kwargs)
        formset.form.base_fields["group"].label = "Grupo no Portal"
        return formset

# Register your models here.
@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    search_fields = [ "documento"]
    fields = ("documento","upload", "descricao", "criado", "modificado" )
    list_display = ["documento",  "descricao", "criado", "modificado" ]
    readonly_fields = ["criado", "modificado" ]
    inlines = [GroupInLine]

    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        grupos_usuario_id = [ x.id for x in request.user.groups.all()]
        return queryset.filter(Q(grupo__id__in=grupos_usuario_id) | Q(grupo=None))