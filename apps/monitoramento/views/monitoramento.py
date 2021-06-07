from django.views.generic.base import TemplateView
from apps.monitoramento.models import TipoMonitoramento
from garb.views import ViewContextMixin

class FerramentaView(ViewContextMixin, TemplateView):
    template_name = "monitoramento/ferramentas/ferramentas.html"
    title = "Ferramentas"

    def get_context_data(self, **kwargs):
        context = super(FerramentaView, self).get_context_data(**kwargs)
        context["tipos_monitoramento"] = TipoMonitoramento.objects.all()
        return context


