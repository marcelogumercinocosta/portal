
import pytest
from django.test import RequestFactory
from django.urls import reverse
from apps.colaborador.admin import ColaboradorAdmin
from apps.colaborador.models import Colaborador
from apps.core.admin import ColaboradorGrupoAcessoInLineRead, GroupInLine
from apps.core.utils.freeipa import FreeIPA
from apps.core.tests.base import *

pytestmark = pytest.mark.django_db


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
