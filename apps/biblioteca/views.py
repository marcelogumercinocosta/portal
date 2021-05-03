from garb.views import ViewContextMixin
from apps.biblioteca.models import Documento
from django.views.generic import ListView
from django.db.models import Q

class DocumentosListView( ViewContextMixin, ListView, ):
    template_name = 'biblioteca/documento_list.html'
    title = 'Biblioteca de Documentos'
    model = Documento

    def get_queryset(self):
        queryset = super().get_queryset()
        grupos_usuario_id = [ x.id for x in self.request.user.groups.all()]
        return queryset.filter(Q(grupo__id__in=grupos_usuario_id) | Q(grupo=None))