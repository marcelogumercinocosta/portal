import base64
import io
import json
from builtins import range
from itertools import chain

import png
import pyqrcode
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin)
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView
from django.views.generic.base import RedirectView, TemplateView
from django.views.generic.edit import CreateView

from apps.core.tasks import send_email_task
from apps.core.utils.freeipa import FreeIPA
from apps.infra.forms import OcorrenciaForm
from apps.core.models import Predio
from apps.infra.models import (LINHAS, Equipamento, EquipamentoParte, Ocorrencia, Rack, Rede, Servidor, StorageGrupoAcessoMontagem)
from apps.infra.utils.freeipa_location import Automount
from apps.infra.utils.datacenter import (DatacenterArea, DataCenterMap, RackMap)
from apps.infra.utils.history import HistoryInfra
from garb.views import ViewContextMixin


class DataCenterView(ViewContextMixin, TemplateView):
    template_name = "infra/datacenter/datacenter.html"
    title = 'Monitoramento Datacenter'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["predios"] = Predio.objects.all().filter(linhas__isnull=False, colunas__isnull=False,)
        return context


class DataCenterPredioView(TemplateView):
    template_name = "infra/datacenter/datacenter_predio.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        predio = get_object_or_404(Predio, id=kwargs["pk"])
        datacenter_map = DataCenterMap(predio)
        context["quantidade_racks"] = Rack.objects.filter(predio=predio).count()
        context["quantidade_equipamentos"] = Equipamento.objects.filter(predio=predio).filter(Q(tipo='Servidor Físico') | Q(tipo='Equipamento Físico')).count()
        context["matriz_datacenter"] = datacenter_map.draw_datacenter(sensor=True)
        context["sensores"] = datacenter_map.sensores
        context["title"] = predio.predio
        return context


class DataCenterMapView(TemplateView):
    template_name = "infra/datacenter/datacenter_map.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        predio = get_object_or_404(Predio, id=kwargs["pk"])
        datacenter = DataCenterMap(predio)
        context["matriz_datacenter"] = datacenter.draw_datacenter()
        return context


class DataCenterMapEditView(TemplateView):
    template_name = "infra/datacenter/datacenter_map.html"
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rack = get_object_or_404(Rack, id=kwargs["pk"])
        datacenter = DataCenterMap(rack.predio, id_rack=rack.pk)
        context["matriz_datacenter"] = datacenter.draw_datacenter()
        return context


class DataCenterJSONView(TemplateView):
    search = None
    racks_id_templates = []

    def get(self, request, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        self.search = request.GET.get("search", None).lower()
        return self.render_to_response(context)

    def render_to_response(self, context, **response_kwargs):
        if self.search:
            servidores = chain(Servidor.objects.filter(nome__contains=str(self.search)), EquipamentoParte.objects.filter(marca__icontains=str(self.search)), EquipamentoParte.objects.filter(modelo__icontains=str(self.search)))
            self.racks_id_templates = ['div[data-element="#rack_' + str(x.rack.id) + '"]' for x in servidores]
        return HttpResponse(json.dumps(list(dict.fromkeys(self.racks_id_templates))), content_type="application/json")


class DataCenterRackDetailView(TemplateView):
    template_name = "infra/datacenter/rack_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rack = RackMap(self.request.GET.get("pk", None), self.request.GET.get("search", None).lower())
        context["rack"] = rack.draw_rack()
        return context


class RackQRCodeView(DetailView):
    model = Rack
    template_name = "infra/rack/qrcode.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qrcode = pyqrcode.create(self.request.scheme + "://" + self.request.get_host() + reverse("infra:rack_detail", args=[context["rack"].id]))
        file = io.BytesIO()
        qrcode.png(file, scale=6)
        context["qrcode"] = base64.b64encode(file.getvalue()).decode("ascii")
        return context


class RackDetailView(DetailView):
    model = Rack
    template_name = "infra/rack/rack_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rack = RackMap(context["rack"].id, None)
        context["rack"] = rack.draw_rack()
        return context


class RackServerDetailView(DetailView):
    model = Equipamento
    template_name = "infra/rack/rack_server_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form_ocorrencia"] = OcorrenciaForm(initial={"equipamento": self.get_object()})
        return context


class OcorrenciaNewView(CreateView):
    model = Ocorrencia
    form_class = OcorrenciaForm
    template_name = "infra/rack/rack_server_detail.html"
    rack_id = 0

    def form_valid(self, form):
        ocorrencia = form.save(commit=False)
        self.rack_id = ocorrencia.equipamento.rack.id
        return super(OcorrenciaNewView, self).form_valid(form)

    def get_success_url(self, **kwargs):
        return reverse_lazy("infra:rack_detail", kwargs={"pk": self.rack_id})


class CriarServidorView(LoginRequiredMixin, PermissionRequiredMixin, RedirectView):
    permission_required = "infra.change_servidor"

    def get_redirect_url(self, *args, **kwargs):
        servidor = get_object_or_404(Servidor, id=kwargs["pk"])
        grupos_acesso = servidor.grupos_acesso.all()
        if grupos_acesso.exists() and servidor.ldap == False:
            client_feeipa = FreeIPA(self.request)
            if client_feeipa.set_host(servidor, description=servidor.descricao):
                automount = Automount(client_feeipa, servidor, self.request)
                automount.adicionar_grupos(grupos_acesso)
                automount.adicionar_oper()
                automount.adicionar_home()
                HistoryInfra(self.request).novo_servidor(servidor=servidor)
                send_email_task.delay("Servidor Criado",f"O Servidor: {servidor.nome} foi criado no FreeIPA, por:{self.request.user.username}",[settings.EMAIL_SYSADMIN])
                servidor.ldap = True
                servidor.save()
        else:
            messages.add_message(self.request, messages.ERROR, "Confira o Cadastro, existe informação faltando ou não salva! É necessário um grupo de acesso! ")
        return reverse_lazy("admin:infra_servidor_change", kwargs={"object_id": servidor.id})
