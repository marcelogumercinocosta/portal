import pytest
import datetime
from django.contrib.admin.sites import AdminSite
from apps.colaborador.models import Colaborador, Vinculo
from apps.core.models import  ColaboradorGrupoAcesso, GrupoAcesso, GrupoPortal, GrupoTrabalho, ResponsavelGrupoTrabalho, Divisao, Predio
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.contrib.auth.models import  Permission
from mixer.backend.django import mixer

@pytest.fixture
def admin_site():
    return AdminSite()

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


@pytest.fixture
@pytest.mark.django_db
def superuser() -> Colaborador:
    superuser = mixer.blend(Colaborador, email="teste.super_user@inpe.br")
    superuser.is_staff = True
    superuser.is_active = True
    superuser.is_superuser = True
    superuser.username = None
    superuser.clean()
    superuser.save()
    return superuser


@pytest.fixture
@pytest.mark.django_db
def colaborador() -> Colaborador:
    vinculo = mixer.blend(Vinculo, vinculo="Administrador")
    divisao = mixer.blend(Divisao)
    predio = mixer.blend(Predio)
    grupo_portal = mixer.blend(GrupoPortal, name="Colaborador")
    grupo_portal.permissions.add(Permission.objects.get(codename="view_colaboradorgrupoacesso"))
    grupo_portal.permissions.add(Permission.objects.get(codename="view_colaborador"))
    grupo_portal.save()
    colaborador = mixer.blend(Colaborador, first_name="Teste", last_name="Fulano de tal", uid=123)
    colaborador.divisao = divisao
    colaborador.vinculo = vinculo
    colaborador.predio = predio
    colaborador.username = None
    colaborador.is_active = True
    colaborador.is_staff = True
    colaborador.is_superuser = False
    colaborador.clean()
    colaborador.groups.add(grupo_portal)
    colaborador.save()
    return colaborador

@pytest.fixture
@pytest.mark.django_db
def secretaria() -> Colaborador:
    grupo_portal = mixer.blend(GrupoPortal, name="Secretaria")
    grupo_portal.permissions.add(Permission.objects.get(codename="secretaria_colaborador",))
    grupo_portal.permissions.add(Permission.objects.get(codename="change_divisao"))
    grupo_portal.permissions.add(Permission.objects.get(codename="view_colaborador",))
    grupo_portal.save()
    secretaria = mixer.blend(Colaborador, email="teste.secretaria@inpe.br")
    secretaria.is_staff = True
    secretaria.is_active = True
    secretaria.username = None
    secretaria.clean()
    secretaria.save()
    secretaria.groups.add(grupo_portal)
    secretaria.save()
    return secretaria


@pytest.fixture
@pytest.mark.django_db
def grupo_trabalho() -> GrupoTrabalho:
    grupo_trabalho = mixer.blend(GrupoTrabalho, grupo="Grupo Trabalho teste", grupo_sistema="teste_grupo", data_criado=None, id=4)
    grupo_trabalho.save()
    return grupo_trabalho


@pytest.fixture
@pytest.mark.django_db
def colaborador_suporte() -> Colaborador:
    grupo_portal = mixer.blend(GrupoPortal, name="Suporte")
    grupo_portal.permissions.add(Permission.objects.get(codename="change_colaborador"))
    grupo_portal.permissions.add(Permission.objects.get(codename="suporte_colaborador"))
    grupo_portal.permissions.add(Permission.objects.get(codename="responsavel_colaborador"))
    grupo_portal.save()
    responsavel = mixer.blend(Colaborador)
    responsavel.groups.add(grupo_portal)
    responsavel.save()
    colaborador_suporte = mixer.blend(Colaborador, first_name="Colaborador", last_name="Fulano de tal", externo=False, responsavel=responsavel, email="teste.pytest1@inpe.br", uid=12)
    colaborador_suporte.data_fim = datetime.date.today() + datetime.timedelta(days=10)
    colaborador_suporte.is_active = True
    colaborador_suporte.username = None
    colaborador_suporte.clean()
    colaborador_suporte.save()
    colaborador_suporte.groups.add(grupo_portal)
    colaborador_suporte.save()
    ## colaborador para Suporte Aprovar ou reprovar
    mixer.blend(Colaborador, username="teste.teste", email="teste.teste@inpe.br", uid="11")
    return colaborador_suporte


@pytest.fixture
@pytest.mark.django_db
def responsavel_grupo() -> Colaborador:
    grupo_portal = mixer.blend(GrupoPortal, name="Responsavel")
    grupo_portal.permissions.add(Permission.objects.get(codename="responsavel_colaborador"))
    grupo_portal.save()

    grupo_trabalho = mixer.blend(GrupoTrabalho, grupo="Grupo de teste", grupo_sistema="teste", gid=10)
    grupo_trabalho.save_confirm()
    
    grupo_acesso = GrupoAcesso(tipo="Desenvolvimento", grupo_trabalho=grupo_trabalho)
    grupo_acesso.save()
    
    responsavel = mixer.blend(Colaborador, first_name="Responsavel", last_name="Fulano de tal", externo=False, email="teste.reponsavel@inpe.br", uid=876598)
    responsavel.username = None
    responsavel.is_active = True
    responsavel.clean()
    responsavel.save()
    responsavel.groups.add(grupo_portal)
    responsavel.save()
    
    responsavel_grupo_trabalho = mixer.blend(ResponsavelGrupoTrabalho, grupo=grupo_trabalho, responsavel=responsavel)
    responsavel_grupo_trabalho.save()
    return responsavel

@pytest.fixture
@pytest.mark.django_db
def chefia() -> Colaborador:
    grupo_portal = mixer.blend(GrupoPortal, name="Chefia")
    grupo_portal.permissions.add(Permission.objects.get(codename="chefia_colaborador"))
    grupo_portal.save()
    chefia = mixer.blend(Colaborador, first_name="Chefe1", last_name="Divisao", email="chefe1.divisao@inpe.br")
    chefia.is_active = True
    chefia.username = None
    chefia.clean()
    chefia.save()
    chefia.groups.add(grupo_portal)
    chefia.save()
    return chefia