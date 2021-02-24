import datetime
from io import BytesIO
from os import remove

import xhtml2pdf.pisa as pisa
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import (LoginRequiredMixin, PermissionRequiredMixin)
from django.contrib.contenttypes.models import ContentType
from django.contrib.staticfiles import finders
from django.core.mail import EmailMessage
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.template.loader import get_template
from django.urls import reverse_lazy
from django.utils.encoding import force_text
from django.views.generic.base import RedirectView, TemplateView, View

from apps.core.models import GrupoAcesso, GrupoPortal, GrupoTrabalho, ColaboradorGrupoAcesso
from apps.colaborador.models import Colaborador
from apps.infra.models import Servidor
from apps.core.tasks import send_email_task
from apps.core.utils.freeipa import FreeIPA
from apps.core.utils.history import HistoryCore
from apps.core.utils.updategrupo import UpdateGrupoAcesso, UpdateColaboradorGrupo
from garb.views import ViewContextMixin


class AtualizarAssinaturaView(LoginRequiredMixin, PermissionRequiredMixin, View):
    template_name = "core/pdf/grupo.html"
    permission_required = "core.change_grupotrabalho"

    def get(self, request, *args, **kwargs):
        grupo = get_object_or_404(GrupoTrabalho, id=kwargs["pk"])
        responsaveis = grupo.responsavelgrupotrabalho_set.all()
        if responsaveis.count() > 0:
            context = {
                "title": "Atualizar Assinatura do Grupo",
                "logo": finders.find("image/logo.png"),
                "checkbox_on": finders.find("core/image/checkbox_on.png"),
                "checkbox_off": finders.find("core/image/checkbox_off.png"),
                "grupo": grupo,
                "responsaveis": responsaveis,
            }
            result = BytesIO()
            template = get_template(self.template_name)
            html = template.render(context)
            pisa.pisaDocument(BytesIO(html.encode("utf8")), result)
            return HttpResponse(result.getvalue(), content_type="application/pdf")
        return HttpResponse("Confirme as informações do Cadastro e/ou Responsáveis!", content_type="text/plain; charset=iso-8859-1")


class ConfirmarAssinaturaView(LoginRequiredMixin, PermissionRequiredMixin, RedirectView):
    permission_required = "core.change_grupotrabalho"

    def get_redirect_url(self, *args, **kwargs):
        grupo = get_object_or_404(GrupoTrabalho, id=kwargs["pk"])
        responsaveis_grupotrabalho = grupo.responsavelgrupotrabalho_set.all()
        if responsaveis_grupotrabalho.count() > 0:
            grupo.save_confirm()
            messages.add_message(self.request, messages.SUCCESS, "Assinatura confirmada, FreeIPA já pode ser Atualizado")
            HistoryCore(self.request).confirmar_assinatura(grupo=grupo)
            return reverse_lazy("admin:core_grupotrabalho_change", kwargs={"object_id": grupo.id})
        messages.add_message(self.request, messages.WARNING, "Confirme as informações do Cadastro e/ou Responsáveis!")
        return reverse_lazy("admin:core_grupotrabalho_change", kwargs={"object_id": grupo.id})


class CriarContaGrupoTrabalhoView(LoginRequiredMixin, PermissionRequiredMixin, RedirectView):
    permission_required = "core.change_grupotrabalho"

    def get_redirect_url(self, *args, **kwargs):
        grupo_trabalho = get_object_or_404(GrupoTrabalho, id=kwargs["pk"])
        tste = grupo_trabalho.responsavelgrupotrabalho_set.all()
        if grupo_trabalho.responsavelgrupotrabalho_set.all().exists() and grupo_trabalho.gid > 0 and grupo_trabalho.confirmacao == True:
            client_feeipa = FreeIPA(self.request)
            if client_feeipa.group_find_count(cn=grupo_trabalho.grupo_sistema) == 0:
                # Cria Conta de User Group
                if client_feeipa.set_grupo(grupo_trabalho):
                    send_email_task.delay("Conta de Grupo Criada",f"A Conta para Grupo de trabalho: <b>{grupo_trabalho.grupo}</b> foi criada no FreeIPA, por:{self.request.user.username,}",[settings.EMAIL_SYSADMIN])
                    # Atualiza Grupos de Acesso
                    history_core = HistoryCore(self.request)
                    history_core.update_grupo_acesso(grupo=grupo_trabalho, assunto="Nova conta de Grupo de Trabalho")
                    UpdateGrupoAcesso(client_feeipa=client_feeipa, history_core=history_core).update_acesso(grupo_trabalho)
                    UpdateColaboradorGrupo(client_feeipa=client_feeipa, history_core=history_core).update_user(grupo_trabalho)
            else:
                messages.add_message(self.request, messages.ERROR, "O grupo já existe!")
        else:
            messages.add_message(self.request, messages.ERROR, "Confira o Cadastro, existe informação faltando ou não salva! ")
        return reverse_lazy("admin:core_grupotrabalho_change", kwargs={"object_id": grupo_trabalho.id})


class AtualizarContaGrupoTrabalhoView(LoginRequiredMixin, PermissionRequiredMixin, RedirectView):
    permission_required = "core.change_grupotrabalho"

    def get_redirect_url(self, *args, **kwargs):
        grupo_trabalho = get_object_or_404(GrupoTrabalho, id=kwargs["pk"])
        client_feeipa = FreeIPA(self.request)
        history_core = HistoryCore(self.request)
        history_core.update_grupo_acesso(grupo=grupo_trabalho, assunto="Atualização da conta de Grupo de Trabalho")
        UpdateGrupoAcesso(client_feeipa=client_feeipa, history_core=history_core).update_acesso(grupo_trabalho)
        UpdateColaboradorGrupo(client_feeipa=client_feeipa, history_core=history_core).update_user(grupo_trabalho)
        messages.add_message(self.request, messages.SUCCESS, "Conta de Grupo de Trabalho Atualizada")
        return reverse_lazy("admin:core_grupotrabalho_change", kwargs={"object_id": grupo_trabalho.id})


class EstruturaGruposView(ViewContextMixin, TemplateView):
    template_name = "core/estrutura_grupos.html"
    title = "Estrutura de Grupos"

    def get_context_data(self, **kwargs):
        grupos_trabalho = GrupoTrabalho.objects.filter(data_criado__isnull=False)
        context = super(EstruturaGruposView, self).get_context_data(**kwargs)
        context["grupos"] = grupos_trabalho
        return context


class CoreStatusView(TemplateView):
    template_name = "core/status.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["colaborador"] = Colaborador.objects.values("is_active").filter(is_active=1).count()
        context["grupo"] = GrupoTrabalho.objects.values("grupo").filter(data_criado__isnull=True).count()
        context["servidor"] = Servidor.objects.values("nome").filter(status="Ativo").count()
        return context
