
import pytest
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import AnonymousUser, Group, Permission, User
from django.test import RequestFactory
from django.urls import reverse
from mixer.backend.django import mixer
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from apps.colaborador.admin import (ColaboradorAdmin, ContaAdmin)
from apps.colaborador.models import Colaborador
from apps.core.admin import ColaboradorGrupoAcessoInLineRead, GroupInLine
from apps.core.models import GrupoAcesso, ColaboradorGrupoAcesso
from apps.core.utils.freeipa import FreeIPA

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


@pytest.fixture
def admin_site():
    return AdminSite()

@pytest.fixture
@pytest.mark.django_db
def superuser() -> Colaborador:
    group = mixer.blend(Group, name="Responsavel")
    responsavel_colaborador = Permission.objects.get(codename="responsavel_colaborador")
    group.permissions.add(responsavel_colaborador)
    group.save()

    superuser = mixer.blend(Colaborador, email="teste.super_user@inpe.br")
    superuser.is_staff = True
    superuser.is_active = True
    superuser.is_superuser = True
    superuser.username = None
    superuser.clean()
    superuser.save()
    superuser.groups.add(group)
    superuser.save()
    return superuser


@pytest.fixture
@pytest.mark.django_db
def secretaria() -> Colaborador:
    group = mixer.blend(Group, name="Secretaria")
    secretaria_colaborador = Permission.objects.get(codename="secretaria_colaborador",)
    view_colaborador = Permission.objects.get(codename="view_colaborador",)
    group.permissions.add(secretaria_colaborador)
    group.permissions.add(view_colaborador)
    group.save()
    secretaria = mixer.blend(Colaborador, email="teste.secretaria@inpe.br")
    secretaria.is_staff = True
    secretaria.is_active = True
    secretaria.username = None
    secretaria.clean()
    secretaria.save()
    secretaria.groups.add(group)
    secretaria.save()
    return secretaria

@pytest.fixture
@pytest.mark.django_db
def colaborador() -> Colaborador:
    group = mixer.blend(Group, name="Colaborador")
    group.permissions.add(Permission.objects.get(codename="change_conta"))
    group.save()

    colaborador = mixer.blend(Colaborador, first_name="Teste", last_name="Fulano de tal", uid=123)
    colaborador.username = None
    colaborador.is_superuser = True
    colaborador.clean()
    colaborador.groups.add(group)
    colaborador.save()
    return colaborador


def test_an_admin_view( admin_client):
    response = admin_client.get('/admin/')
    assert response.status_code == 200


def test_admin_colaborador_superuser_edit_email_user_not_activeview( admin_site, superuser, colaborador):
    colaborador.ramal = 123456
    colaborador.save()
    request = RequestFactory().get(reverse('admin:colaborador_colaborador_change', args=(colaborador.id,)))
    request.user = superuser
    request = message_middleware(request)
    model_admin = ColaboradorAdmin(Colaborador, admin_site)
    model_admin.change_view(request=request, object_id=str(colaborador.pk))
    assert model_admin.inlines == [GroupInLine, ColaboradorGrupoAcessoInLineRead]
    form_colaborador = model_admin.get_form(request,obj=colaborador,change=False)
    data_form = colaborador.__dict__
    data_form.update({"ramal":"12312313"})
    form = form_colaborador(data=data_form)
    freeipa = FreeIPA(request)
    assert freeipa.set_colaborador(colaborador, "tmp_password") == True
    model_admin.save_model(request=request, obj=colaborador, change=True, form=form)
    assert freeipa.user_find_show(displayname=colaborador.username)['result'][0]['telephonenumber'] == ["12312313"]
    assert freeipa.user_delete(colaborador.username) == True

def test_admin_colaborador_secretaria_user_active_view( admin_site, secretaria, colaborador):
    colaborador.is_active = True
    colaborador.save()
    request = RequestFactory().get(reverse('admin:colaborador_colaborador_change', args=(colaborador.id,)))
    request.user = secretaria
    model_admin = ColaboradorAdmin(Colaborador, admin_site)
    model_admin.change_view(request=request, object_id=str(colaborador.pk))
    assert model_admin.readonly_fields == ["username", "uid", "email" , "is_staff", "is_active", "last_login", "date_joined", "data_fim"] 


def test_admin_colaborador_secretaria_view( admin_site, colaborador, secretaria):
    request = RequestFactory().get(reverse('admin:colaborador_colaborador_change', args=(colaborador.id,)))
    request.user = secretaria
    model_admin = ColaboradorAdmin(Colaborador, admin_site)
    model_admin.change_view(request=request, object_id=str(colaborador.pk))
    assert model_admin.inlines == [ColaboradorGrupoAcessoInLineRead]


def test_admin_conta_view( admin_site, superuser):
    request = RequestFactory().get(reverse('admin:colaborador_conta_conta'))
    request.user = superuser
    model_admin = ContaAdmin(Colaborador, admin_site)
    model_admin.change_view(request=request)
    assert model_admin.inlines == [ColaboradorGrupoAcessoInLineRead]