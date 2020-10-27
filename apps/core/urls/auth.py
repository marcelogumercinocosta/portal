from django.contrib.auth.decorators import login_required
from django.urls import path
from apps.core.views import AtualizarAssinaturaView, AtualizarContaGrupoTrabalhoView, ConfirmarAssinaturaView, EstruturaGruposView, CriarContaGrupoTrabalhoView

app_name = "core"

urlpatterns = [
    path("grupotrabalho/<int:pk>/assinatura/", login_required(AtualizarAssinaturaView.as_view()), name="atualizar_assinatura"),
    path("grupotrabalho/<int:pk>/confirmarassinatura/", login_required(ConfirmarAssinaturaView.as_view()), name="confirmar_assinatura"),
    path("grupotrabalho/<int:pk>/criarconta/", login_required(CriarContaGrupoTrabalhoView.as_view()), name="criar_conta_grupo"),
    path("grupotrabalho/<int:pk>/atualizarconta/", login_required(AtualizarContaGrupoTrabalhoView.as_view()), name="atualizar_conta_grupo"),
]
