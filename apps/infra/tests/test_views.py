import pytest
from django.contrib.auth.models import AnonymousUser, Group, Permission, User
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.exceptions import ValidationError
from django.http import Http404
from django.test import RequestFactory
from django.urls import reverse
from mixer.backend.django import mixer

from apps.colaborador.models import Colaborador
from apps.core.models import ( GrupoAcesso, Predio,
                              ResponsavelGrupoTrabalho)
from apps.core.utils.freeipa import FreeIPA
from apps.core.utils.history import HistoryCore
from apps.core.views import UpdateGrupoAcesso
from apps.infra.models import ( Equipamento,
                               EquipamentoGrupoAcesso, EquipamentoParte,
                               HostnameIP, Rack, Rede, Servidor,
                               ServidorHostnameIP,
                               StorageGrupoAcessoMontagem)
from apps.infra.views import (CriarServidorView, DataCenterJSONView,
                              DataCenterMapView, DataCenterRackDetailView, DataCenterMapEditView,
                              DataCenterView, RackDetailView, RackQRCodeView, DataCenterPredioView,
                              RackServerDetailView, OcorrenciaNewView)
from apps.core.tests.base import *

pytestmark = pytest.mark.django_db


@pytest.fixture
@pytest.mark.django_db
def rack() -> Rack:
    predio = mixer.blend(Predio, linhas=40, colunas=40, sensores=16, predio_sistema="CPT")
    rack = mixer.blend(Rack, posicao_linha_inicial="AX" , posicao_linha_final="BA", posicao_coluna_inicial=38, posicao_coluna_final=38, consumo=1000, kvm_posicao=10, predio=predio)
    rack.save()
    return rack

@pytest.fixture
@pytest.mark.django_db
def responsavel() -> Colaborador:
    responsavel = mixer.blend(Colaborador, first_name="Responsavel", last_name="Fulano de tal", externo=False, email="teste.reponsavel@inpe.br")
    responsavel.username = None
    responsavel.clean()
    responsavel.groups.add(Group.objects.get(name="Responsavel"))
    responsavel.save()
    return responsavel


def test_criar_servidor_error_view(superuser, grupo_trabalho, responsavel_grupo):
    responsavel_grupo_trabalho = mixer.blend(ResponsavelGrupoTrabalho, grupo=grupo_trabalho, responsavel=responsavel_grupo)
    responsavel_grupo_trabalho.save()

    rede = mixer.blend(Rede, rede="rede", ip='192.168.0', id=2)
    hostnameip = mixer.blend(HostnameIP, hostname='server1', ip='192.168.0.2', tipo=rede)
    hostnameip.save()

    servidor = mixer.blend(Servidor, nome='server1', descricao="Servidor de TESTE")
    servidor.save()
    servidor_host = mixer.blend(ServidorHostnameIP, servidor=servidor, hostnameip=hostnameip)
    servidor_host.save()

    request = RequestFactory().get(reverse("infra:criar_servidor", kwargs={"pk": servidor.pk}))
    request = message_middleware(request)
    request.user = superuser
    response = CriarServidorView.as_view()(request, pk=servidor.pk)
    assert response.status_code == 302
    assert FreeIPA(request).host_find_count(fqdn=servidor.freeipa_name) == 0


def test_criar_servidor_view(superuser, grupo_trabalho, responsavel_grupo):

    rede = mixer.blend(Rede, rede="rede", ip='192.168.0', prioridade_montagem=1)
    mixer.blend(StorageGrupoAcessoMontagem, ip='192.168.0.1', parametro='-fstype=nfs4,rw', tipo='OPERACIONAL', montagem="/dados/teste", namespace="/oper/dados/teste", automount="auto.grupo" , rede=rede, grupo_trabalho=grupo_trabalho).save()
    mixer.blend(StorageGrupoAcessoMontagem, ip='192.168.0.1', parametro='-fstype=nfs4,rw', tipo='OPERACIONAL', montagem="/scripts/teste", namespace="/oper/scripts/teste", automount="auto.grupo", rede=rede, grupo_trabalho=grupo_trabalho).save()
    mixer.blend(StorageGrupoAcessoMontagem, ip='192.168.0.1', parametro='-fstype=nfs4,rw', tipo='OPERACIONAL', montagem="/log/teste", namespace="/oper/log/teste", automount="auto.grupo", rede=rede, grupo_trabalho=grupo_trabalho).save()
    mixer.blend(StorageGrupoAcessoMontagem, ip='192.168.0.5', parametro='-fstype=nfs4,rw', tipo='OPERACIONAL', montagem="/share/teste", namespace="/share/teste", automount="auto.grupo", rede=rede, grupo_trabalho=grupo_trabalho).save()
    mixer.blend(StorageGrupoAcessoMontagem, ip='192.168.0.2', parametro='-fstype=nfs4,ro', tipo='OPERACIONAL', montagem="/oper", namespace="/oper", automount="auto.oper", rede=rede).save()
    mixer.blend(StorageGrupoAcessoMontagem, ip='192.168.0.6', parametro='-fstype=nfs4,ro', tipo='OPERACIONAL', montagem="/oper/share", namespace="/share", automount="auto.oper", rede=rede).save()
    mixer.blend(StorageGrupoAcessoMontagem, ip='192.168.0.10', parametro='-fstype=nfs4,rw', tipo='OPERACIONAL', montagem="*", namespace="/HOME/&", automount="auto.home",rede=rede).save()

    responsavel_grupo_trabalho = mixer.blend(ResponsavelGrupoTrabalho, grupo=grupo_trabalho, responsavel=responsavel_grupo)
    responsavel_grupo_trabalho.save()
    grupo_trabalho.gid = 9000
    grupo_trabalho.desenvolvimento = True
    grupo_trabalho.operacional = True
    grupo_trabalho.save_confirm()

    hostnameip = mixer.blend(HostnameIP, hostname='server1', ip='192.168.0.2', tipo=rede)
    hostnameip.save()

    servidor = mixer.blend(Servidor, nome='server1', descricao="Servidor de TESTE")
    servidor.save()
    servidor_host = mixer.blend(ServidorHostnameIP, servidor=servidor, hostnameip=hostnameip)
    servidor_host.save()

    request = RequestFactory().get(reverse("infra:criar_servidor", kwargs={"pk": servidor.pk}))
    request = message_middleware(request)
    request.user = superuser

    freeipa = FreeIPA(request) 
    freeipa.set_grupo(grupo_trabalho)
    history_core = HistoryCore(request)
    history_core.update_grupo_acesso(grupo=grupo_trabalho, assunto="Nova conta de Grupo de Trabalho")
    UpdateGrupoAcesso(client_feeipa=freeipa, history_core=history_core).update_acesso(grupo_trabalho)

    grupo_acesso_dev = GrupoAcesso.objects.filter(grupo_trabalho__id=grupo_trabalho.id, tipo='DESENVOLVIMENTO')
    assert grupo_acesso_dev.exists() == True
    equipamento_grupo_acesso = mixer.blend(EquipamentoGrupoAcesso, equipamento=servidor.equipamento_ptr, grupo_acesso=grupo_acesso_dev[0])
    equipamento_grupo_acesso.save()

    grupo_acesso_oper = GrupoAcesso.objects.filter(grupo_trabalho__id=grupo_trabalho.id, tipo='OPERACIONAL')
    assert grupo_acesso_oper.exists() == True
    equipamento_grupo_acesso = mixer.blend(EquipamentoGrupoAcesso, equipamento=servidor.equipamento_ptr, grupo_acesso=grupo_acesso_oper[0])
    equipamento_grupo_acesso.save()

    response = CriarServidorView.as_view()(request, pk=servidor.pk)
    assert response.status_code == 302

    assert freeipa.host_find_count(fqdn=servidor.freeipa_name) == 1
    assert freeipa.automountlocation_find_count(cn=servidor.freeipa_name_mount) == 1
    assert freeipa.automountmap_find_count(automountlocationcn=servidor.freeipa_name_mount, automountmapname=grupo_acesso_oper[0].automountmap) == 1
    assert freeipa.automountkey_find_count(automountlocationcn=servidor.freeipa_name_mount, automountmapautomountmapname=grupo_acesso_oper[0].automountmap) == 4
    assert freeipa.automountkey_find_count(automountlocationcn=servidor.freeipa_name_mount, automountmapautomountmapname='auto.oper') == 2
    assert freeipa.automountkey_find_count(automountlocationcn=servidor.freeipa_name_mount, automountmapautomountmapname='auto.home') == 1
    assert freeipa.hbacrule_show(cn=grupo_acesso_oper[0].hbac_freeipa)['result']['memberhost_host'] == ['server1.cptec.inpe.br']

    grupos_acesso = GrupoAcesso.objects.filter(grupo_trabalho__id=grupo_trabalho.pk)
    for grupoacesso  in grupos_acesso: 
        assert freeipa.hbacrule_delete(grupoacesso.hbac_freeipa)
    assert freeipa.remove_grupo(grupo_trabalho) == True
    assert freeipa.host_delete(servidor.freeipa_name) == True
    assert freeipa.automountlocation_del(servidor.freeipa_name_mount) == True
    assert HostnameIP.objects.get(pk=hostnameip.pk).reservado == False


def test_data_center_view(rack):
    request = RequestFactory().get(reverse("infra:datacenter"))
    response = DataCenterView.as_view()(request)
    assert response.status_code == 200

def test_data_center_predio_view(rack):
    servidor = mixer.blend(Servidor, name='server1', rack=rack)
    servidor.save()
    request = RequestFactory().get(reverse("infra:datacenter_predio", kwargs={"pk": rack.predio.pk}))
    response = DataCenterPredioView.as_view()(request, pk=rack.predio.pk)
    assert response.status_code == 200


def test_data_center_map_edit_view(rack):
    request = RequestFactory().get(reverse("infra:datacenter_map_edit", kwargs={"pk": rack.pk}))
    response = DataCenterMapEditView.as_view()(request, pk=rack.pk)
    assert response.status_code == 200


def test_data_center_map_insert_view():
    predio = mixer.blend(Predio, linhas=40, colunas=40, areas='(2,4,2,4)')
    request = RequestFactory().get(reverse("infra:datacenter_map", kwargs={"pk": predio.pk}))
    response = DataCenterMapView.as_view()(request, pk=predio.pk)
    assert response.status_code == 200


def test_datacenter_search(rack):
    servidor = mixer.blend(Servidor, nome='server1', rack=rack)
    servidor.save()
    request = RequestFactory().get(reverse("infra:datacenter_search"))
    request.GET._mutable = True
    request.GET['search']='server3'
    response_None = DataCenterJSONView.as_view()(request)
    assert response_None.status_code == 200
    assert response_None.content == b'[]'
    request.GET['search']='server1'
    response_OK = DataCenterJSONView.as_view()(request)
    assert response_OK.content == b'["div[data-element=\\"#rack_1\\"]"]'
    assert response_OK.status_code == 200


def test_rack_qrcode_view(rack):
    request = RequestFactory().get(reverse("infra:rack_qrcode", kwargs={"pk": rack.pk}))
    response = RackQRCodeView.as_view()(request, pk=rack.pk)
    assert response.status_code == 200


def test_rack_qrcode_detail_view(rack):
    request = RequestFactory().get(reverse("infra:rack_detail", kwargs={"pk": rack.pk}))
    response = RackDetailView.as_view()(request, pk=rack.pk)
    assert response.status_code == 200


def test_rack_server_detail_view():
    servidor = mixer.blend(Servidor)
    request = RequestFactory().get(reverse("infra:rack_server_detail", kwargs={"pk": servidor.pk}))
    response = RackServerDetailView.as_view()(request, pk=servidor.pk)
    assert response.status_code == 200


def test_ocorrencia_new_view(rack):
    equipamento = mixer.blend(Equipamento, rack=rack)
    equipamento.save()
    data = {"equipamento": equipamento.id, "descricao": "Teste de ocorrencia"}
    request = RequestFactory().post(reverse("infra:ocorrencia_criar"), data=data)
    response = OcorrenciaNewView.as_view()(request, data=data)
    assert response.status_code == 302


def test_rack_detail_view(rack):
    equipamento_parte = mixer.blend(EquipamentoParte, marca='HP', modelo='GEN 10', patrimonio="10", rack=rack, consumo=10)
    equipamento_parte.save()
    request = RequestFactory().get(reverse("infra:datacenter_rack_detail"))
    request.GET._mutable = True
    request.GET['pk']=rack.pk
    request.GET['search']='GEN'
    response = DataCenterRackDetailView.as_view()(request)
    assert response.status_code == 200


