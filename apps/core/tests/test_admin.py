
import datetime

import pytest
from django.test import RequestFactory
from django.urls import reverse
from mixer.backend.django import mixer

from apps.colaborador.models import Colaborador
from apps.core.admin import (GrupoAcessoColaboradorInLineRead, GroupInLine,
                             GrupoAcessoAdmin, ColaboradorGrupoAcessoInLineRead,DivisaoAdmin,
                             GrupoTrabalhoAdmin, GrupoAcessoInLine, ColaboradorGrupoAcesso)
from apps.core.models import (GrupoAcesso, GrupoTrabalho, Divisao, ColaboradorGrupoAcesso, GrupoPortal)
from apps.core.utils.freeipa import FreeIPA
from apps.core.tests.base import *

pytestmark = pytest.mark.django_db


def test_colaborador_grupoacesso_inline_read(admin_site, superuser) -> None:
    request = RequestFactory().get(reverse('admin:colaborador_colaborador_change', args=(superuser.id,)))
    request.user = superuser
    model_admin = ColaboradorGrupoAcessoInLineRead(ColaboradorGrupoAcesso, admin_site)
    assert model_admin.has_delete_permission(request) == False
    assert model_admin.has_add_permission(request) == False


def test_group_inline(admin_site, superuser) -> None:
    request = RequestFactory().get(reverse('admin:colaborador_colaborador_change', args=(superuser.id,)))
    request.user = superuser
    model_admin = GroupInLine(GrupoPortal, admin_site)
    formset = model_admin.get_formset(request)
    assert formset.form.base_fields["group"].label == "Grupo no Portal"


def test_grupoacesso_grupotrabalho_inline(admin_site, superuser, grupo_trabalho) -> None:
    request = RequestFactory().get(reverse('admin:core_grupotrabalho_change', args=(grupo_trabalho.id,)))
    request.user = superuser
    model_admin = GrupoAcessoInLine(GrupoAcesso, admin_site)
    assert model_admin.has_delete_permission(request) == False
    assert model_admin.has_add_permission(request) == False


def test_grupoacesso_grupotrabalho_inline(admin_site, superuser, grupo_trabalho) -> None:
    request = RequestFactory().get(reverse('admin:core_grupotrabalho_change', args=(grupo_trabalho.id,)))
    request.user = superuser
    model_admin = GrupoAcessoInLine(GrupoAcesso, admin_site)
    assert model_admin.has_delete_permission(request) == False
    assert model_admin.has_add_permission(request) == False


def test_grupotrabalho_grupoacesso_inline(admin_site, superuser, grupo_trabalho) -> None:
    request = RequestFactory().get(reverse('admin:core_grupotrabalho_change', args=(grupo_trabalho.id,)))
    request.user = superuser
    model_admin = GrupoAcessoInLine(GrupoAcesso, admin_site)
    assert model_admin.has_delete_permission(request) == False
    assert model_admin.has_add_permission(request) == False


def test_colaborador_grupoacesso_inlineread(admin_site, superuser, grupo_trabalho, colaborador) -> None:
    colaborador_grupo_acesso = ColaboradorGrupoAcesso
    colaborador_grupo_acesso.colaborador = colaborador
    request = RequestFactory().get(reverse('admin:core_grupotrabalho_change', args=(grupo_trabalho.id,)))
    request.user = superuser
    model_admin = GrupoAcessoColaboradorInLineRead(ColaboradorGrupoAcesso, admin_site)

    assert model_admin.has_delete_permission(request) == False
    assert model_admin.has_add_permission(request) == False
    assert model_admin.nome(colaborador_grupo_acesso) == colaborador.full_name
    assert model_admin.username(colaborador_grupo_acesso) == colaborador.username
    assert model_admin.ramal(colaborador_grupo_acesso) == colaborador.ramal
    assert model_admin.email(colaborador_grupo_acesso) == colaborador.email


def test_grupoacesso_admin(admin_site, superuser) -> None:
    request = RequestFactory().get(reverse('admin:core_grupoacesso_changelist'))
    request.user = superuser
    model_admin = GrupoAcessoAdmin(GrupoAcesso, admin_site)
    assert model_admin.has_add_permission(request) == False

def test_grupotrabalho_admin(admin_site, superuser, grupo_trabalho) -> None:
    request = RequestFactory().get(reverse('admin:core_grupotrabalho_change', args=(grupo_trabalho.id,)))
    request.user = superuser
    model_admin = GrupoTrabalhoAdmin(GrupoTrabalho, admin_site)
    assert model_admin.oper(grupo_trabalho) == grupo_trabalho.operacional
    assert model_admin.pesq(grupo_trabalho) == grupo_trabalho.pesquisa
    assert model_admin.dev(grupo_trabalho) == grupo_trabalho.pesquisa
    assert model_admin.doc(grupo_trabalho) == grupo_trabalho.documento
    assert model_admin.readonly_fields == ["data_criado","confirmacao"]


def test_grupotrabalho_create_admin(admin_site, superuser, grupo_trabalho) -> None:
    request = RequestFactory().get(reverse('admin:core_grupotrabalho_change', args=(grupo_trabalho.id,)))
    grupo_trabalho.data_criado = datetime.date.today()
    grupo_trabalho.confirmacao = True
    grupo_trabalho.save()
    request.user = superuser
    model_admin = GrupoTrabalhoAdmin(GrupoTrabalho, admin_site)
    model_admin.change_view(request=request, object_id=str(grupo_trabalho.pk))
    assert model_admin.readonly_fields ==  ["grupo_sistema", "gid", "divisao", "data_criado","confirmacao"]
    model_admin.add_view(request=request)
    assert model_admin.readonly_fields == ["data_criado","confirmacao"]


def test_grupotrabalho_create_delete_not_freeipa(admin_site, superuser, grupo_trabalho) -> None:
    request = RequestFactory().get(reverse('admin:core_grupotrabalho_change', args=(grupo_trabalho.id,)))
    request.user = superuser
    model_admin = GrupoTrabalhoAdmin(GrupoTrabalho, admin_site)
    model_admin.delete_model(request=request, obj=grupo_trabalho)
    assert GrupoTrabalho.objects.filter(id=grupo_trabalho.pk).exists() == False

def test_grupotrabalho_create_delete_freeipa(admin_site, superuser) -> None:
    grupo_trabalho = mixer.blend(GrupoTrabalho, grupo="Grupo teste", grupo_sistema="teste", data_criado=None, gid=10)
    grupo_trabalho.save()
    request = RequestFactory().get(reverse('admin:core_grupotrabalho_change', args=(grupo_trabalho.id,)))
    request.user = superuser
    request = message_middleware(request)
    grupo_trabalho.data_criado = datetime.date.today()
    grupo_trabalho.confirmacao = True
    grupo_trabalho.save()
    model_admin = GrupoTrabalhoAdmin(GrupoTrabalho, admin_site)
    freeipa = FreeIPA(request) 
    assert freeipa.set_grupo(grupo_trabalho) == True
    assert freeipa.group_find_count(cn=grupo_trabalho.grupo_sistema) == 1
    assert freeipa.sudorule_find_count(cn=grupo_trabalho.get_sudo()) == 1
    assert freeipa.user_find_count(displayname=grupo_trabalho.grupo_sistema) == 1
    sudo_rule = freeipa.sudorule_find_show(cn=grupo_trabalho.get_sudo())
    # assert sudo_rule['result']['memberallowcmd_sudocmdgroup'] == ['sudo_cmd_default_usuarios']
    model_admin.delete_model(request=request, obj=grupo_trabalho)
    assert freeipa.group_find_count(cn=grupo_trabalho.grupo_sistema) == 0
    assert freeipa.sudorule_find_count(cn=grupo_trabalho.get_sudo()) == 0
    assert freeipa.user_find_count(displayname=grupo_trabalho.grupo_sistema) == 0
    assert GrupoTrabalho.objects.filter(id=grupo_trabalho.pk).exists() == False


def test_divisao_admin(admin_site, superuser) -> None:
    chefe = mixer.blend(Colaborador, first_name="chefe", last_name='principal', email='email@dochefe.com')
    chefe_substituto = mixer.blend(Colaborador, first_name="chefe", last_name='substituto', email='email@dochefe.com')
    divisao = mixer.blend(Divisao, chefe=chefe, chefe_substituto=chefe_substituto)
    request = RequestFactory().get(reverse('admin:core_divisao_change', args=(divisao.id,)))
    request.user = superuser
    model_admin = DivisaoAdmin(Divisao, admin_site)
    model_admin.change_view(request=request, object_id=str(divisao.id))
    assert model_admin.readonly_fields == []



def test_divisao_admin_secretaria(admin_site, secretaria) -> None:
    chefe = mixer.blend(Colaborador, first_name="chefe", last_name='principal', email='email@dochefe.com')
    chefe_substituto = mixer.blend(Colaborador, first_name="chefe", last_name='substituto', email='email@dochefe.com')
    divisao = mixer.blend(Divisao, chefe=chefe, chefe_substituto=chefe_substituto)
    request = RequestFactory().get(reverse('admin:core_divisao_change', args=(divisao.id,)))
    request.user = secretaria
    model_admin = DivisaoAdmin(Divisao, admin_site)
    model_admin.change_view(request=request, object_id=str(divisao.id))
    assert model_admin.readonly_fields == ["divisao", 'divisao_completo', 'coordenacao']