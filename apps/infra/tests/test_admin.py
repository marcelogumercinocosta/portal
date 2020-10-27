
import datetime

import pytest
from django.forms import inlineformset_factory
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import AnonymousUser, Group, Permission, User
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.forms import formset_factory
from django.test import RequestFactory
from django.urls import reverse
from mixer.backend.django import mixer

from apps.colaborador.models import Colaborador
from apps.core.models import (Divisao, GrupoAcesso, GrupoTrabalho, Predio, 
                              ResponsavelGrupoTrabalho)
from apps.core.utils.freeipa import FreeIPA
from apps.core.utils.history import HistoryCore
from apps.core.views import UpdateGrupoAcesso
from apps.infra.admin import (EquipamentoParteRackInLine,
                              EquipamentoRackInLine,
                              GrupoAcessoEquipamentoInLine,
                              GrupoAcessoEquipamentoInLineRead,
                              HostnameIPInLine, OcorrenciaInLine, RackAdmin,
                              ServidorAdmin)
from apps.infra.forms import EquipamentoGrupoAcessoForm, ServidorForm, HostnameIPInLineForm
from apps.infra.models import (AmbienteVirtual, Equipamento,
                               EquipamentoGrupoAcesso, EquipamentoParte,
                               HostnameIP, Ocorrencia, Rack, Rede, Servidor,
                               ServidorHostnameIP, Storage, StorageArea,
                               StorageAreaGrupoTrabalho,
                               StorageGrupoAcessoMontagem, Supercomputador)
from apps.infra.utils.freeipa_location import Automount

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
@pytest.mark.django_db
def grupo_trabalho() -> GrupoTrabalho:
    grupo_trabalho = mixer.blend(GrupoTrabalho, grupo="Grupo teste", grupo_sistema="teste", data_criado=None, id=4)
    grupo_trabalho.gid = 9000
    grupo_trabalho.desenvolvimento = True
    grupo_trabalho.operacional = True
    grupo_trabalho.save_confirm()

    responsavel = mixer.blend(Colaborador, first_name="Responsavel", last_name="Fulano de tal", externo=False, email="teste.reponsavel@inpe.br")
    responsavel.username = None
    responsavel.clean()
    responsavel.groups.add(Group.objects.get(name="Responsavel"))
    responsavel.save()

    responsavel_grupo_trabalho = mixer.blend(ResponsavelGrupoTrabalho, grupo=grupo_trabalho, responsavel=responsavel)
    responsavel_grupo_trabalho.save()

    return grupo_trabalho


@pytest.fixture
@pytest.mark.django_db
def responsavel() -> Colaborador:
    
    return responsavel


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


def test_grupoacesso_grupotrabalho_inline(admin_site, superuser) -> None:
    grupo_acesso = mixer.blend(GrupoAcesso)
    equipamento = mixer.blend(Equipamento)
    equipamento_grupo_acesso = mixer.blend(EquipamentoGrupoAcesso, equipamento=equipamento, grupo_acesso=grupo_acesso)

    request = RequestFactory().get(reverse('admin:core_grupoacesso_change', args=(grupo_acesso.id,)))
    request.user = superuser
    model_admin = GrupoAcessoEquipamentoInLineRead(EquipamentoGrupoAcesso, admin_site)
    assert model_admin.has_delete_permission(request) == False
    assert model_admin.has_add_permission(request) == False
    assert model_admin.equipamento_name(equipamento_grupo_acesso) == equipamento.nome() 
    assert model_admin.equipamento_descricao(equipamento_grupo_acesso) == equipamento.descricao
    assert model_admin.equipamento_tipo(equipamento_grupo_acesso) == equipamento.tipo 

def test_equipamento_rack_inline(admin_site, superuser) -> None:
    rack = mixer.blend(Rack, posicao_linha_inicial="AX" , posicao_linha_final="BA", posicao_coluna_inicial=38, posicao_coluna_final=38, consumo=1000)

    request = RequestFactory().get(reverse('admin:infra_rack_change', args=(rack.id,)))
    request.user = superuser
    model_admin = EquipamentoRackInLine(Servidor, admin_site)
    assert model_admin.has_delete_permission(request) == False
    assert model_admin.has_add_permission(request) == False

def test_hostname_ip_inline(admin_site, superuser) -> None:
    servidor = mixer.blend(Servidor)

    request = RequestFactory().get(reverse('admin:infra_servidor_change', args=(servidor.pk,)))
    request.user = superuser
    model_admin = HostnameIPInLine(ServidorHostnameIP, admin_site)
    assert model_admin.has_change_permission(request) == False


def test_ocorrencia_inline(admin_site, superuser) -> None:
    equipamento = mixer.blend(EquipamentoParte)
    ocorrencia = mixer.blend(Ocorrencia, equipamento=equipamento)
    request = RequestFactory().get(reverse('admin:infra_equipamentoparte_change', args=(equipamento.pk,)))

    request.user = superuser
    model_admin = OcorrenciaInLine(Ocorrencia, admin_site)
    assert model_admin.has_add_permission(request) == False
    assert model_admin.get_readonly_fields(ocorrencia) == ["data"]


def test_equipamento_parte_rack_inLine(admin_site, superuser) -> None:
    rack = mixer.blend(Rack, posicao_linha_inicial="AX" , posicao_linha_final="BA", posicao_coluna_inicial=38, posicao_coluna_final=38, consumo=1000)
    equipamento_parte = mixer.blend(EquipamentoParte, marca='HP', modelo='GEN 10', rack=rack, patrimonio=123 )

    request = RequestFactory().get(reverse('admin:infra_rack_change', args=(rack.id,)))
    request.user = superuser
    model_admin = EquipamentoParteRackInLine(EquipamentoParte, admin_site)
    assert model_admin.has_delete_permission(request) == False
    assert model_admin.has_add_permission(request) == False
    assert model_admin.name_inline(equipamento_parte) == "HP GEN 10 - Patrimônio:123" 


def test_rack_admin(admin_site, superuser) -> None:
    rack = mixer.blend(Rack, posicao_linha_inicial="AX" , posicao_linha_final="BA", posicao_coluna_inicial=38, posicao_coluna_final=38, consumo=1000)
    model_admin = RackAdmin(Rack, admin_site)
    assert model_admin.equipamentos(rack) == 0
    assert model_admin.equipamentos_consumo(rack) == None
    equipamento_parte = mixer.blend(EquipamentoParte, marca='HP', modelo='GEN 10', rack=rack, patrimonio=123, consumo=1000)
    assert model_admin.equipamentos(rack) == 1
    assert model_admin.equipamentos_consumo(rack) == 1000

    request = RequestFactory().get(reverse('admin:infra_rack_change', args=(rack.id,)))
    request.user = superuser
    model_admin = RackAdmin(Rack, admin_site)

    model_admin.add_view(request=request)
    assert model_admin.readonly_fields ==  []

    model_admin.change_view(request=request, object_id=str(rack.id))
    assert model_admin.readonly_fields ==  ["predio"]


def test_servidor_admin_create(admin_site, superuser) -> None:
    rede = mixer.blend(Rede, rede="rede", ip='192.168.0')
    hostnameip = mixer.blend(HostnameIP, hostname='server1', ip='192.168.0.2', tipo=rede)
    servidor = mixer.blend(Servidor, nome='server1 | 192.168.0.2', descricao="Servidor de TESTE")
    data_form = servidor.__dict__
    form = ServidorForm(data=data_form)

    request = RequestFactory().get(reverse('admin:infra_servidor_add'))
    request.user = superuser
    request = message_middleware(request)
    model_admin = ServidorAdmin(Servidor, admin_site)
    model_admin.save_model(request=request, obj=servidor, change=False, form=form)
    assert Servidor.objects.filter(pk=servidor.pk).exists() == True
    assert HostnameIP.objects.get(pk=hostnameip.pk).reservado == True


def test_servidor_admin(admin_site, superuser, grupo_trabalho) -> None:
    predio =  mixer.blend(Predio)
    rede = mixer.blend(Rede, rede="rede", ip='192.168.0', prioridade=1)
    hostnameip = mixer.blend(HostnameIP, hostname='server1', ip='192.168.0.2', tipo=rede, reservado=True)
    mixer.blend(StorageGrupoAcessoMontagem, ip='192.168.0.1', parametro='-fstype=nfs4,rw', tipo='OPERACIONAL', montagem="/dados/teste", namespace="/oper/dados/teste", automount="auto.grupo" , rede=rede, grupo_trabalho=grupo_trabalho)
    mixer.blend(StorageGrupoAcessoMontagem, ip='192.168.0.1', parametro='-fstype=nfs4,rw', tipo='OPERACIONAL', montagem="/scripts/teste", namespace="/oper/scripts/teste", automount="auto.grupo", rede=rede, grupo_trabalho=grupo_trabalho)
    mixer.blend(StorageGrupoAcessoMontagem, ip='192.168.0.1', parametro='-fstype=nfs4,rw', tipo='OPERACIONAL', montagem="/log/teste", namespace="/oper/log/teste", automount="auto.grupo", rede=rede, grupo_trabalho=grupo_trabalho)
    mixer.blend(StorageGrupoAcessoMontagem, ip='192.168.0.5', parametro='-fstype=nfs4,rw', tipo='OPERACIONAL', montagem="/share/teste", namespace="/share/teste", automount="auto.grupo", rede=rede, grupo_trabalho=grupo_trabalho)
    servidor = mixer.blend(Servidor, nome='server1', descricao="Servidor de TESTE", ldap=True, tipo_uso="OPERACIONAL", predio=predio)
    data_form = servidor.__dict__

    ServidorHostnameIP.objects.create(servidor=servidor, hostnameip=hostnameip)

    request = RequestFactory().get(reverse('admin:infra_servidor_change', args=[servidor.pk]))
    request.user = superuser
    request = message_middleware(request)
    model_admin = ServidorAdmin(Servidor, admin_site)
    
    freeipa = FreeIPA(request) 
    freeipa.set_grupo(grupo_trabalho)
    history_core = HistoryCore(request)
    history_core.update_grupo_acesso(grupo=grupo_trabalho, assunto="Nova conta de Grupo de Trabalho")
    UpdateGrupoAcesso(client_feeipa=freeipa, history_core=history_core).update_acesso(grupo_trabalho)

    freeipa.set_host(servidor, description=servidor.descricao)
    assert model_admin.inlines == (HostnameIPInLine,) 
    assert model_admin.readonly_fields == ("status","ldap") 

    model_admin.add_view(request=request)
    assert model_admin.inlines == ()
    assert model_admin.readonly_fields == ("status","ldap") 

    model_admin.change_view(request=request, object_id=str(servidor.pk))
    assert model_admin.inlines == (HostnameIPInLine, GrupoAcessoEquipamentoInLine, OcorrenciaInLine) 
    assert model_admin.readonly_fields == ("nome", "status", "ldap") 

    assert freeipa.host_find_show(fqdn=servidor.freeipa_name)['result']['description'] == ["Servidor de TESTE"]
    data_form.update({"descricao":"Servidor de TESTE alteração"})
    form = ServidorForm(data=data_form)
    model_admin.save_model(request=request, obj=servidor, change=True, form=form)
    assert freeipa.host_find_show(fqdn=servidor.freeipa_name)['result']['description'] == ["Servidor de TESTE alteração"]

    grupo_acesso_oper = GrupoAcesso.objects.filter(grupo_trabalho__id=grupo_trabalho.id, tipo='OPERACIONAL')
    data = {
        'form-INITIAL_FORMS': '0',
        'form-TOTAL_FORMS': '2',
        'form-MAX_NUM_FORMS': '',
        'form-0-grupo_acesso':  grupo_acesso_oper[0].id,
        'form-0-equipamento':  servidor.equipamento_ptr.id
    }
    grupoacesso_equipamento_inline_formset = inlineformset_factory(Servidor, EquipamentoGrupoAcesso, fields=['grupo_acesso'], form=EquipamentoGrupoAcessoForm, can_delete=True)
    formset = grupoacesso_equipamento_inline_formset(data, prefix='form', instance=servidor)
    formset.is_valid()
    model_admin.save_formset(request=request, form=form, formset=formset, change=True )

    assert freeipa.automountlocation_find_count(cn=servidor.freeipa_name_mount) == 1
    assert freeipa.automountmap_find_count(automountlocationcn=servidor.freeipa_name_mount, automountmapname=grupo_acesso_oper[0].automountmap) == 1
    assert freeipa.automountkey_find_count(automountlocationcn=servidor.freeipa_name_mount, automountmapautomountmapname=grupo_acesso_oper[0].automountmap) == 4
    assert freeipa.hbacrule_show(cn=grupo_acesso_oper[0].hbac_freeipa)['result']['memberhost_host'] == ['server1.cptec.inpe.br']
    assert model_admin.grupo(servidor) == "TESTE"

    grupoacesso_equipamento = EquipamentoGrupoAcesso.objects.all()
    assert len(grupoacesso_equipamento) ==  1

    data = {
        # management_form data
        'form-INITIAL_FORMS': '1',
        'form-TOTAL_FORMS': '2',
        'form-MAX_NUM_FORMS': '',
        'form-0-grupo_acesso':  grupoacesso_equipamento[0].grupo_acesso.id,
        'form-0-equipamento':  servidor.equipamento_ptr.id,
        'form-0-id': grupoacesso_equipamento[0].id,
        'form-0-DELETE': True,
    }

    grupoacesso_equipamento_inline_formset = inlineformset_factory(Servidor, EquipamentoGrupoAcesso, fields=['grupo_acesso'], form=EquipamentoGrupoAcessoForm, can_delete=True)
    formset = grupoacesso_equipamento_inline_formset(data, prefix='form', instance=servidor)
    formset.is_valid()
    model_admin.save_formset(request=request, form=form, formset=formset, change=True )
    assert len(EquipamentoGrupoAcesso.objects.all()) ==  0
    assert freeipa.automountmap_find_count(automountlocationcn=servidor.freeipa_name_mount, automountmapname=grupoacesso_equipamento[0].grupo_acesso.automountmap) == 0
    with pytest.raises(AssertionError):
        assert 'memberhost_host' in freeipa.hbacrule_show(cn=grupo_acesso_oper[0].hbac_freeipa)['result']

    hostnameip_2 = mixer.blend(HostnameIP, hostname='server2', ip='192.168.0.3', tipo=rede, reservado=False)
    data = {
        # management_form data
        'form-INITIAL_FORMS': '0',
        'form-TOTAL_FORMS': '2',
        'form-MAX_NUM_FORMS': '',
        
        # First user data
        'form-0-hostnameip':  hostnameip_2.id,
        'form-0-equipamento':  servidor.equipamento_ptr.id
    }

    hostname_equipamento_inline_formset = inlineformset_factory(Servidor, ServidorHostnameIP, fields=['hostnameip'], form=HostnameIPInLineForm, can_delete=True)
    formset = hostname_equipamento_inline_formset(data, prefix='form', instance=servidor)
    formset.is_valid()
    model_admin.save_formset(request=request, form=form, formset=formset, change=True )
    assert HostnameIP.objects.get(pk=hostnameip_2.pk).reservado == True

    grupos_acesso = GrupoAcesso.objects.filter(grupo_trabalho__id=grupo_trabalho.pk)
    for grupoacesso  in grupos_acesso: 
        assert freeipa.hbacrule_delete(grupoacesso.hbac_freeipa) 
    assert freeipa.remove_grupo(grupo_trabalho) == True
    servidor_hostname_ip = ServidorHostnameIP.objects.all()
    assert len(servidor_hostname_ip) ==  2

    data = {
        # management_form data
        'form-INITIAL_FORMS': '1',
        'form-TOTAL_FORMS': '2',
        'form-MAX_NUM_FORMS': '',
        'form-0-hostnameip':  servidor_hostname_ip[1].hostnameip.id,
        'form-0-equipamento':  servidor.equipamento_ptr.id,
        'form-0-id': servidor_hostname_ip[1].id,
        'form-0-DELETE': True,
    }

    hostname_equipamento_inline_formset = inlineformset_factory(Servidor, ServidorHostnameIP, fields=['hostnameip'], form=HostnameIPInLineForm, can_delete=True)
    formset = hostname_equipamento_inline_formset(data, prefix='form', instance=servidor)
    formset.is_valid()
    model_admin.save_formset(request=request, form=form, formset=formset, change=True )
    assert HostnameIP.objects.get(pk=hostnameip_2.pk).reservado == False
    assert len(ServidorHostnameIP.objects.all()) ==  1

    model_admin.delete_model(request=request, obj=servidor)
    assert freeipa.host_find_count(fqdn=servidor.freeipa_name) == 0
    assert freeipa.automountlocation_find_count(cn=servidor.freeipa_name_mount) == 0
    assert HostnameIP.objects.get(pk=hostnameip.pk).reservado == False
    assert Servidor.objects.filter(pk=servidor.pk).exists() == False

def test_servidor_admin_automount_error(admin_site, superuser, grupo_trabalho) -> None:
    rede = mixer.blend(Rede, rede="rede", ip='192.168.0', prioridade=1)
    hostnameip = mixer.blend(HostnameIP, hostname='server1', ip='192.168.0.2', tipo=rede, reservado=True)
    servidor = mixer.blend(Servidor, nome='server1', descricao="Servidor de TESTE", ldap=True, tipo_uso="OPERACIONAL")
    ServidorHostnameIP.objects.create(servidor=servidor, hostnameip=hostnameip)
    request = RequestFactory().get(reverse('admin:infra_servidor_change', args=[servidor.pk]))
    request.user = superuser
    request = message_middleware(request)
    model_admin = ServidorAdmin(Servidor, admin_site)
    
    freeipa = FreeIPA(request)
    freeipa.set_grupo(grupo_trabalho)
    history_core = HistoryCore(request)
    history_core.update_grupo_acesso(grupo=grupo_trabalho, assunto="Nova conta de Grupo de Trabalho")
    UpdateGrupoAcesso(client_feeipa=freeipa, history_core=history_core).update_acesso(grupo_trabalho)
    freeipa.set_host(servidor, description=servidor.descricao)
    assert freeipa.automountlocation_find_count(cn=servidor.freeipa_name_mount) == 1
    
    grupos_acesso = GrupoAcesso.objects.filter(grupo_trabalho__id=grupo_trabalho.pk)
    automount = Automount(freeipa, servidor, request)
    automount.remover_grupos(grupos_acesso)
    freeipa.automountlocation_del(servidor.freeipa_name_mount)
    automount.remover_grupos(grupos_acesso)

    assert freeipa.remove_grupo(grupo_trabalho) == True
    model_admin.delete_model(request=request, obj=servidor)
    for grupoacesso  in grupos_acesso: 
        assert freeipa.hbacrule_delete(grupoacesso.hbac_freeipa) 