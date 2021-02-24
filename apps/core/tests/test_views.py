import datetime

import pytest
from apps.core.models import (ColaboradorGrupoAcesso, GrupoAcesso,
                              GrupoTrabalho, ResponsavelGrupoTrabalho)
from apps.core.utils.freeipa import FreeIPA
from apps.core.views import (AtualizarAssinaturaView,
                             AtualizarContaGrupoTrabalhoView,
                             ConfirmarAssinaturaView, CoreStatusView,
                             CriarContaGrupoTrabalhoView, EstruturaGruposView)
from django.contrib.auth.models import User
from django.test import RequestFactory
from django.urls import reverse
from mixer.backend.django import mixer
from apps.core.tests.base import *

pytestmark = pytest.mark.django_db

def test_assinatura_error(grupo_trabalho, superuser):
    request = RequestFactory().get(reverse("core:atualizar_assinatura", kwargs={"pk": grupo_trabalho.pk}))
    request = message_middleware(request)
    request.user = superuser
    response = AtualizarAssinaturaView.as_view()(request, pk=grupo_trabalho.pk)
    assert response.status_code == 200
    assert response.content.decode(('latin-1')) == "Confirme as informações do Cadastro e/ou Responsáveis!"


def test_assinatura_ok(grupo_trabalho, superuser, responsavel_grupo):
    responsavel_grupo_trabalho = mixer.blend(ResponsavelGrupoTrabalho, grupo=grupo_trabalho, responsavel=responsavel_grupo)
    responsavel_grupo_trabalho.save()
    request = RequestFactory().get(reverse("core:atualizar_assinatura", kwargs={"pk": grupo_trabalho.pk}))
    request = message_middleware(request)
    request.user = superuser
    response = AtualizarAssinaturaView.as_view()(request, pk=grupo_trabalho.pk)
    assert response.status_code == 200


def test_assinatura_confirmar_error(grupo_trabalho, superuser):
    request = RequestFactory().get(reverse("core:confirmar_assinatura", kwargs={"pk": grupo_trabalho.pk}))
    request = message_middleware(request)
    request.user = superuser
    response = ConfirmarAssinaturaView.as_view()(request, pk=grupo_trabalho.pk)
    assert response.status_code == 302
    grupo_trabalho_confirmado = GrupoTrabalho.objects.get(pk=grupo_trabalho.pk)
    assert grupo_trabalho_confirmado.confirmacao == False


def test_assinatura_confirmar_ok(grupo_trabalho, superuser, responsavel_grupo):
    responsavel_grupo_trabalho = mixer.blend(ResponsavelGrupoTrabalho, grupo=grupo_trabalho, responsavel=responsavel_grupo)
    responsavel_grupo_trabalho.save()
    request = RequestFactory().get(reverse("core:confirmar_assinatura", kwargs={"pk": grupo_trabalho.pk}))
    request = message_middleware(request)
    request.user = superuser
    response = ConfirmarAssinaturaView.as_view()(request, pk=grupo_trabalho.pk)
    assert response.status_code == 302
    grupo_trabalho_confirmado = GrupoTrabalho.objects.get(pk=grupo_trabalho.pk)
    assert grupo_trabalho_confirmado.confirmacao == True


def test_criar_conta_grupo_ok(grupo_trabalho, superuser, responsavel_grupo):
    # Cria o Responsavel no FreeIpa()
    freeipa = FreeIPA() 
    assert freeipa.set_colaborador(responsavel_grupo,'tmppassword') == 1
    
    # Prepara o Grupo de Trabalho com responsavel
    grupo_trabalho.gid = 9000
    grupo_trabalho.desenvolvimento = True
    grupo_trabalho.operacional = True
    grupo_trabalho.documento = True
    grupo_trabalho.pesquisa = True
    responsavel_grupo_trabalho = mixer.blend(ResponsavelGrupoTrabalho, grupo=grupo_trabalho, responsavel=responsavel_grupo)
    responsavel_grupo_trabalho.save()
    grupo_trabalho.save_confirm()

    request = RequestFactory().get(reverse("core:criar_conta_grupo", kwargs={"pk": grupo_trabalho.pk}))
    request = message_middleware(request)
    request.user = superuser
    response = CriarContaGrupoTrabalhoView.as_view()(request, pk=grupo_trabalho.pk)
    assert response.status_code == 302

    grupo_trabalho_confirmado = GrupoTrabalho.objects.get(pk=grupo_trabalho.pk)
    assert ColaboradorGrupoAcesso.objects.filter(colaborador_id=responsavel_grupo.id).exists() == True
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
    assert freeipa.user_delete(responsavel_grupo.username)


def test_criar_conta_grupo_erro(grupo_trabalho, superuser, responsavel_grupo):
    request = RequestFactory().get(reverse("core:criar_conta_grupo", kwargs={"pk": grupo_trabalho.pk}))
    request = message_middleware(request)
    request.user = superuser
    response = CriarContaGrupoTrabalhoView.as_view()(request, pk=grupo_trabalho.pk)
    assert response.status_code == 302

    grupo_trabalho.gid = 9000
    grupo_trabalho.save_confirm()
    assert response.status_code == 302

    responsavel_grupo_trabalho = mixer.blend(ResponsavelGrupoTrabalho, grupo=grupo_trabalho, responsavel=responsavel_grupo)
    responsavel_grupo_trabalho.save()
    grupo_trabalho.save()
    response = CriarContaGrupoTrabalhoView.as_view()(request, pk=grupo_trabalho.pk)
    assert response.status_code == 302

def test_criar_conta_grupo_erro_freeipa(grupo_trabalho, superuser, responsavel_grupo):
    responsavel_grupo_trabalho = mixer.blend(ResponsavelGrupoTrabalho, grupo=grupo_trabalho, responsavel=responsavel_grupo)
    responsavel_grupo_trabalho.save()
    grupo_trabalho.gid = 9000
    grupo_trabalho.save_confirm()
    request = RequestFactory().get(reverse("core:criar_conta_grupo", kwargs={"pk": grupo_trabalho.pk}))
    request = message_middleware(request)
    request.user = superuser
    assert FreeIPA(request).group_create(grupo_trabalho.grupo_sistema, grupo_trabalho.gid, description="TESTE ERRO CREATE GRUPO") == True
    response = CriarContaGrupoTrabalhoView.as_view()(request, pk=grupo_trabalho.pk)
    assert response.status_code == 302
    grupo_trabalho_confirmado = GrupoTrabalho.objects.get(pk=grupo_trabalho.pk)
    assert grupo_trabalho_confirmado.data_criado == None
    assert FreeIPA(request).group_delete(grupo_trabalho.grupo_sistema) == True


def test_atualizar_conta_grupotrabalho(grupo_trabalho, superuser, responsavel_grupo):
    responsavel_grupo_trabalho = mixer.blend(ResponsavelGrupoTrabalho, grupo=grupo_trabalho, responsavel=responsavel_grupo)
    responsavel_grupo_trabalho.save()
    grupo_trabalho.gid = 9000
    grupo_trabalho.desenvolvimento = True
    grupo_trabalho.operacional = True
    grupo_trabalho.save_confirm()
    request = RequestFactory().get(reverse("core:criar_conta_grupo", kwargs={"pk": grupo_trabalho.pk}))
    request = message_middleware(request)
    request.user = superuser
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
    request.user = superuser
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
    request.user = superuser
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
