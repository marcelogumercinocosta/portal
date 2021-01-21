from django.contrib import admin
from apps.desk.models import (Ticket, Problema)
from apps.desk.forms import TicketForm
from django.db.models import Q

@admin.register(Problema)
class ProblemaAdmin(admin.ModelAdmin):
    list_display = ["problema", 'grupo_portal']
    list_filter = ["grupo_portal" ]
    search_fields = ["problema", 'grupo_portal']


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    change_form_template = "desk/admin/change_form_ticket.html"
    search_fields = ["ticket"]
    list_display = ["ticket", 'status', 'colaborador']
    list_filter = ["status" ]
    form = TicketForm
    filter_horizontal = ['equipamento']

    def save_model(self, request, obj, form, change):
        obj.operador_id = request.user.pk
        super().save_model(request, obj, form, change)

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        if db_field.name == 'equipamento':
            qs = kwargs.get('queryset', db_field.remote_field.model.objects.filter(Q(tipo='Servidor Físico') | Q(tipo='Servidor Virtual')))
            kwargs['queryset'] = qs.select_related('servidor')
        return super().formfield_for_manytomany(db_field, request=request, **kwargs)