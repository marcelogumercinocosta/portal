import pytest
from django.contrib.auth.models import AnonymousUser, Group, Permission, User
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import Http404
from django.test import RequestFactory
from django.urls import reverse
from mixer.backend.django import mixer
from apps.colaborador.models import Colaborador, Vinculo
from apps.core.models import Divisao, GrupoAcesso, GrupoTrabalho, ResponsavelGrupoTrabalho, ColaboradorGrupoAcesso
from apps.core.views import AtualizarAssinaturaView, ConfirmarAssinaturaView, EstruturaGruposView, CriarContaGrupoTrabalhoView, AtualizarContaGrupoTrabalhoView, CoreStatusView
from apps.core.utils.freeipa import FreeIPA 
import datetime
pytestmark = pytest.mark.django_db


def message_middleware(req):
    """Annotate a request object with a session"""
    middleware = SessionMiddleware()
    middleware.process_request(req)
    req.session.save()
    """Annotate a request object with a messages"""
    middleware = MessageMiddleware()
    middleware.process_request(req)
    req.session.save()
    return req

@pytest.mark.django_db
@pytest.fixture(autouse=True)
def set_permission() -> None:
    group = mixer.blend(Group, name="Responsavel")
    responsavel_colaborador = Permission.objects.get(codename="responsavel_colaborador")
    group.permissions.add(responsavel_colaborador)
    group.save()


@pytest.fixture
@pytest.mark.django_db
def superuser() -> Colaborador:
    group = mixer.blend(Group, name="Suporte")
    group.permissions.add(Permission.objects.get(codename="suporte_colaborador"))
    group.permissions.add(Permission.objects.get(codename="change_grupotrabalho"))
    group.save()

    superuser = mixer.blend(Colaborador, email="teste.super_user@inpe.br")
    superuser.is_staff = True
    superuser.is_active = True
    superuser.is_superuser = True
    superuser.username = None
    superuser.clean()
    superuser.groups.add(group)
    superuser.save()
    return superuser


@pytest.fixture
@pytest.mark.django_db
def grupo_trabalho() -> GrupoTrabalho:
    grupo_trabalho = mixer.blend(GrupoTrabalho, grupo="Grupo teste", grupo_sistema="teste", data_criado=None)
    grupo_trabalho.save()
    return grupo_trabalho


@pytest.fixture
@pytest.mark.django_db
def responsavel() -> Colaborador:
    responsavel = mixer.blend(Colaborador, first_name="Responsavel", last_name="Fulano de tal", externo=False, email="teste.reponsavel@inpe.br", uid=787)
    responsavel.username = None
    responsavel.clean()
    responsavel.groups.add(Group.objects.get(name="Responsavel"))
    responsavel.save()
    return responsavel


def test_assinatura_error(grupo_trabalho, superuser):
    request = RequestFactory().get(reverse("core:atualizar_assinatura", kwargs={"pk": grupo_trabalho.pk}))
    request = message_middleware(request)
    request.user = User(id=superuser.id)
    response = AtualizarAssinaturaView.as_view()(request, pk=grupo_trabalho.pk)
    assert response.status_code == 200
    assert response.content.decode(('latin-1')) == "Confirme as informações do Cadastro e/ou Responsáveis!"


def test_assinatura_ok(grupo_trabalho, superuser, responsavel):
    responsavel_grupo_trabalho = mixer.blend(ResponsavelGrupoTrabalho, grupo=grupo_trabalho, responsavel=responsavel)
    responsavel_grupo_trabalho.save()
    request = RequestFactory().get(reverse("core:atualizar_assinatura", kwargs={"pk": grupo_trabalho.pk}))
    request = message_middleware(request)
    request.user = User(id=superuser.id)
    response = AtualizarAssinaturaView.as_view()(request, pk=grupo_trabalho.pk)
    assert response.status_code == 200


def test_assinatura_confirmar_error(grupo_trabalho, superuser):
    request = RequestFactory().get(reverse("core:confirmar_assinatura", kwargs={"pk": grupo_trabalho.pk}))
    request = message_middleware(request)
    request.user = User(id=superuser.id)
    response = ConfirmarAssinaturaView.as_view()(request, pk=grupo_trabalho.pk)
    assert response.status_code == 302
    grupo_trabalho_confirmado = GrupoTrabalho.objects.get(pk=grupo_trabalho.pk)
    assert grupo_trabalho_confirmado.confirmacao == False


def test_assinatura_confirmar_ok(grupo_trabalho, superuser, responsavel):
    responsavel_grupo_trabalho = mixer.blend(ResponsavelGrupoTrabalho, grupo=grupo_trabalho, responsavel=responsavel)
    responsavel_grupo_trabalho.save()
    request = RequestFactory().get(reverse("core:confirmar_assinatura", kwargs={"pk": grupo_trabalho.pk}))
    request = message_middleware(request)
    request.user = User(id=superuser.id)
    response = ConfirmarAssinaturaView.as_view()(request, pk=grupo_trabalho.pk)
    assert response.status_code == 302
    grupo_trabalho_confirmado = GrupoTrabalho.objects.get(pk=grupo_trabalho.pk)
    assert grupo_trabalho_confirmado.confirmacao == True


def test_criar_conta_grupo_ok(grupo_trabalho, superuser, responsavel):
    responsavel_grupo_trabalho = mixer.blend(ResponsavelGrupoTrabalho, grupo=grupo_trabalho, responsavel=responsavel)
    grupo_trabalho.gid = 9000
    grupo_trabalho.desenvolvimento = True
    grupo_trabalho.operacional = True
    grupo_trabalho.documento = True
    grupo_trabalho.pesquisa = True
    freeipa = FreeIPA() 
    assert freeipa.set_colaborador(responsavel,'tmppassword') == 1
    grupo_trabalho.save_confirm()
    request = RequestFactory().get(reverse("core:criar_conta_grupo", kwargs={"pk": grupo_trabalho.pk}))
    request = message_middleware(request)
    request.user = User(id=superuser.id)
    response = CriarContaGrupoTrabalhoView.as_view()(request, pk=grupo_trabalho.pk)
    assert response.status_code == 302

    grupo_trabalho_confirmado = GrupoTrabalho.objects.get(pk=grupo_trabalho.pk)
    assert ColaboradorGrupoAcesso.objects.filter(colaborador_id=responsavel.id).exists() == True
    assert grupo_trabalho_confirmado.data_criado == datetime.date.today()
    assert freeipa.group_find_count(cn=grupo_trabalho_confirmado.grupo_sistema) == 1
    assert freeipa.sudorule_find_count(cn=grupo_trabalho_confirmado.get_sudo()) == 1
    assert freeipa.user_find_count(displayname=grupo_trabalho_confirmado.grupo_sistema) == 1
    grupos_acesso = GrupoAcesso.objects.filter(grupo_trabalho__id=grupo_trabalho_confirmado.pk)
    assert len(grupos_acesso) == 4
    for grupoacesso  in grupos_acesso: 
        assert freeipa.hbacrule_find_count(cn=grupoacesso.hbac_freeipa) == 1
    for grupoacesso  in grupos_acesso: 
        assert freeipa.hbacrule_delete(grupoacesso.hbac_freeipa)
        assert freeipa.hbacrule_find_count(cn=grupoacesso.hbac_freeipa) == 0
    assert freeipa.remove_grupo(grupo_trabalho_confirmado) == True
    assert freeipa.user_delete(responsavel.username)


def test_criar_conta_grupo_erro(grupo_trabalho, superuser, responsavel):
    request = RequestFactory().get(reverse("core:criar_conta_grupo", kwargs={"pk": grupo_trabalho.pk}))
    request = message_middleware(request)
    request.user = User(id=superuser.id)
    response = CriarContaGrupoTrabalhoView.as_view()(request, pk=grupo_trabalho.pk)
    assert response.status_code == 302

    grupo_trabalho.gid = 9000
    grupo_trabalho.save_confirm()
    assert response.status_code == 302

    responsavel_grupo_trabalho = mixer.blend(ResponsavelGrupoTrabalho, grupo=grupo_trabalho, responsavel=responsavel)
    responsavel_grupo_trabalho.save()
    grupo_trabalho.save()
    response = CriarContaGrupoTrabalhoView.as_view()(request, pk=grupo_trabalho.pk)
    assert response.status_code == 302

def test_criar_conta_grupo_erro_freeipa(grupo_trabalho, superuser, responsavel):
    responsavel_grupo_trabalho = mixer.blend(ResponsavelGrupoTrabalho, grupo=grupo_trabalho, responsavel=responsavel)
    responsavel_grupo_trabalho.save()
    grupo_trabalho.gid = 9000
    grupo_trabalho.save_confirm()
    request = RequestFactory().get(reverse("core:criar_conta_grupo", kwargs={"pk": grupo_trabalho.pk}))
    request = message_middleware(request)
    request.user = User(id=superuser.id)
    assert FreeIPA(request).group_create(grupo_trabalho.grupo_sistema, grupo_trabalho.gid, description="TESTE ERRO CREATE GRUPO") == True
    response = CriarContaGrupoTrabalhoView.as_view()(request, pk=grupo_trabalho.pk)
    assert response.status_code == 302
    grupo_trabalho_confirmado = GrupoTrabalho.objects.get(pk=grupo_trabalho.pk)
    assert grupo_trabalho_confirmado.data_criado == None
    assert FreeIPA(request).group_delete(grupo_trabalho.grupo_sistema) == True


def test_atualizar_conta_grupotrabalho(grupo_trabalho, superuser, responsavel):
    responsavel_grupo_trabalho = mixer.blend(ResponsavelGrupoTrabalho, grupo=grupo_trabalho, responsavel=responsavel)
    responsavel_grupo_trabalho.save()
    grupo_trabalho.gid = 9000
    grupo_trabalho.desenvolvimento = True
    grupo_trabalho.operacional = True
    grupo_trabalho.save_confirm()
    request = RequestFactory().get(reverse("core:criar_conta_grupo", kwargs={"pk": grupo_trabalho.pk}))
    request = message_middleware(request)
    request.user = User(id=superuser.id)
    response = CriarContaGrupoTrabalhoView.as_view()(request, pk=grupo_trabalho.pk)
    assert response.status_code == 302

    freeipa = FreeIPA(request) 
    assert freeipa.group_find_count(cn=grupo_trabalho.grupo_sistema) == 1
    assert freeipa.sudorule_find_count(cn=grupo_trabalho.get_sudo()) == 1
    assert freeipa.user_find_count(displayname=grupo_trabalho.grupo_sistema) == 1
    grupos_acesso = GrupoAcesso.objects.filter(grupo_trabalho__id=grupo_trabalho.pk)
    assert len(grupos_acesso) == 2
    for grupo_acesso  in grupos_acesso: 
        assert freeipa.hbacrule_find_count(cn=grupo_acesso.hbac_freeipa) == 1

    grupo_trabalho.documento = True
    grupo_trabalho.pesquisa = True
    grupo_trabalho.save_confirm()
    request = RequestFactory().get(reverse("core:atualizar_conta_grupo", kwargs={"pk": grupo_trabalho.pk}))
    request = message_middleware(request)
    request.user = User(id=superuser.id)
    response = AtualizarContaGrupoTrabalhoView.as_view()(request, pk=grupo_trabalho.pk)
    assert response.status_code == 302
    grupos_acesso = GrupoAcesso.objects.filter(grupo_trabalho__id=grupo_trabalho.pk)
    assert len(grupos_acesso) == 4
    for grupo_acesso  in grupos_acesso: 
        assert freeipa.hbacrule_find_count(cn=grupo_acesso.hbac_freeipa) == 1

    grupo_trabalho.desenvolvimento = False
    grupo_trabalho.operacional = False
    grupo_trabalho.pesquisa = False
    grupo_trabalho.documento = False
    grupo_trabalho.save_confirm()
    request = RequestFactory().get(reverse("core:atualizar_conta_grupo", kwargs={"pk": grupo_trabalho.pk}))
    request = message_middleware(request)
    request.user = User(id=superuser.id)
    response = AtualizarContaGrupoTrabalhoView.as_view()(request, pk=grupo_trabalho.pk)
    assert response.status_code == 302
    for grupo_acesso  in grupos_acesso: 
        assert freeipa.hbacrule_find_count(cn=grupo_acesso.hbac_freeipa) == 0
    grupos_acesso = GrupoAcesso.objects.filter(grupo_trabalho__id=grupo_trabalho.pk)
    assert len(grupos_acesso) == 0

    assert FreeIPA(request).remove_grupo(grupo_trabalho) == True


def test_get_estrutura_grupos():
    request = RequestFactory().get("/estrutura/grupos/")
    response = EstruturaGruposView.as_view()(request)
    assert response.status_code == 200


def test_get_status():
    request = RequestFactory().get(reverse("core_open:status"))
    response = CoreStatusView.as_view()(request)
    assert response.status_code == 200