
import pytest
from django.test import RequestFactory
from django.urls import reverse
from apps.colaborador.admin import ColaboradorAdmin
from apps.colaborador.models import Colaborador
from apps.core.admin import ColaboradorGrupoAcessoInLineRead, GroupInLine
from apps.core.utils.freeipa import FreeIPA
from apps.core.tests.base import *

pytestmark = pytest.mark.django_db


def test_admin_colaborador_superuser_atualizar_email_ramal_colaborador( admin_site, superuser, colaborador):
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

def test_admin_colaborador_secretaria_visualizar_colaborador_ativo( admin_site, secretaria, colaborador):
    colaborador.is_active = True
    colaborador.save()
    request = RequestFactory().get(reverse('admin:colaborador_colaborador_change', args=(colaborador.id,)))
    request.user = secretaria
    model_admin = ColaboradorAdmin(Colaborador, admin_site)
    model_admin.change_view(request=request, object_id=str(colaborador.pk))
    assert model_admin.readonly_fields == ["username", "uid", "email" , "is_staff", "is_active", "last_login", "date_joined", "data_fim"] 



def test_admin_colaborador_secretaria_visualizar( admin_site, colaborador, secretaria):
    request = RequestFactory().get(reverse('admin:colaborador_colaborador_change', args=(colaborador.id,)))
    request.user = secretaria
    model_admin = ColaboradorAdmin(Colaborador, admin_site)
    model_admin.change_view(request=request, object_id=str(colaborador.pk))
    assert model_admin.inlines == [ColaboradorGrupoAcessoInLineRead]


def test_admin_colaborador_secretaria_visualizar_colaborador_nao_ativo( admin_site, secretaria, colaborador):
    colaborador.is_active = False
    colaborador.save()
    request = RequestFactory().get(reverse('admin:colaborador_colaborador_change', args=(colaborador.id,)))
    request.user = secretaria
    model_admin = ColaboradorAdmin(Colaborador, admin_site)
    model_admin.change_view(request=request, object_id=str(colaborador.pk))
    assert model_admin.inlines == [] 
    assert model_admin.readonly_fields == [ "first_name", "last_name",  "data_nascimento", "email", "telefone" ,"externo", 
                                            "username", "uid", "is_staff", "is_active", "last_login", "date_joined", "vinculo", 
                                            "predio", "divisao", "ramal", "responsavel", "registro_inpe", "empresa", "data_inicio", "data_fim"]
    
    
def test_admin_colaborador_suporte_visualizar_colaborador_ativo( admin_site, colaborador, colaborador_suporte):
    colaborador.is_active = True
    colaborador.save()
    request = RequestFactory().get(reverse('admin:colaborador_colaborador_change', args=(colaborador.id,)))
    request.user = colaborador_suporte
    model_admin = ColaboradorAdmin(Colaborador, admin_site)
    model_admin.change_view(request=request, object_id=str(colaborador.pk))
    assert model_admin.readonly_fields == [ "first_name", "last_name",  "data_nascimento", "username", "uid", "is_staff", "is_active", 
                                    "last_login", "date_joined", "vinculo", "predio", "divisao", "responsavel", "registro_inpe", 
                                    "empresa", "data_inicio", "data_fim"] 
    assert model_admin.fieldsets == [ 
                    ("Informações Pessoais", {"fields": ["first_name", "last_name",  "data_nascimento", "email", ]}), 
                    ("Informações Portal", {"fields": ["username", "uid", "is_staff", "is_active", "last_login", "date_joined"]}), 
                    ("Informações Profissionais", {"fields": ["vinculo", "predio", "divisao", "ramal", "responsavel", "registro_inpe", "empresa", "data_inicio", "data_fim", "externo"]})]