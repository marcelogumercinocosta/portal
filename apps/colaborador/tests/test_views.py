import pytest
import datetime
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth.tokens import default_token_generator

from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.test import RequestFactory
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from mixer.backend.django import mixer

from apps.colaborador.models import Colaborador, Vinculo
from apps.colaborador.views import (ColaboradorStatusView, InicioView, ColaboradorHistoricoView, 
                                    NovoView, PasswordResetConfirmView,
                                    SecretariaRevisarView, SecretariaNegarView,
                                    SecretariaView, SolicitacaoView,
                                    SuporteCriarContaView, SuporteView,
                                    TermoCompromissoView, SolicitacaoEnviarView,
                                    ResponsavelView, ResponsavelNegarView,
                                    ResponsavelAprovarView, ChefiaAprovarView, ColaboradorContaView)
from apps.core.models import Divisao, GrupoAcesso, GrupoTrabalho, ColaboradorGrupoAcesso, Predio
from apps.core.utils.freeipa import FreeIPA
from apps.core.tests.base import *

pytestmark = pytest.mark.django_db


@pytest.fixture
@pytest.mark.django_db
def colaborador_data() -> Colaborador:
    grupo_portal = mixer.blend(GrupoPortal, name="Responsavel")
    responsavel_colaborador = Permission.objects.get(codename="responsavel_colaborador")
    grupo_portal.permissions.add(responsavel_colaborador)
    grupo_portal.save()


    responsavel = mixer.blend(Colaborador)
    responsavel.groups.add(grupo_portal)
    vinculo = mixer.blend(Vinculo, vinculo="servidor")
    divisao = mixer.blend(Divisao, email="divisao@divisao.com")
    predio = mixer.blend(Predio)
    colaborador = mixer.blend(Colaborador)
    data = {k: v for k, v in colaborador.__dict__.items() if v is not None}
    data.update(
        {
            "check_me_out1": True,
            "check_me_out2": True,
            "check_me_out3": True,
            "documento_tipo": "RG",
            "predio": predio.id,
            "vinculo": vinculo.id,
            "divisao": divisao.id,
            "responsavel": responsavel.id,
            "cpf": "111111111111",
            "email": "tal@test.com",
        }
    )
    return data


@pytest.fixture
@pytest.mark.django_db
def colaborador_solicitacao() -> Colaborador:
    colaborador0 = mixer.blend(Colaborador, username="teste.solicitacao", email="teste.solicitacao@inpe.br", uid="12")
    colaborador0.save()
    colaborador = mixer.blend(Colaborador, first_name="Colaborador", last_name="Fulano de tal", externo=False, email="teste.pytest1@inpe.br")
    colaborador.username = None
    colaborador.clean()
    colaborador.save()
    return colaborador


@pytest.fixture
@pytest.mark.django_db
def grupo_acesso() -> GrupoAcesso:
    grupo_trabalho = mixer.blend(GrupoTrabalho, grupo="Grupo dados", grupo_sistema="dados")
    grupo_trabalho.save()
    grupo_acesso = GrupoAcesso()
    grupo_acesso.make(tipo="Desenvolvimento", grupo_trabalho=grupo_trabalho)
    grupo_acesso.save()
    return grupo_acesso


def test_get_inicio():
    request = RequestFactory().get("/colaborador/inicio")
    response = InicioView.as_view()(request)
    assert response.status_code == 200


def test_get_inicio_novo_erro():
    with pytest.raises(Http404) as excinfo:
        request = RequestFactory().get("/colaborador/inicio/novo")
        NovoView.as_view()(request)
        assert "Page does not exist" in str(excinfo.value)


def test_get_inicio_novo_ok():
    request = RequestFactory().get("/colaborador/inicio/novo/?motivo=atualizar")
    response = NovoView.as_view()(request)
    assert response.status_code == 200

    request = RequestFactory().get("/colaborador/inicio/?motivo=novo")
    response = NovoView.as_view()(request)
    assert response.status_code == 200


def test_post_inicio_novo_ok(colaborador_data):
    request = RequestFactory().post("/colaborador/inicio/novo/?motivo=atualizar", data=colaborador_data)
    response = NovoView.as_view()(request)
    assert response.status_code == 302
    colaborador = Colaborador.objects.get(email="tal@test.com")
    assert colaborador.email == "tal@test.com"


def test_get_secretaria_error(colaborador):
    request = RequestFactory().get("/secretaria")
    request.user = colaborador
    with pytest.raises(PermissionDenied) as excinfo:
        SecretariaView.as_view()(request)
        assert "PermissionDenied" in str(excinfo.value)
    request.user = AnonymousUser()
    response = SecretariaView.as_view()(request)
    assert response.status_code == 302


def test_get_sercretaria_ok(secretaria):
    request = RequestFactory().get("/secretaria")
    request.user = secretaria
    response = SecretariaView.as_view()(request)
    assert response.status_code == 200

def test_post_secretaria_negado_ok(secretaria, colaborador_solicitacao):
    assert len(Colaborador.objects.filter(pk=colaborador_solicitacao.pk)) == 1
    request = RequestFactory().post("/secretaria/negar", data={"colaborador": colaborador_solicitacao.id, "motivo": "teste"})
    request = message_middleware(request)
    request.user = secretaria
    response = SecretariaNegarView.as_view()(request)
    assert response.status_code == 302
    assert len(Colaborador.objects.filter(pk=colaborador_solicitacao.id)) == 0


def test_get_secretaria_aprovado(secretaria, colaborador):
    request = RequestFactory().post(reverse("colaborador:secretaria_revisar", kwargs={"pk": colaborador.pk}))
    request = message_middleware(request)
    request.user = secretaria
    response = SecretariaRevisarView.as_view()(request, pk=colaborador.pk)
    assert response.status_code == 302


def test_get_chefia_link_errado_permissao_acesso(colaborador):
    uid = urlsafe_base64_encode(force_bytes(colaborador.pk))
    token_generator = default_token_generator.make_token(colaborador)
    request = RequestFactory().get(reverse("colaborador:chefia_aprovar", kwargs={"uidb64": uid, "token": token_generator}))
    request = message_middleware(request)
    request.user = colaborador
    with pytest.raises(PermissionDenied) as excinfo:
        ChefiaAprovarView.as_view()(request)
        assert "PermissionDenied" in str(excinfo.value)
    request.user = AnonymousUser()
    response = ChefiaAprovarView.as_view()(request)
    assert response.status_code == 302

def test_get_chefia_link_errado_uid(colaborador, chefia):
    colaborador.is_active = False
    colaborador.save()
    uid = urlsafe_base64_encode(force_bytes(colaborador.pk))
    request = RequestFactory().get(reverse("colaborador:chefia_aprovar", kwargs={"uidb64": uid, "token": "token"}))
    request = message_middleware(request)
    request.user = chefia
    response = ChefiaAprovarView.as_view()(request, uidb64=uid, token="token")
    assert response.status_code == 200
    colaborador_aprovado = Colaborador.objects.get(id=colaborador.id)
    assert colaborador_aprovado.is_active == False


def test_get_chefia_ok(colaborador, chefia):
    colaborador.is_active = False
    colaborador.save()
    uid = urlsafe_base64_encode(force_bytes(colaborador.pk))
    token_generator = default_token_generator.make_token(colaborador)
    request = RequestFactory().get(reverse("colaborador:chefia_aprovar", kwargs={"uidb64": uid, "token": token_generator}))
    request = message_middleware(request)
    request.user = chefia
    response = ChefiaAprovarView.as_view()(request, uidb64=uid, token=token_generator)
    assert response.status_code == 200
    colaborador_aprovado = Colaborador.objects.get(id=colaborador.id)
    assert colaborador_aprovado.is_staff == True

def test_get_suporte_erro_permissao_acesso(colaborador):
    request = RequestFactory().get("/suporte")
    request.user = colaborador
    with pytest.raises(PermissionDenied) as excinfo:
        SuporteView.as_view()(request)
        assert "PermissionDenied" in str(excinfo.value)
    request.user = AnonymousUser()
    response = SuporteView.as_view()(request)
    assert response.status_code == 302


def test_get_suporte_ok(colaborador_suporte):
    request = RequestFactory().get("/suporte")
    request.user = colaborador_suporte
    response = SuporteView.as_view()(request)
    assert response.status_code == 200


def test_post_suporte_criar_ok(colaborador_suporte, colaborador):
    colaborador.is_staff = False
    data = {"id": colaborador.id, "username": "teste.ok", "uid": "2222", "email": "teste.pytest3k@inpe.br"}
    request = RequestFactory().post(reverse("colaborador:suporte_criar_conta", kwargs={"pk": colaborador.pk}), data=data)
    request = message_middleware(request)
    request.user = colaborador_suporte
    response = SuporteCriarContaView.as_view()(request, pk=colaborador.pk, data=data)
    assert response.status_code == 302
    colaborador_aprovado = Colaborador.objects.get(id=colaborador.id)
    assert colaborador_aprovado.is_staff == True
    assert FreeIPA().user_find_count(displayname="teste.ok") == 1
    assert FreeIPA(request).user_delete(username="teste.ok") == True


def test_post_suporte_criar_erro_username(colaborador_suporte):
    data = {"id": colaborador_suporte.id, "username": "colaborador_suporte.tal", "uid": "11111", "email": "teste.teste@inpe.br"}
    request = RequestFactory().post(reverse("colaborador:suporte_criar_conta", kwargs={"pk": colaborador_suporte.pk}), data=data)
    request = message_middleware(request)
    request.user = colaborador_suporte
    SuporteCriarContaView.as_view()(request, pk=colaborador_suporte.pk, data=data)
    colaborador_reprovado = Colaborador.objects.get(id=colaborador_suporte.id)
    assert colaborador_reprovado.is_staff == False


def test_post_suporte_criar_erro_email(colaborador_suporte):
    data = {"id": colaborador_suporte.id, "username": "teste.teste", "uid": "11111", "email": "teste.teste@inpe.br"}
    request = RequestFactory().post(reverse("colaborador:suporte_criar_conta", kwargs={"pk": colaborador_suporte.pk}), data=data)
    request = message_middleware(request)
    request.user = colaborador_suporte
    SuporteCriarContaView.as_view()(request, pk=colaborador_suporte.pk, data=data)
    colaborador_reprovado = Colaborador.objects.get(id=colaborador_suporte.id)
    assert colaborador_reprovado.is_staff == False


def test_post_suporte_criar_erro_uid(colaborador_suporte):
    data = {"id": colaborador_suporte.id, "username": "teste2", "uid": "11", "email": "teste2@inpe.br"}
    request = RequestFactory().post(reverse("colaborador:suporte_criar_conta", kwargs={"pk": colaborador_suporte.pk}), data=data)
    request = message_middleware(request)
    request.user = colaborador_suporte
    SuporteCriarContaView.as_view()(request, pk=colaborador_suporte.pk, data=data)
    colaborador_reprovado = Colaborador.objects.get(id=colaborador_suporte.id)
    assert colaborador_reprovado.is_staff == False


def test_get_termo_ok(secretaria):
    colaborador = mixer.blend(Colaborador, first_name="Colaborador", last_name="Fulano de tal", email="teste.teste@inpe.br",)
    colaborador.save()
    request = RequestFactory().get(reverse("colaborador:secretaria_termo", kwargs={"pk": colaborador.pk}))
    request.user = secretaria
    response = TermoCompromissoView.as_view()(request, pk=colaborador.pk)
    assert response.status_code == 200

    colaborador = mixer.blend(Colaborador, first_name="Colaborador", last_name="Fulano de tal", email="teste.teste@com.br",)
    colaborador.save()
    request = RequestFactory().get(reverse("colaborador:secretaria_termo", kwargs={"pk": colaborador.pk}))
    request.user = secretaria

    response = TermoCompromissoView.as_view()(request, pk=colaborador.pk)
    assert response.status_code == 200


def test_password_reset_confirma_ok(colaborador_suporte):
    password = colaborador_suporte.password
    uid = urlsafe_base64_encode(force_bytes(colaborador_suporte.pk))
    token_generator = default_token_generator.make_token(colaborador_suporte)

    request = RequestFactory().get(reverse("password_reset_confirm", kwargs={"uidb64": uid, "token": token_generator}))
    request = message_middleware(request)
    assert FreeIPA(request).set_colaborador(colaborador_suporte, "tmp_password") == True

    response = PasswordResetConfirmView.as_view()(request, uidb64=uid, token=token_generator)
    colaborador_senha = Colaborador.objects.get(id=colaborador_suporte.id)
    assert response.status_code == 200
    assert password != colaborador_senha.password
    assert FreeIPA(request).user_delete(username=colaborador_suporte.username) == True


def test_password_reset_confirma_error(colaborador_suporte):
    password = colaborador_suporte.password
    uid = urlsafe_base64_encode(force_bytes(51))
    token_generator = default_token_generator.make_token(colaborador_suporte)
    request = RequestFactory().get(reverse("password_reset_confirm", kwargs={"uidb64": uid, "token": token_generator}))
    request = message_middleware(request)
    response = PasswordResetConfirmView.as_view()(request, uidb64=uid, token=token_generator)
    colaborador_senha = Colaborador.objects.get(id=colaborador_suporte.id)
    assert response.status_code == 200
    assert password == colaborador_senha.password


def test_get_solicitacao_ok(colaborador_solicitacao):
    grupo = mixer.blend(GrupoTrabalho, grupo="Grupo dados", grupo_sistema="dados")
    grupo.data_criado = datetime.date.today()
    grupo.save()
    request = RequestFactory().get(reverse("colaborador:conta_grupoacesso_solicitacao"))
    request.user = colaborador_solicitacao
    response = SolicitacaoView.as_view()(request)
    assert response.status_code == 200
    assert len(response.context_data['grupos_novos']) == 1


def test_get_solicitacao_enviar_ok(colaborador_solicitacao, grupo_acesso):
    request = RequestFactory().get(reverse("colaborador:conta_grupoacesso_solicitacao_enviar", kwargs={"pk":grupo_acesso.id}))
    request = message_middleware(request)
    request.user = colaborador_solicitacao
    response = SolicitacaoEnviarView.as_view()(request, pk=grupo_acesso.id)
    assert response.status_code == 302
    assert ColaboradorGrupoAcesso.objects.filter(colaborador_id=colaborador_solicitacao.id).exists() == True


def test_get_responsavel_ok(responsavel_grupo, colaborador):
    grupo_acesso = GrupoAcesso.objects.all()[0]
    colaborador_grupo_acesso = mixer.blend(ColaboradorGrupoAcesso, colaborador=colaborador, grupo_acesso=grupo_acesso, aprovacao=0)
    colaborador_grupo_acesso.save()

    request = RequestFactory().get(reverse("colaborador:responsavel"))
    request.user = responsavel_grupo
    response = ResponsavelView.as_view()(request)
    assert response.status_code == 200
    assert len(response.context_data['solicitacoes']) == 1


def test_get_responsavel_aprovado(responsavel_grupo, grupo_trabalho, colaborador):
    grupo_acesso = GrupoAcesso.objects.all()[0]
    colaborador_grupo_acesso = mixer.blend(ColaboradorGrupoAcesso, colaborador=colaborador, grupo_acesso=grupo_acesso, aprovacao=0)
    colaborador_grupo_acesso.save()

    assert  colaborador_grupo_acesso.status() == "Aguardando Aprovação"
    grupo_acesso = GrupoAcesso.objects.filter(id=colaborador_grupo_acesso.grupo_acesso.pk)[0]
    grupo_trabalho = grupo_acesso.grupo_trabalho
    request = RequestFactory().post(reverse("colaborador:responsavel_aprovar", kwargs={"pk": colaborador_grupo_acesso.pk}))
    request = message_middleware(request)
    request.user = responsavel_grupo
    assert FreeIPA(request).set_colaborador(colaborador_grupo_acesso.colaborador, "tmp_password") == True
    assert FreeIPA(request).group_create(group=grupo_trabalho.grupo_sistema, gidnumber=grupo_trabalho.gid, description='Teste:test_get_responsavel_aprovado') == True
    assert FreeIPA(request).set_hbac_group(grupo_acesso=colaborador_grupo_acesso.grupo_acesso) == True

    response = ResponsavelAprovarView.as_view()(request, pk=colaborador_grupo_acesso.pk)
    assert response.status_code == 302
    
    colaborador_grupo_acesso_aprovado = ColaboradorGrupoAcesso.objects.all()[0]
    assert  colaborador_grupo_acesso_aprovado.status() == "Acesso Aprovado"

    hbacrule_show = FreeIPA().hbacrule_show(cn=colaborador_grupo_acesso.grupo_acesso.hbac_freeipa)
    assert  hbacrule_show['result']['memberuser_user'] == [colaborador_grupo_acesso.colaborador.username]
    assert FreeIPA(request).remove_hbac_group_rule(grupo_acesso=colaborador_grupo_acesso.grupo_acesso) == True
    assert FreeIPA(request).user_delete(username=colaborador_grupo_acesso.colaborador.username) == True
    assert FreeIPA(request).group_delete(grupo_trabalho.grupo_sistema) == True


def test_post_responsavel_negar_form_ok(responsavel_grupo,colaborador):
    grupo_acesso = GrupoAcesso.objects.all()[0]
    colaborador_grupo_acesso = mixer.blend(ColaboradorGrupoAcesso, colaborador=colaborador, grupo_acesso=grupo_acesso, aprovacao=0)
    colaborador_grupo_acesso.save()

    request = RequestFactory().post("/responsavel/negar", data={"colaborador_grupoacesso": colaborador_grupo_acesso.id, "motivo": "teste"})
    request = message_middleware(request)
    request.user = responsavel_grupo
    response = ResponsavelNegarView.as_view()(request)
    assert response.status_code == 302
    assert len(ColaboradorGrupoAcesso.objects.all()) == 0


def test_get_status_ok(secretaria):
    request = RequestFactory().get(reverse("colaborador:status"))
    request.user = secretaria
    response = ColaboradorStatusView.as_view()(request)
    assert response.status_code == 200


def test_colaborador_historico_view(responsavel_grupo):
    request = RequestFactory().get(reverse("colaborador:conta_historico"))
    request.user = responsavel_grupo
    response = ColaboradorHistoricoView.as_view()(request)
    assert response.status_code == 200


def test_colaborador_conta_view(colaborador):
    request = RequestFactory().get(reverse("colaborador:conta"))
    request.user = colaborador
    response = ColaboradorContaView.as_view()(request)
    assert response.status_code == 200