from django.contrib.auth.decorators import login_required
from django.urls import path

from apps.colaborador.views import (
    ResponsavelAprovarView,
    ResponsavelNegarView,
    ResponsavelView,
    SecretariaRevisarView,
    SecretariaNegarView,
    SecretariaView,
    SolicitacaoEnviarView,
    SolicitacaoView,
    SuporteCriarContaView,
    SuporteView,
    TermoCompromissoView,
    ColaboradorStatusView,
    ChefiaAprovarView,
    ColaboradorHistoricoView,
    ColaboradorContaView,
)

app_name = "colaborador"

urlpatterns = [
    
    path("chefia/<uidb64>/<token>", login_required(ChefiaAprovarView.as_view()), name="chefia_aprovar"),
    path("responsavel/", login_required(ResponsavelView.as_view()), name="responsavel"),
    path("responsavel/<int:pk>/aprovar", login_required(ResponsavelAprovarView.as_view()), name="responsavel_aprovar"),
    path("responsavel/negar/", login_required(ResponsavelNegarView.as_view()), name="responsavel_negar"),
    path("secretaria/", login_required(SecretariaView.as_view()), name="secretaria"),
    path("secretaria/negar", login_required(SecretariaNegarView.as_view()), name="secretaria_negar"),
    path("secretaria/<int:pk>/revisar/", login_required(SecretariaRevisarView.as_view()), name="secretaria_revisar"),
    path("secretaria/<int:pk>/termo/", login_required(TermoCompromissoView.as_view()), name="secretaria_termo"),
    path("suporte/", login_required(SuporteView.as_view()), name="suporte"),
    path("suporte/<int:pk>/criar", login_required(SuporteCriarContaView.as_view()), name="suporte_criar_conta"),
    path("grupoacesso/solicitacao", login_required(SolicitacaoView.as_view()), name="conta_grupoacesso_solicitacao"),
    path("grupoacesso/<int:pk>/solicitacao", login_required(SolicitacaoEnviarView.as_view()), name="conta_grupoacesso_solicitacao_enviar"),
    path("status", login_required(ColaboradorStatusView.as_view()), name="status"),
    path("history", login_required(ColaboradorHistoricoView.as_view()), name="conta_historico"),
    path("sua", login_required(ColaboradorContaView.as_view()), name="conta"),
]
