from io import BytesIO

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.models import LogEntry
from django.contrib.auth.forms import PasswordResetForm, urlsafe_base64_encode
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import PasswordContextMixin
from django.contrib.staticfiles import finders
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template.loader import get_template
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes
from django.views.decorators.csrf import csrf_protect
from django.views.generic import DetailView
from django.views.generic.base import RedirectView, TemplateView, View
from django.views.generic.edit import CreateView, FormView, UpdateView
from xhtml2pdf import pisa

from apps.colaborador.forms import  ColaboradorForm, ResponsavelNegarForm, SecretariaNegarForm, SuporteForm
from apps.colaborador.models import Colaborador
from apps.colaborador.utils import HistoryColaborador, gerar_password, get_user
from apps.core.models import ColaboradorGrupoAcesso, Divisao, GrupoAcesso, GrupoTrabalho
from apps.core.tasks import send_email_template_task
from apps.core.utils.freeipa import FreeIPA
from garb.views import ViewContextMixin


class InicioView(ViewContextMixin, TemplateView):
    template_name = "colaborador/inicio.html"
    title = "Novo Colaborador"


class NovoView(ViewContextMixin, CreateView):
    model = Colaborador
    form_class = ColaboradorForm
    template_name = "colaborador/form.html"
    title = "Novo Colaborador"
    motivo = None
    success_url = reverse_lazy("colaborador_open:sucesso")

    def get_initial(self):
        self.motivo = self.request.GET.get("motivo")
        if self.motivo is None:
            raise Http404("Page does not exist")

    def form_valid(self, form):
        colaborador = form.save_sendmail(self.request.scheme, self.request.get_host())
        HistoryColaborador(self.request).novo(colaborador)
        return super().form_valid(form)


class SucessoView(ViewContextMixin, TemplateView):
    template_name = "colaborador/sucesso.html"
    title = "Novo Colaborador"


class SecretariaView(ViewContextMixin, LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = "colaborador/secretaria.html"
    permission_required = "colaborador.secretaria_colaborador"
    title = "Secretaria"

    def get_context_data(self, **kwargs):
        context = super(SecretariaView, self).get_context_data(**kwargs)
        context["divisao"] = Divisao.objects.get(pk=self.request.user.divisao.pk)
        context["colaboradores"] = Colaborador.objects.filter(divisao_id=self.request.user.divisao.id, is_active=False, is_staff=False)
        context["form_negar"] = SecretariaNegarForm
        return context


class SecretariaNegarView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    form_class = SecretariaNegarForm
    template_name = "colaborador/secretaria.html"
    permission_required = "colaborador.secretaria_colaborador"
    success_url = reverse_lazy("colaborador:secretaria")

    def form_valid(self, form):
        colaborador = form.sendmail()
        colaborador.delete()
        messages.add_message(self.request, messages.SUCCESS, "Colaborador Negado com Sucesso")
        return super().form_valid(form)


class SecretariaRevisarView(LoginRequiredMixin, PermissionRequiredMixin, RedirectView):
    permission_required = "colaborador.secretaria_colaborador"
    token_generator = default_token_generator

    def get_redirect_url(self, *args, **kwargs):
        colaborador = get_object_or_404(Colaborador, id=kwargs["pk"])
        HistoryColaborador(self.request).secretaria(colaborador)
        pk = urlsafe_base64_encode(force_bytes(colaborador.pk))
        token = self.token_generator.make_token(colaborador)
        context_email = [["protocol", self.request.scheme], ["domain",self.request.get_host()], ["name", colaborador.full_name], ["uidb64", pk], ["token",token]]
        send_emails = colaborador.divisao.emails_to()
        send_email_template_task.delay((f"Aprovação para criação de conta"), "colaborador/email/secretaria_revisado.html", send_emails, context_email)
        messages.add_message(self.request, messages.SUCCESS, "Foi enviado email para o(s) Chefe(s) ativo(s) da Divisão, solicitando aprovação do colaborador")
        return reverse_lazy("colaborador:secretaria")


class ChefiaAprovarView(ViewContextMixin, LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = "colaborador/chefia.html"
    permission_required = "colaborador.chefia_colaborador"
    title = "Aprovação do Colaborador"
    token_generator = default_token_generator

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        colaborador = get_user(kwargs["uidb64"])
        token = kwargs["token"]
        if not self.token_generator.check_token(colaborador, token) or colaborador.is_active:
            context["validlink"] = False
        else:
            colaborador.chefia_aprovar()
            context["validlink"] = True
            context["colaborador"] = colaborador
            HistoryColaborador(self.request).chefia(colaborador)
            send_email_template_task.delay((f"Agora é com o suporte"), "colaborador/email/chefia_aprovado.html", [colaborador.email], [["name", colaborador.full_name]])
            if not "@inpe.br" in colaborador.email:
                send_email_template_task.delay((f"Novo Colaborador"), "colaborador/email/suporte_username.html", [settings.EMAIL_SUPORTE], [["name", colaborador.full_name],["username", colaborador.username]])
            messages.add_message(self.request, messages.SUCCESS, "Colaborador Aprovado com Sucesso")
        return context


class SuporteView(ViewContextMixin, LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = "colaborador/suporte.html"
    permission_required = "colaborador.suporte_colaborador"
    title = "Suporte"

    def get_context_data(self, **kwargs):
        context = super(SuporteView, self).get_context_data(**kwargs)
        context["colaboradores"] = Colaborador.objects.filter(is_active=True, is_staff=False)
        context["form_suporte"] = SuporteForm
        return context


class SuporteCriarContaView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Colaborador
    form_class = SuporteForm
    template_name = "colaborador/suporte.html"
    permission_required = "colaborador.suporte_colaborador"
    success_url = reverse_lazy("colaborador:suporte")

    def get_form_kwargs(self):
        form = super().get_form_kwargs()
        form["request"] = self.request  # the trick!
        return form

    def form_valid(self, form):
        tmp_password = str(gerar_password())
        colaborador = form.save(commit=False)
        if FreeIPA(self.request).set_colaborador(colaborador, tmp_password):
            colaborador = form.save_sendmail(tmp_password)
            colaborador.suporte_criar()
        HistoryColaborador(self.request).suporte(colaborador)
        return super(SuporteCriarContaView, self).form_valid(form)

    def form_invalid(self, form):
        return HttpResponseRedirect(reverse_lazy("colaborador:suporte"))


class TermoCompromissoView(ViewContextMixin, LoginRequiredMixin, PermissionRequiredMixin, View):
    template_name = "colaborador/pdf/termo.html"
    permission_required = "colaborador.secretaria_colaborador"
    title = "Termo de Compromisso"

    def get(self, request, *args, **kwargs):
        colaborador = get_object_or_404(Colaborador, id=kwargs["pk"])
        if "@inpe.br" in colaborador.email:
            motivo_detalhe = "Cadastro para atualização conta"
            motivo = "atualizacao"
        else:
            motivo_detalhe = "Novo email / Conta Acesso aos Recursos"
            motivo = "admissao"
        context = {"title": "Termo de Compromisso de " + colaborador.full_name, "logo": finders.find("image/logo.png"), "motivo_detalhe": motivo_detalhe, "motivo": motivo, "colaborador": colaborador}
        result = BytesIO()
        template = get_template(self.template_name)
        html = template.render(context)
        pisa.pisaDocument(BytesIO(html.encode("utf8")), result)
        return HttpResponse(result.getvalue(), content_type="application/pdf")


class PasswordResetConfirmView(ViewContextMixin, TemplateView):
    template_name = "colaborador/novasenha.html"
    title = "Redefinição de senha realizada com êxito"
    token_generator = default_token_generator

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        token = kwargs["token"]
        colaborador = get_user(kwargs["uidb64"])
        if not self.token_generator.check_token(colaborador, token):
            context["validlink"] = False
            context["title"] = "Redefinição de senha sem êxito"
        else:
            tmp_password = str(gerar_password())
            if FreeIPA(self.request).set_novasenha(colaborador, tmp_password):
                colaborador.set_password(tmp_password)
                colaborador.save()
            context.update({"validlink": True, "password": tmp_password})
        return context

class SolicitacaoView(ViewContextMixin, LoginRequiredMixin, TemplateView):
    template_name = "colaborador/solicitacao.html"
    title = "SOLICITAÇÃO DE ACESSO"

    def get_context_data(self, **kwargs):
        colaborador_id = self.request.user.id
        grupos_trabalho = GrupoTrabalho.objects.filter(data_criado__isnull=False)
        colaborador_grupos_acesso_solicitados = [colaborador_grupo_acesso.grupo_acesso.id for colaborador_grupo_acesso in ColaboradorGrupoAcesso.objects.filter(colaborador__id=colaborador_id, aprovacao=0)]
        colaborador_grupos_acesso_aprovados = [colaborador_grupo_acesso.grupo_acesso.id for colaborador_grupo_acesso in ColaboradorGrupoAcesso.objects.filter(colaborador__id=colaborador_id, aprovacao=1)]
        context = super(SolicitacaoView, self).get_context_data(**kwargs)
        context["grupos_novos"] = grupos_trabalho
        context["grupos_solicitados"] = colaborador_grupos_acesso_solicitados
        context["grupos_aprovados"] = colaborador_grupos_acesso_aprovados
        return context


class SolicitacaoEnviarView(LoginRequiredMixin, RedirectView):
    def get_redirect_url(self, *args, **kwargs):
        grupo_acesso = get_object_or_404(GrupoAcesso, id=kwargs["pk"])
        send_emails = [responsavel.email for responsavel in grupo_acesso.grupo_trabalho.responsavel.all()]
        colaborador = get_object_or_404(Colaborador, id=self.request.user.id)
        context_email = [
            ["sexo", colaborador.sexo],
            ["name", colaborador.full_name],
            ["divisao", colaborador.divisao.divisao],
            ["scheme", self.request.scheme],
            ["host", self.request.get_host()],
            ["grupo", grupo_acesso.grupo_acesso],
            ["divisao", colaborador.divisao.divisao],
        ]
        send_email_template_task.delay((f"Solicitação de acesso aos recursos do Grupo de Trabalho"), "colaborador/email/colaborador_solicitacao.html", send_emails, context_email)
        HistoryColaborador(self.request).solicitacao(colaborador, grupo_acesso)
        ColaboradorGrupoAcesso.objects.create(colaborador=colaborador, grupo_acesso=grupo_acesso)
        messages.add_message(self.request, messages.SUCCESS, "Solicitação Enviada")
        return reverse_lazy("colaborador:conta_grupoacesso_solicitacao")


class ResponsavelView(ViewContextMixin, LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = "colaborador/responsavel.html"
    permission_required = "colaborador.responsavel_colaborador"
    title = "Responsável"

    def get_context_data(self, **kwargs):
        responsavel = self.request.user
        responsavel_grupos_acesso = [GrupoAcesso.id for GrupoAcesso in GrupoAcesso.objects.filter(grupo_trabalho__responsavelgrupotrabalho__responsavel_id=responsavel.id, grupo_trabalho__confirmacao=1)]
        colaborador_grupo_acesso = ColaboradorGrupoAcesso.objects.filter(grupo_acesso_id__in=responsavel_grupos_acesso, aprovacao=0).order_by("colaborador__name")
        context = super(ResponsavelView, self).get_context_data(**kwargs)
        context["solicitacoes"] = colaborador_grupo_acesso
        context["form_negar"] = ResponsavelNegarForm
        return context


class ResponsavelAprovarView(LoginRequiredMixin, PermissionRequiredMixin, RedirectView):
    permission_required = "colaborador.responsavel_colaborador"

    def get_redirect_url(self, *args, **kwargs):
        colaborador_grupo_acesso = get_object_or_404(ColaboradorGrupoAcesso, id=kwargs["pk"])
        colaborador = colaborador_grupo_acesso.colaborador
        grupo_acesso = colaborador_grupo_acesso.grupo_acesso
        grupo_trabalho_acesso = get_object_or_404(GrupoAcesso, id=grupo_acesso.id)
        if FreeIPA(self.request).add_user_group_hhac(colaborador.username, grupo_acesso.hbac_freeipa, grupo_trabalho_acesso.grupo_trabalho.grupo_sistema):
            HistoryColaborador(self.request).responsavel(colaborador_grupo_acesso, "Aprovado")
            messages.add_message(self.request, messages.SUCCESS, "Colaborador Aprovado com Sucesso")
            context_email = [["name", colaborador.full_name], ["grupo", grupo_acesso.grupo_acesso]]
            send_email_template_task.delay(f"Acesso Aprovado com Sucesso:{grupo_acesso.grupo_acesso}", "colaborador/email/responsavel_aprovado.html", [colaborador.email], context_email)
            colaborador_grupo_acesso.aprovacao = 1
            colaborador_grupo_acesso.save()
        return reverse_lazy("colaborador:responsavel")


class ResponsavelNegarView(LoginRequiredMixin, PermissionRequiredMixin, FormView):
    form_class = ResponsavelNegarForm
    template_name = "colaborador/responsavel.html"
    permission_required = "colaborador.responsavel_colaborador"
    success_url = reverse_lazy("colaborador:responsavel")

    def form_valid(self, form):
        colaborador_grupoacesso = form.sendmail()
        colaborador_grupoacesso.delete()
        HistoryColaborador(self.request).responsavel(colaborador_grupoacesso, "Reprovado")
        messages.add_message(self.request, messages.SUCCESS, "Colaborador Negado com Sucesso")
        return super().form_valid(form)


class ColaboradorStatusView(LoginRequiredMixin, TemplateView):
    template_name = "colaborador/status.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["colaborador_ativo"] = Colaborador.objects.values("is_active").filter(is_active=1).count()
        context["colaborador_aprovacao"] = Colaborador.objects.values("is_active").filter(is_active=0, password="").count()
        context["colaborador_desativado"] = Colaborador.objects.values("is_active").filter(is_active=0, is_staff=0).exclude(password="").count()
        return context


class ColaboradorHistoricoView(LoginRequiredMixin, TemplateView):
    template_name = "colaborador/admin/object_history_conta.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["action_list"] = LogEntry.objects.filter(content_type__model='Colaborador', object_id=self.request.user.id).exclude(change_message="No fields changed.").order_by('-action_time')
        return context


class ColaboradorContaView(ViewContextMixin, LoginRequiredMixin, DetailView ):
    model = Colaborador
    template_name = "colaborador/conta.html"
    title = "Sua Conta"

    def get_object(self):
        return get_object_or_404(Colaborador, pk=self.request.user.id)