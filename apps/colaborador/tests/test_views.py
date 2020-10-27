import pytest
import datetime
from django.contrib.auth.models import AnonymousUser, Group, Permission, User
from django.contrib.auth.tokens import default_token_generator
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404
from django.test import RequestFactory
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from mixer.backend.django import mixer

from apps.colaborador.forms import ColaboradorForm, SuporteForm
from apps.colaborador.models import Colaborador, Vinculo
from apps.colaborador.views import (ColaboradorStatusView, InicioView, ColaboradorHistoricoView, 
                                    NovoView, PasswordResetConfirmView,
                                    SecretariaAprovarView, SecretariaNegarView,
                                    SecretariaView, SolicitacaoView,
                                    SuporteCriarContaView, SuporteView,
                                    TermoCompromissoView, SolicitacaoEnviarView,
                                    ResponsavelView, ResponsavelNegarView,
                                    ResponsavelAprovarView, ChefiaAprovarView)
from apps.core.models import Divisao, GrupoAcesso, GrupoTrabalho, ResponsavelGrupoTrabalho, ColaboradorGrupoAcesso, Predio
from apps.core.utils.freeipa import FreeIPA

pytestmark = pytest.mark.django_db


def message_middleware(request):
    """Annotate a request object with a session"""
    middleware = SessionMiddleware()
    middleware.process_request(request)
    request.session.save()
    """Annotate a request object with a messages"""
    middleware = MessageMiddleware()
    middleware.process_request(request)
    request.session.save()
    return request


@pytest.mark.django_db
@pytest.fixture(autouse=True)
def set_permission() -> None:
    group = mixer.blend(Group, name="Responsavel")
    responsavel_colaborador = Permission.objects.get(codename="responsavel_colaborador")
    group.permissions.add(responsavel_colaborador)
    group.save()

    group = mixer.blend(Group, name="Secretaria")
    secretaria_colaborador = Permission.objects.get(codename="secretaria_colaborador")
    group.permissions.add(secretaria_colaborador)
    group.save()

    group = mixer.blend(Group, name="Suporte")
    secretaria_colaborador = Permission.objects.get(codename="suporte_colaborador")
    group.permissions.add(secretaria_colaborador)
    group.save()

    group = mixer.blend(Group, name="Chefia")
    chefia_colaborador = Permission.objects.get(codename="chefia_colaborador")
    group.permissions.add(chefia_colaborador)
    group.save()

    group = mixer.blend(Group, name="Colaborador")
    group.save()


@pytest.fixture
@pytest.mark.django_db
def colaborador_data() -> Colaborador:
    responsavel = mixer.blend(Colaborador)
    responsavel.groups.add(Group.objects.get(name="Responsavel"))
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
            "estado_civil": "Solteiro",
            "sexo": "Masculino",
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
def colaborador_suporte() -> Colaborador:
    grupo_portal = Group.objects.get(name="Suporte")
    colaborador0 = mixer.blend(Colaborador, username="teste.teste", email="teste.teste@inpe.br", uid="11")
    responsavel = mixer.blend(Colaborador)
    responsavel.groups.add(grupo_portal)
    responsavel.save()
    colaborador = mixer.blend(Colaborador, first_name="Colaborador", last_name="Fulano de tal", externo=False, responsavel=responsavel, email="teste.pytest1@inpe.br", uid=12)
    colaborador.data_fim = datetime.date.today() + datetime.timedelta(days=10)
    colaborador.username = None
    colaborador.clean()
    colaborador.save()
    return colaborador


@pytest.fixture
@pytest.mark.django_db
def reponsavel_grupo() -> Colaborador:
    grupo_trabalho = mixer.blend(GrupoTrabalho, grupo="Grupo de teste", grupo_sistema="teste", gid=10)
    grupo_trabalho.save_confirm()
    grupo_acesso = GrupoAcesso(tipo="Desenvolvimento", grupo_trabalho=grupo_trabalho)
    grupo_acesso.save()
    responsavel = mixer.blend(Colaborador, first_name="Responsavel", last_name="Fulano de tal", externo=False, email="teste.reponsavel@inpe.br")
    responsavel.username = None
    responsavel.clean()
    responsavel.groups.add(Group.objects.get(name="Responsavel"))
    responsavel.save()
    responsavel_grupo_trabalho = mixer.blend(ResponsavelGrupoTrabalho, grupo=grupo_trabalho, responsavel=responsavel)
    colaborador0 = mixer.blend(Colaborador, username="teste.teste", email="teste.teste@inpe.br", uid="11", responsavel=responsavel)
    colaborador_grupo_acesso = ColaboradorGrupoAcesso(colaborador=colaborador0, grupo_acesso=grupo_acesso)
    colaborador_grupo_acesso.save()
    return responsavel


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
    grupo_acesso = GrupoAcesso(tipo="Desenvolvimento", grupo_trabalho=grupo_trabalho)
    grupo_acesso.save()
    return grupo_acesso


@pytest.fixture
@pytest.mark.django_db
def secretaria() -> Colaborador:
    secretaria = mixer.blend(Colaborador)
    secretaria.groups.add(Group.objects.get(name="Secretaria"))
    secretaria.save()
    return secretaria


@pytest.fixture
@pytest.mark.django_db
def colaborador() -> Colaborador:
    colaborador = mixer.blend(Colaborador, first_name="Colaborador", last_name="Fulano de tal")
    colaborador.groups.add(Group.objects.get(name="Colaborador"))
    colaborador.save()
    return colaborador

@pytest.fixture
@pytest.mark.django_db
def chefia() -> Colaborador:
    chefia = mixer.blend(Colaborador, first_name="Chefe1", last_name="Divisao", email="chefe1.divisao@inpe.br")
    chefia.groups.add(Group.objects.get(name="Chefia"))
    chefia.save()
    return chefia

@pytest.fixture
@pytest.mark.django_db
def suporte() -> Colaborador:
    secretaria = mixer.blend(Colaborador)
    secretaria.groups.add(Group.objects.get(name="Suporte"))
    secretaria.save()
    return secretaria


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


def test_get_secretaria_error():
    request = RequestFactory().get("/secretaria")
    request.user = User(id=1)
    with pytest.raises(PermissionDenied) as excinfo:
        SecretariaView.as_view()(request)
        assert "PermissionDenied" in str(excinfo.value)
    request.user = AnonymousUser()
    response = SecretariaView.as_view()(request)
    assert response.status_code == 302


def test_get_sercretaria_ok(secretaria):
    request = RequestFactory().get("/secretaria")
    request.user = User(id=secretaria.id)
    response = SecretariaView.as_view()(request)
    assert response.status_code == 200

def test_post_secretaria_negar_form_ok(secretaria, colaborador):
    assert len(Colaborador.objects.filter(pk=colaborador.id)) == 1
    request = RequestFactory().post("/secretaria/negar", data={"colaborador": colaborador.id, "motivo": "teste"})
    request = message_middleware(request)
    request.user = User(id=secretaria.id)
    response = SecretariaNegarView.as_view()(request)
    assert response.status_code == 302
    assert len(Colaborador.objects.filter(pk=colaborador.id)) == 0


def test_get_secretaria_aprovado(secretaria, colaborador):
    request = RequestFactory().post(reverse("colaborador:secretaria_aprovar", kwargs={"pk": colaborador.pk}))
    request = message_middleware(request)
    request.user = User(id=secretaria.id)
    response = SecretariaAprovarView.as_view()(request, pk=colaborador.pk)
    assert response.status_code == 302


def test_get_chefia_error(colaborador):
    uid = urlsafe_base64_encode(force_bytes(colaborador.pk))
    token_generator = default_token_generator.make_token(colaborador)
    request = RequestFactory().get(reverse("colaborador:chefia_aprovar", kwargs={"uidb64": uid, "token": token_generator}))
    request = message_middleware(request)
    request.user = User(id=colaborador.id)
    with pytest.raises(PermissionDenied) as excinfo:
        ChefiaAprovarView.as_view()(request)
        assert "PermissionDenied" in str(excinfo.value)
    request.user = AnonymousUser()
    response = ChefiaAprovarView.as_view()(request)
    assert response.status_code == 302

def test_get_chefia_error_link(colaborador, chefia):
    uid = urlsafe_base64_encode(force_bytes(colaborador.pk))
    request = RequestFactory().get(reverse("colaborador:chefia_aprovar", kwargs={"uidb64": uid, "token": "token"}))
    request = message_middleware(request)
    request.user = User(id=chefia.id)
    response = ChefiaAprovarView.as_view()(request, uidb64=uid, token="token")
    assert response.status_code == 200
    colaborador_aprovado = Colaborador.objects.get(id=colaborador.id)
    assert colaborador_aprovado.is_active == False


def test_get_chefia_ok(colaborador, chefia):
    uid = urlsafe_base64_encode(force_bytes(colaborador.pk))
    token_generator = default_token_generator.make_token(colaborador)
    request = RequestFactory().get(reverse("colaborador:chefia_aprovar", kwargs={"uidb64": uid, "token": token_generator}))
    request = message_middleware(request)
    request.user = User(id=chefia.id)
    response = ChefiaAprovarView.as_view()(request, uidb64=uid, token=token_generator)
    assert response.status_code == 200
    colaborador_aprovado = Colaborador.objects.get(id=colaborador.id)
    assert colaborador_aprovado.is_active == True

def test_get_suporte_error():
    request = RequestFactory().get("/suporte")
    request.user = User(id=1)
    with pytest.raises(PermissionDenied) as excinfo:
        SuporteView.as_view()(request)
        assert "PermissionDenied" in str(excinfo.value)
    request.user = AnonymousUser()
    response = SuporteView.as_view()(request)
    assert response.status_code == 302


def test_get_suporte_ok(suporte):
    request = RequestFactory().get("/suporte")
    request.user = User(id=suporte.id)
    response = SuporteView.as_view()(request)
    assert response.status_code == 200


def test_post_suporte_criar_ok(suporte, colaborador_suporte):
    data = {"id": colaborador_suporte.id, "username": "teste.ok", "uid": "2222", "email": "teste.pytest3k@inpe.br"}
    request = RequestFactory().post(reverse("colaborador:suporte_criar_conta", kwargs={"pk": colaborador_suporte.pk}), data=data)
    request = message_middleware(request)
    request.user = User(id=suporte.id)
    response = SuporteCriarContaView.as_view()(request, pk=colaborador_suporte.pk, data=data)
    assert response.status_code == 302
    colaborador_aprovado = Colaborador.objects.get(id=colaborador_suporte.id)
    assert colaborador_aprovado.is_staff == True
    assert FreeIPA().user_find_count(displayname="teste.ok") == 1
    assert FreeIPA(request).user_delete(username="teste.ok") == True


def test_post_suporte_criar_error_username(suporte, colaborador_suporte):
    data = {"id": colaborador_suporte.id, "username": "colaborador_suporte.tal", "uid": "11111", "email": "teste.teste@inpe.br"}
    request = RequestFactory().post(reverse("colaborador:suporte_criar_conta", kwargs={"pk": colaborador_suporte.pk}), data=data)
    request = message_middleware(request)
    request.user = User(id=suporte.id)
    SuporteCriarContaView.as_view()(request, pk=colaborador_suporte.pk, data=data)
    colaborador_reprovado = Colaborador.objects.get(id=colaborador_suporte.id)
    assert colaborador_reprovado.is_staff == False


def test_post_suporte_criar_error_email(suporte, colaborador_suporte):
    data = {"id": colaborador_suporte.id, "username": "teste.teste", "uid": "11111", "email": "teste.teste@inpe.br"}
    request = RequestFactory().post(reverse("colaborador:suporte_criar_conta", kwargs={"pk": colaborador_suporte.pk}), data=data)
    request = message_middleware(request)
    request.user = User(id=suporte.id)
    SuporteCriarContaView.as_view()(request, pk=colaborador_suporte.pk, data=data)
    colaborador_reprovado = Colaborador.objects.get(id=colaborador_suporte.id)
    assert colaborador_reprovado.is_staff == False


def test_post_suporte_criar_error_uid(suporte, colaborador_suporte):
    data = {"id": colaborador_suporte.id, "username": "teste2", "uid": "11", "email": "teste2@inpe.br"}
    request = RequestFactory().post(reverse("colaborador:suporte_criar_conta", kwargs={"pk": colaborador_suporte.pk}), data=data)
    request = message_middleware(request)
    request.user = User(id=suporte.id)
    SuporteCriarContaView.as_view()(request, pk=colaborador_suporte.pk, data=data)
    colaborador_reprovado = Colaborador.objects.get(id=colaborador_suporte.id)
    assert colaborador_reprovado.is_staff == False


def test_get_termo_ok(secretaria):
    colaborador = mixer.blend(Colaborador, first_name="Colaborador", last_name="Fulano de tal", email="teste.teste@inpe.br",)
    colaborador.save()
    request = RequestFactory().get(reverse("colaborador:secretaria_termo", kwargs={"pk": colaborador.pk}))
    request.user = User(id=secretaria.id)
    response = TermoCompromissoView.as_view()(request, pk=colaborador.pk)
    assert response.status_code == 200

    colaborador = mixer.blend(Colaborador, first_name="Colaborador", last_name="Fulano de tal", email="teste.teste@com.br",)
    colaborador.save()
    request = RequestFactory().get(reverse("colaborador:secretaria_termo", kwargs={"pk": colaborador.pk}))
    request.user = User(id=secretaria.id)

    response = TermoCompromissoView.as_view()(request, pk=colaborador.pk)
    assert response.status_code == 200


def test_password_reset_confirm_ok(colaborador_suporte):
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


def test_password_reset_confirm_user_error(colaborador_suporte):
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
    request.user = User(id=colaborador_solicitacao.id)
    response = SolicitacaoView.as_view()(request)
    assert response.status_code == 200
    assert len(response.context_data['grupos_novos']) == 1


def test_get_solicitacao_enviar_ok(colaborador_solicitacao, grupo_acesso):
    request = RequestFactory().get(reverse("colaborador:conta_grupoacesso_solicitacao_enviar", kwargs={"pk":grupo_acesso.id}))
    request = message_middleware(request)
    request.user = User(id=colaborador_solicitacao.id)
    response = SolicitacaoEnviarView.as_view()(request, pk=grupo_acesso.id)
    assert response.status_code == 302
    assert ColaboradorGrupoAcesso.objects.filter(colaborador_id=colaborador_solicitacao.id).exists() == True


def test_get_responsavel_ok(reponsavel_grupo):
    request = RequestFactory().get(reverse("colaborador:responsavel"))
    request.user = User(id=reponsavel_grupo.id)
    response = ResponsavelView.as_view()(request)
    assert response.status_code == 200
    assert len(response.context_data['solicitacoes']) == 1


def test_get_responsavel_aprovado(reponsavel_grupo):
    colaborador_grupo_acesso = ColaboradorGrupoAcesso.objects.all()[0]
    assert  colaborador_grupo_acesso.status() == "Aguardando Aprovação"
    grupo_acesso = GrupoAcesso.objects.filter(id=colaborador_grupo_acesso.grupo_acesso.pk)[0]
    grupo_trabalho = grupo_acesso.grupo_trabalho
    request = RequestFactory().post(reverse("colaborador:responsavel_aprovar", kwargs={"pk": colaborador_grupo_acesso.pk}))
    request = message_middleware(request)
    request.user = User(id=reponsavel_grupo.id)
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


def test_post_responsavel_negar_form_ok(reponsavel_grupo):
    colaborador_grupo_acesso = ColaboradorGrupoAcesso.objects.all()
    assert  len(colaborador_grupo_acesso) == 1
    request = RequestFactory().post("/responsavel/negar", data={"colaborador_grupoacesso": colaborador_grupo_acesso[0].id, "motivo": "teste"})
    request = message_middleware(request)
    request.user = User(id=reponsavel_grupo.id)
    response = ResponsavelNegarView.as_view()(request)
    assert response.status_code == 302
    assert len(ColaboradorGrupoAcesso.objects.all()) == 0


def test_get_status_ok(secretaria):
    request = RequestFactory().get(reverse("colaborador:status"))
    request.user = User(id=secretaria.id)
    response = ColaboradorStatusView.as_view()(request)
    assert response.status_code == 200


def test_colaborador_historico_view(reponsavel_grupo):
    request = RequestFactory().get(reverse("colaborador:conta_historico"))
    request.user = User(id=reponsavel_grupo.id)
    response = ColaboradorHistoricoView.as_view()(request)
    assert response.status_code == 200



