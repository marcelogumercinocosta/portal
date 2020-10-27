import pytest
from django.contrib.auth.models import AnonymousUser, Group, Permission, User
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.core.exceptions import ValidationError
from django.http import Http404
from django.test import RequestFactory
from django.urls import reverse
from mixer.backend.django import mixer
from apps.infra.models import Storage, StorageAreaGrupoTrabalho, StorageArea, AmbienteVirtual, Servidor, Supercomputador
from apps.core.models import Divisao, GrupoTrabalho
from apps.monitoramento.models.storage import Area, StorageHistorico, QuotaUtilizada
from apps.monitoramento.views.monitoramento import FerramentaView
from apps.monitoramento.views.storage import NetappView, NetappLisView, XE6QuotaView, XE6QuotaListView, NetappModelView
from apps.monitoramento.views.vm import XenView, XenPoolView, XenPoolListView
from apps.monitoramento.views.uso import SupercomputadorView, SupercomputadorNodesView, SupercomputadorHistView
from django.conf import settings
import datetime
import os

pytestmark = pytest.mark.django_db


def test_monitoramento_view():
    request = RequestFactory().get(reverse("monitoramento:ferramentas"))
    response = FerramentaView.as_view()(request)
    assert response.status_code == 200

def test_monitoramento_netapp_view():
    request = RequestFactory().get(reverse("monitoramento:storage_netapp"))
    response = NetappView.as_view()(request)
    assert response.status_code == 200

def test_monitoramento_netapp_model_view():
    storage = mixer.blend(Storage, marca='Netapp', modelo='8040', id=4 , atualizacao=datetime.datetime.now() )
    divisao = mixer.blend(Divisao, divisao='TESTE')
    grupo = mixer.blend(GrupoTrabalho, grupo="Grupo dados", grupo_sistema="dados", divisao=divisao)
    storage_area = mixer.blend(StorageArea, storage=storage, area="/disco", capacidade=100)
    storage_area_grupo_trabalho = mixer.blend(StorageAreaGrupoTrabalho, quota=10, storage_area=storage_area, grupo=grupo)
    area = mixer.blend(Area, storage_grupo_trabalho=storage_area_grupo_trabalho)
    request = RequestFactory().get(reverse("monitoramento:storage_netapp_model", kwargs={"pk": storage.id}))
    response = NetappModelView.as_view()(request, pk=storage.pk)
    assert response.status_code == 200

    storage_historico = mixer.blend(StorageHistorico, storage_grupo_trabalho=storage_area_grupo_trabalho, atualizacao=datetime.datetime.now(), disco_used=1)
    request = RequestFactory().get(reverse("monitoramento:storage_netapp_list", kwargs={"pk": grupo.id}))
    response = NetappLisView.as_view()(request, pk=grupo.pk)
    assert response.status_code == 200

def test_monitoramento_netapp_error_storage_area_view():
    storage = mixer.blend(Storage, marca='Netapp', modelo='8040', id=4 , atualizacao=datetime.datetime.now() )
    divisao = mixer.blend(Divisao, divisao='TESTE')
    grupo = mixer.blend(GrupoTrabalho, grupo="Grupo dados", grupo_sistema="dados", divisao=divisao)
    
    request = RequestFactory().get(reverse("monitoramento:storage_netapp_list", kwargs={"pk": grupo.id}))
    response = NetappLisView.as_view()(request, pk=grupo.pk)
    assert response.status_code == 200


def test_monitoramento_netapp_error_index_area_view():
    storage = mixer.blend(Storage, marca='Netapp', modelo='8040', id=4 , atualizacao=datetime.datetime.now() )
    divisao = mixer.blend(Divisao, divisao='TESTE')
    grupo = mixer.blend(GrupoTrabalho, grupo="Grupo dados", grupo_sistema="dados", divisao=divisao)
    storage_area = mixer.blend(StorageArea, storage=storage, area="/disco", capacidade=100)
    storage_area_grupo_trabalho = mixer.blend(StorageAreaGrupoTrabalho, quota=10, storage_area=storage_area, grupo=grupo)
    request = RequestFactory().get(reverse("monitoramento:storage_netapp_list", kwargs={"pk": grupo.id}))
    response = NetappLisView.as_view()(request, pk=grupo.pk)
    assert response.status_code == 200


def test_quota_view():
    storage = mixer.blend(Storage, marca='Netapp', modelo='8040', id=5 , atualizacao=datetime.datetime.now() )
    request = RequestFactory().get(reverse("monitoramento:storage_xe6quota"))
    response = XE6QuotaView.as_view()(request)
    assert response.status_code == 200


def test_quota_list_view():
    storage = mixer.blend(Storage, marca='Netapp', modelo='8040', id=5 , atualizacao=datetime.datetime.now() )
    divisao = mixer.blend(Divisao, divisao='TESTE')
    grupo = mixer.blend(GrupoTrabalho, grupo="Grupo dados", grupo_sistema="dados", divisao=divisao)
    storage_area = mixer.blend(StorageArea, storage=storage, area="/disco", capacidade=100)
    storage_area_grupo_trabalho = mixer.blend(StorageAreaGrupoTrabalho, quota=10, storage_area=storage_area, grupo=grupo)
    quota = mixer.blend(QuotaUtilizada, storage_grupo_trabalho=storage_area_grupo_trabalho, quota=10, usado=5)
    request = RequestFactory().get(reverse("monitoramento:storage_xe6quota_list", kwargs={"pk": grupo.id}))
    response = XE6QuotaListView.as_view()(request, pk=grupo.pk)
    assert response.status_code == 200


def test_vm_xen_view():
    request = RequestFactory().get(reverse("monitoramento:vms_xen"))
    response = XenView.as_view()(request)
    assert response.status_code == 200


def test_vm_xen_pool_view():
    ambiente = mixer.blend(AmbienteVirtual)
    request = RequestFactory().get(reverse("monitoramento:vms_xen_pool", kwargs={"pk": ambiente.pk}))
    response = XenPoolView.as_view()(request, pk=ambiente.pk)
    assert response.status_code == 200


def test_vm_xen_list_view():
    settings.XEN_AUTH_USER = os.environ["XEN_AUTH_USER"]
    settings.XEN_AUTH_PASSWORD = os.environ["XEN_AUTH_PASSWORD"]
    servidores = os.environ["XEN_SERVIDORES_TEST"]
    ambiente = mixer.blend(AmbienteVirtual)
    for servidor in servidores.split(','):
        ambiente.servidor.add(mixer.blend(Servidor, nome=servidor))
    ambiente.save()
    request = RequestFactory().get(reverse("monitoramento:vms_xen_pool", kwargs={"pk": ambiente.pk}))
    response = XenPoolListView.as_view()(request, pk=ambiente.pk)
    assert response.status_code == 200


def test_uso_supercomputador_view():
    request = RequestFactory().get(reverse("monitoramento:uso_supercomputador"))
    response = SupercomputadorView.as_view()(request)
    assert response.status_code == 200

def test_uso_supercomputador_nodes_view():
    supercomputador = mixer.blend(Supercomputador, kafka_topico_realtime="xc50_nodes", kafka_topico_historico="xc50_hist")
    request = RequestFactory().get(reverse("monitoramento:uso_supercomputador_nodes", kwargs={"pk": supercomputador.pk}))
    response = SupercomputadorNodesView.as_view()(request, pk=supercomputador.pk)
    assert response.status_code == 200


def test_uso_supercomputador_nodes_error_view():
    supercomputador = mixer.blend(Supercomputador, kafka_topico_realtime="_nodes", kafka_topico_historico="xc50_hist")
    request = RequestFactory().get(reverse("monitoramento:uso_supercomputador_nodes", kwargs={"pk": supercomputador.pk}))
    response = SupercomputadorNodesView.as_view()(request, pk=supercomputador.pk)
    assert response.status_code == 200

def test_uso_supercomputador_hist_error_view():
    supercomputador = mixer.blend(Supercomputador, kafka_topico_realtime="xc50_nodes", kafka_topico_historico="_hist")
    request = RequestFactory().get(reverse("monitoramento:uso_supercomputador_hist", kwargs={"pk": supercomputador.pk}))
    response = SupercomputadorHistView.as_view()(request, pk=supercomputador.pk)
    assert response.status_code == 200

def test_uso_supercomputador_hist_view():
    supercomputador = mixer.blend(Supercomputador, kafka_topico_realtime="xc50_nodes", kafka_topico_historico="xc50_hist")
    request = RequestFactory().get(reverse("monitoramento:uso_supercomputador_hist", kwargs={"pk": supercomputador.pk}))
    response = SupercomputadorHistView.as_view()(request, pk=supercomputador.pk)
    assert response.status_code == 200