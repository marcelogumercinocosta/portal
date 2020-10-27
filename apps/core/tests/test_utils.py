import pytest
from django.contrib.auth.models import AnonymousUser, Group, Permission, User
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from mixer.backend.django import mixer

from apps.colaborador.models import Colaborador
from apps.core.models import (GrupoAcesso, GrupoTrabalho,
                              ResponsavelGrupoTrabalho)
from apps.core.utils.freeipa import FreeIPA
from apps.infra.models import Servidor

pytestmark = pytest.mark.django_db

def test_set_novasenha_error():
    colaborador = mixer.blend(Colaborador, username="teste.teste", email="teste.teste@inpe.br", uid="11")
    colaborador.save()
    assert FreeIPA().set_novasenha(colaborador,'teste_erro') == False


def test_set_colaborador_error():
    grupo_portal = mixer.blend(Group, name="Responsavel")
    responsavel_colaborador = Permission.objects.get(codename="responsavel_colaborador")
    grupo_portal.permissions.add(responsavel_colaborador)
    grupo_portal.save()

    colaborador0 = mixer.blend(Colaborador, username="teste.teste", email="teste.teste@inpe.br", uid="11")
    colaborador0.save()
    responsavel = mixer.blend(Colaborador)
    responsavel.groups.add(grupo_portal)
    responsavel.save()
    colaborador = mixer.blend(Colaborador, first_name="Colaborador", last_name="Fulano de tal", externo=False, responsavel=responsavel, email="teste.pytest1@inpe.br", uid=0)
    colaborador.username = None
    colaborador.clean()
    colaborador.save()
    assert FreeIPA().set_colaborador(colaborador,'teste_erro') == False

    grupo_trabalho = mixer.blend(GrupoTrabalho, grupo="Grupo de teste", grupo_sistema="teste", gid=0)
    grupo_trabalho.save()
    assert FreeIPA().set_colaborador_grupo(grupo_trabalho) == False


def test_set_grupo_error():
    grupo_trabalho = mixer.blend(GrupoTrabalho, grupo="Grupo de teste", grupo_sistema="teste", gid=0)
    grupo_trabalho.save()
    assert FreeIPA().set_grupo(grupo_trabalho) == False


def test_set_host_error():
    servidor = mixer.blend(Servidor)
    servidor.save()
    assert FreeIPA().set_host(servidor, force=False) == False


def test_set_sudo_error():
    grupo_trabalho = mixer.blend(GrupoTrabalho, grupo="Grupo de teste", grupo_sistema="teste", gid=0)
    grupo_trabalho.save()
    assert FreeIPA().set_sudo(grupo_trabalho) == False


def test_remove_grupo_error():
    grupo_trabalho = mixer.blend(GrupoTrabalho, grupo="Grupo de teste", grupo_sistema="teste", gid=0)
    grupo_trabalho.save()
    assert FreeIPA().remove_grupo(grupo_trabalho) == False


def test_set_hbac_group():
    grupo_portal = mixer.blend(Group, name="Responsavel")
    responsavel_colaborador = Permission.objects.get(codename="responsavel_colaborador")
    grupo_portal.permissions.add(responsavel_colaborador)
    grupo_portal.save()
    responsavel = mixer.blend(Colaborador)
    responsavel.groups.add(grupo_portal)
    responsavel.save()

    grupo_trabalho = mixer.blend(GrupoTrabalho, grupo="Grupo de teste", grupo_sistema="teste", gid=0)
    grupo_trabalho.save()
    grupo_trabalho.gid = 9000
    grupo_trabalho.desenvolvimento = True
    grupo_trabalho.operacional = True
    grupo_trabalho.documento = True
    grupo_trabalho.pesquisa = True
    grupo_trabalho.save_confirm()

    responsavel_grupo_trabalho = mixer.blend(ResponsavelGrupoTrabalho, grupo=grupo_trabalho, responsavel=responsavel)
    responsavel_grupo_trabalho.save()
    grupo_trabalho.gid = 9000
    grupo_trabalho.desenvolvimento = True
    grupo_trabalho.operacional = True
    grupo_trabalho.save_confirm()

    grupo_acesso = mixer.blend(GrupoAcesso, grupo_trabalho=grupo_trabalho)
    grupo_acesso.save()
    assert FreeIPA().set_hbac_group(grupo_acesso) == False
    


def test_add_user_group_hhac_error():
    grupo_portal = mixer.blend(Group, name="Responsavel")
    responsavel_colaborador = Permission.objects.get(codename="responsavel_colaborador")
    grupo_portal.permissions.add(responsavel_colaborador)
    grupo_portal.save()
    colaborador0 = mixer.blend(Colaborador, username="teste.teste", email="teste.teste@inpe.br", uid="11")
    colaborador0.save()
    responsavel = mixer.blend(Colaborador)
    responsavel.groups.add(grupo_portal)
    responsavel.save()
    colaborador = mixer.blend(Colaborador, first_name="Colaborador", last_name="Fulano de tal", externo=False, responsavel=responsavel, email="teste.pytest1@inpe.br", uid=0)
    colaborador.username = None
    colaborador.clean()
    colaborador.save()
    assert FreeIPA().add_user_group_hhac(colaborador,'teste', 'teste') == False
