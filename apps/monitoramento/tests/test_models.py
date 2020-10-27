import datetime
import time

import pytest
from mixer.backend.django import mixer

from apps.core.models import Divisao, GrupoAcesso, GrupoTrabalho
from apps.monitoramento.models import Area, StorageHistorico, QuotaUtilizada, QuotaUtilizadaLista, Prometheus, TipoMonitoramento, Monitoramento, SupercomputadorRack, SupercomputadorNode, SupercomputadorHistorico
from apps.infra.models import StorageAreaGrupoTrabalho, StorageArea
from django.core.exceptions import ValidationError

pytestmark = pytest.mark.django_db


def test_area() -> None:
    area = mixer.blend(Area, area="vol_dmz_divisao_grupo_oper_grupo" )
    assert str(area) == "vol_dmz_divisao_grupo_oper_grupo"


def test_storage_historico() -> None:
    area_historico = mixer.blend(StorageHistorico)
    area_historico.atualizacao = datetime.date.today() 
    assert str(area_historico) == str(datetime.date.today() )


def test_quotautilizada() -> None:
    divisao = mixer.blend(Divisao, divisao='TESTE')
    grupo = mixer.blend(GrupoTrabalho, grupo="Grupo dados", grupo_sistema="dados", divisao=divisao)
    storage_area =  mixer.blend(StorageArea, area="/disco")
    storage_area_grupo_trabalho =  mixer.blend(StorageAreaGrupoTrabalho, storage_area=storage_area, grupo=grupo)

    quota_utilizada = mixer.blend(QuotaUtilizada, limite=100, quota=0 , usado=0, storage_grupo_trabalho=storage_area_grupo_trabalho)
    assert quota_utilizada.porcentagem() == 0
    quota_utilizada.quota = 80
    quota_utilizada.usado = 40
    assert quota_utilizada.porcentagem() == 50
    assert quota_utilizada.area() == "/disco"


def test_quotautilizadalista() -> None:
    divisao = mixer.blend(Divisao, divisao='TESTE')
    grupo = mixer.blend(GrupoTrabalho, grupo="Grupo dados", grupo_sistema="dados", divisao=divisao)
    storage_area =  mixer.blend(StorageArea, area="/disco")
    storage_area_grupo_trabalho =  mixer.blend(StorageAreaGrupoTrabalho, storage_area=storage_area, grupo=grupo)
    quota_utilizada = mixer.blend(QuotaUtilizada, limite=100, quota=0 , usado=0, storage_grupo_trabalho=storage_area_grupo_trabalho)
    quota_utilizada_lista = mixer.blend(QuotaUtilizadaLista, quota_utilizada=quota_utilizada, tipo='U')
    assert quota_utilizada_lista.get_tipo() == "Usuário" 
    quota_utilizada_lista1 = mixer.blend(QuotaUtilizadaLista, quota_utilizada=quota_utilizada, tipo='G')
    assert quota_utilizada_lista1.get_tipo() == "Grupo" 

def test_prometheus() -> None:
    prometheus = mixer.blend(Prometheus, jobname='job')
    assert str(prometheus) == 'job'

def test_tipomonitoramento() -> None:
    tipo = mixer.blend(TipoMonitoramento, nome='Externo')
    assert str(tipo) == 'Externo'

def test_monitoramento() -> None:
    monitoramento = mixer.blend(Monitoramento, nome='RNP')
    assert str(monitoramento) == 'RNP'


def test_supercomputador() -> None:
    supercomputador_rack = SupercomputadorRack("rack1")
    assert str(supercomputador_rack) == "rack1"

    supercomputador_node_1 = SupercomputadorNode({'rack': 'C2-0', 'chassis': 'c0', 'slot': 'n2', 'posicao': 'p5', 'status': 'c', 'usuario': 'user.p', 'comando': 'fcst_zhao.', 'size': '54', 'tempo': '3h14m'})
    assert str(supercomputador_node_1) == 'c0:n2:p5'
    assert supercomputador_node_1.get_classe_html() == "processing"
    supercomputador_node_2 = SupercomputadorNode({'rack': 'C2-1', 'chassis': 'c0', 'slot': 'n1', 'posicao': 'p2', 'status': 'S', 'usuario': '', 'comando': '', 'size': '', 'tempo': ''})
    assert supercomputador_node_2.get_classe_html() == "service"
    

    supercomputador_rack.add_no(supercomputador_node_1)
    supercomputador_rack.add_no(supercomputador_node_2)
    assert len(supercomputador_rack.nos) == 2

    supercomputador_hist_1 = SupercomputadorHistorico({'update': 1603152301, 'jobs': 27, 'service': 39, 'free_batch': 201, 'admindown': 0, 'waiting': 0, 'free': 0, 'down': 23, 'running': 489, 'suspect': 0, 'noexist': 0, 'allocated_interactive': 16})
    assert supercomputador_hist_1.get_services() == 39
    assert supercomputador_hist_1.get_downs() == 23
    assert supercomputador_hist_1.get_used() == 489 + 16 + 0 + 39
    assert supercomputador_hist_1.get_frees() == 201
    assert supercomputador_hist_1.get_total() == 39 + 23 + 489 + 16 + 0 + 39 + 201
    assert supercomputador_hist_1.get_used_percent() == ((489 + 16 + 0 + 39) *100)/ (39 + 23 + 489 + 16 + 0 + 39 + 201)
    assert supercomputador_hist_1.get_down_percent() == ((23)*100)/ (39 + 23 + 489 + 16 + 0 + 39 + 201)
    assert supercomputador_hist_1.get_last() == '19/10 21:05'
    assert supercomputador_hist_1.get_alerta() == ["lighten-3", "grey", "red"]
    assert supercomputador_hist_1.get_alerta_time() ==  "alert_time red"
    assert supercomputador_hist_1.get_ok() == False

    supercomputador_hist_2 = SupercomputadorHistorico({'update': time.time(),'jobs':1})
    assert supercomputador_hist_2.get_used_percent() == 0
    assert supercomputador_hist_2.get_down_percent() == 0
    assert supercomputador_hist_2.get_alerta() == ["darken-4", "", "brown"]
    assert supercomputador_hist_2.get_alerta_time() ==  "blue" 
    assert supercomputador_hist_2.get_ok() == True