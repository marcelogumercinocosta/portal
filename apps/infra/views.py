
from django.http.response import Http404
from apps.infra.utils.xen_crud import XenCrud
import base64
import io
import json
from itertools import chain

import pyqrcode
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import (LoginRequiredMixin, PermissionRequiredMixin)
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView
from django.views.generic.base import RedirectView, TemplateView
from django.views.generic.edit import CreateView, FormView, UpdateView

from apps.core.tasks import send_email_task
from apps.core.utils.freeipa import FreeIPA
from apps.infra.forms import OcorrenciaForm, ServidorVMForm
from apps.core.models import Predio
from apps.infra.models import ( LINHAS, Equipamento, EquipamentoParte, Ocorrencia, Rack, Servidor, TemplateVM)
from apps.infra.utils.freeipa_location import Automount
from apps.infra.utils.datacenter import ( DataCenterMap, RackMap)
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


class CriarServidorLdapView(LoginRequiredMixin, PermissionRequiredMixin, RedirectView):
    permission_required = "infra.change_servidor"

    def get_redirect_url(self, *args, **kwargs):
        servidor = get_object_or_404(Servidor, id=kwargs["pk"])
        grupos_acesso = servidor.grupos_acesso.all()
        if grupos_acesso.exists() and servidor.conta == "Aguardando":
            client_feeipa = FreeIPA(self.request)
            if client_feeipa.set_host(servidor, description=servidor.descricao):
                automount = Automount(client_feeipa, servidor, self.request)
                automount.adicionar_grupos(grupos_acesso)
                automount.adicionar_oper()
                automount.adicionar_home()
                HistoryInfra(self.request).novo_servidor(servidor=servidor)
                send_email_task.delay("Servidor Criado",f"O Servidor: {servidor.nome} foi criado no FreeIPA, por:{self.request.user.username}",[settings.EMAIL_SYSADMIN])
                servidor.conta = "FreeIPA"
                servidor.save()
                if servidor.tipo == 'Servidor Virtual':
                    return reverse_lazy("infra:criar_vm", kwargs={"pk": servidor.id, })
        else:
            messages.add_message(self.request, messages.ERROR, "Confira o Cadastro, existe informação faltando ou não salva! É necessário um grupo de acesso! ")
        return reverse_lazy("admin:infra_servidor_change", kwargs={"object_id": servidor.id, })


class CriarServidorLocalView(LoginRequiredMixin, PermissionRequiredMixin, RedirectView):
    permission_required = "infra.change_servidor"

    def get_redirect_url(self, *args, **kwargs):
        servidor = get_object_or_404(Servidor, id=kwargs["pk"])
        grupos_acesso = servidor.grupos_acesso.all()
        if grupos_acesso.exists() and servidor.conta == "Aguardando":
            HistoryInfra(self.request).novo_servidor(servidor=servidor)
            send_email_task.delay("Servidor Criado",f"O Servidor: {servidor.nome} foi criado com conta Local, por:{self.request.user.username}",[settings.EMAIL_SYSADMIN])
            servidor.conta = "Local"
            servidor.save()
            if servidor.tipo == 'Servidor Virtual':
                return reverse_lazy("infra:criar_vm", kwargs={"pk": servidor.id, })
        else:
            messages.add_message(self.request, messages.ERROR, "Confira o Cadastro, existe informação faltando ou não salva! É necessário um grupo de acesso! ")
        return reverse_lazy("admin:infra_servidor_change", kwargs={"object_id": servidor.id, })

class CriarVmView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    form_class = ServidorVMForm
    template_name = "infra/servidor/vm.html"
    permission_required = "infra.change_servidor"
    task = 0

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = ServidorVMForm(initial={'servidor': self.kwargs['pk'] })
        context["opts"] = Servidor._meta
        context["original"] = get_object_or_404(Servidor, id=self.kwargs['pk'])
        context["template"] = 0
        return context
    
    def form_valid(self, form):
        vm = get_object_or_404(Servidor, id=form.cleaned_data['servidor'])
        self.template = form.cleaned_data['template']
        memoria = form.cleaned_data['memoria']
        cpu = form.cleaned_data['cpu']
        self.task = XenCrud(self.request, vm, self.template.ambiente_virtual).create_vm(self.template, memoria, cpu)
        if not self.task:
            return super().form_invalid(form)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("infra:criar_vm_progress", kwargs={"pk": self.kwargs['pk'], "task_id": self.task.id, "template_id": self.template.id  })

class CriarVmProgressView(LoginRequiredMixin, TemplateView):
    template_name = "infra/servidor/vm.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["opts"] = Servidor._meta
        context["original"] = get_object_or_404(Servidor, id=self.kwargs['pk'])
        context["template"] = get_object_or_404(TemplateVM, id=self.kwargs['template_id'])
        context["task_id"] = self.kwargs['task_id'] 
        return context