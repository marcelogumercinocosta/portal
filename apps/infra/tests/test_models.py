import pytest
import time
from mixer.backend.django import mixer
from datetime import datetime, timedelta
from apps.core.models import Divisao, GrupoAcesso, GrupoTrabalho, Predio
from apps.infra.models import (AmbienteVirtual,  Equipamento,
                               EquipamentoGrupoAcesso, EquipamentoParte,
                               Ocorrencia, Rack, Storage, StorageArea,
                               StorageAreaGrupoTrabalho, Supercomputador,
                               HostnameIP, ServidorHostnameIP,Rede, 
                               Servidor, Rack, EquipamentoGrupoAcesso)
from django.core.exceptions import EmptyResultSet

pytestmark = pytest.mark.django_db


def test_rack() -> None:
    predio =  mixer.blend(Predio, predio_sistema='RACK')
    rack = mixer.blend(Rack, posicao_linha_inicial="AX" , posicao_linha_final="BA", posicao_coluna_inicial=38, posicao_coluna_final=38, consumo=1000, predio=predio)
    assert rack.linha_inicial() == 24
    assert rack.linha_final() == 27
    assert rack.linha_nome() == 25
    assert rack.coluna_inicial() == 38
    assert rack.coluna_final() == 38
    assert rack.coluna_nome() == 38
    rack.comsumo_servidores = 100
    assert rack.disponivel() == 900
    rack.save()
    assert rack.rack == "RACKAX38"
    assert str(rack) == "RACKAX38"

    rack = mixer.blend(Rack, posicao_linha_inicial="AX" , posicao_linha_final="AX", posicao_coluna_inicial=38, posicao_coluna_final=40, consumo=1000)
    assert rack.linha_nome() == 24
    assert rack.coluna_nome() == 39

    rack = mixer.blend(Rack, posicao_linha_inicial="BB" , posicao_linha_final="AX", posicao_coluna_inicial=40, posicao_coluna_final=38, consumo=1000)
    assert rack.linha_nome() == 27
    assert rack.coluna_nome() == 40
    assert rack.posicao_linha_inicial_numero() == 28

    rack = mixer.blend(Rack, posicao_linha_inicial="AX" , posicao_linha_final="AX", posicao_coluna_inicial=40, posicao_coluna_final=38, consumo=1000)
    assert rack.coluna_nome() == 39


def test_ocorrencia() -> None:
    ocorrencia = mixer.blend(Ocorrencia, ocorrencia=None)
    assert ocorrencia.get_status() == "bg-danger"
    ocorrencia.ocorrencia = 100
    assert ocorrencia.get_status() == "bg-warning" 
    assert str(ocorrencia) == f"100 {ocorrencia.descricao}" 


def test_ambiente_virtual() -> None:
    ambiente_virtual = mixer.blend(AmbienteVirtual, nome='LAN', virtualizador='XEN', versao='7.0' )
    assert str(ambiente_virtual) == "LAN (XEN 7.0)" 


def test_equipamento_parte() -> None:
    equipamento_parte = mixer.blend(EquipamentoParte, marca='HP', modelo='GEN 10', patrimonio="10" )
    assert equipamento_parte.tipo == "Equipamento Físico" 
    assert str(equipamento_parte) == "Equipamento Físico - HP GEN 10" 


def test_storage_storagearea() -> None:
    storage = mixer.blend(Storage, marca='Netapp', modelo='8040')
    assert str(storage) == "Netapp 8040"
    assert storage.tipo == "Storage" 
    assert storage.capacidade() == 0
    storage.save()
    storage_area = mixer.blend(StorageArea, storage=storage, area="/disco", capacidade=100)
    storage_area.save()
    assert str(storage_area) == "Netapp 8040 - /disco"
    assert storage.capacidade() == 100
    divisao = mixer.blend(Divisao, divisao='TESTE')
    grupo = mixer.blend(GrupoTrabalho, grupo="Grupo dados", grupo_sistema="dados", divisao=divisao)
    grupo.save()
    storage_area_grupo_trabalho = mixer.blend(StorageAreaGrupoTrabalho, quota=None, storage_area=storage_area, grupo=grupo)
    assert storage_area_grupo_trabalho.area_total_liberado_porcentagem() == 0
    assert storage_area_grupo_trabalho.area_total_usado_porcentagem() == 0
    assert storage_area_grupo_trabalho.area_total_liberado_corrigido_porcentagem() == 0
    assert storage_area_grupo_trabalho.quota_KB() == 0
    storage_area_grupo_trabalho.quota = 100 
    storage_area_grupo_trabalho.area_total_usado = ( 10 * 1024 * 1024 * 1024 * 1024 )
    storage_area_grupo_trabalho.area_total_liberado = ( 50 * 1024 * 1024 * 1024 * 1024 )
    assert storage_area_grupo_trabalho.quota_KB() == ( 100 * 1024 * 1024 * 1024 * 1024 )
    assert storage_area_grupo_trabalho.area_total_usado_porcentagem() == 10
    assert storage_area_grupo_trabalho.area_total_liberado_corrigido_porcentagem() == 40
    assert storage_area_grupo_trabalho.area_total_liberado_porcentagem() == 50
    assert str(storage_area_grupo_trabalho) == "TESTE | GRUPO DADOS - Netapp 8040 - /disco"


def test_supercomputador() -> None:
    supercomputador = mixer.blend(Supercomputador, marca='Cray', modelo='CX50')
    assert supercomputador.tipo == "Supercomputador"
    assert supercomputador.racks == [] 
    assert supercomputador.update == None
    assert str(supercomputador) == "Cray CX50"
    rack = mixer.blend(Rack)
    supercomputador.add_rack(rack)
    assert len(supercomputador.racks) == 1
    supercomputador.set_update(int(time.time()))
    assert supercomputador.update == datetime.fromtimestamp(int(time.time()))
    with pytest.raises(EmptyResultSet) as excinfo:
        supercomputador.set_update(1603547701)
        assert supercomputador.update == None


def test_servidor_hostnameip() -> None:
    rede = mixer.blend(Rede, rede="rede", ip='192.168.1')
    hostnameip = mixer.blend(HostnameIP, hostname='server1', ip='192.168.1.2', tipo=rede)
    hostnameip.reservado = True 
    hostnameip.save()
    assert str(hostnameip) == "server1 | 192.168.1.2 | rede"
    servidor = mixer.blend(Servidor, nome='server1')
    assert servidor.freeipa_name == "server1.cptec.inpe.br"
    assert servidor.freeipa_name_mount == "mount_server1"
    servidor_host = mixer.blend(ServidorHostnameIP, servidor=servidor, hostnameip=hostnameip)
    servidor_host.save()
    servidor.delete()
    assert str(servidor) == 'server1'
    assert str(servidor_host) == 'server1'
    hostnameip = HostnameIP.objects.get(pk=hostnameip.id)
    assert hostnameip.reservado == False


def test_equipamento_grupo_acesso() -> None:
    grupo = mixer.blend(GrupoTrabalho, grupo="Grupo dados", grupo_sistema="dados")
    grupo_acesso = GrupoAcesso(tipo="Desenvolvimento", grupo_trabalho=grupo)
    grupo_acesso.save()
    servidor = mixer.blend(Servidor, nome='server1', descricao="TESTE DO EQUIPAMENTO", tipo="Servidor Virtual", tipo_uso='DESENVOLVIMENTO')
    assert servidor.nome_completo() == "[ SERVER1 - DESENVOLVIMENTO ] TESTE DO EQUIPAMENTO"
    equipamento_grupo_acesso = mixer.blend(EquipamentoGrupoAcesso, equipamento=servidor, grupo_acesso=grupo_acesso)
    assert str(equipamento_grupo_acesso) == "DADOS | DESENVOLVIMENTO"
    assert servidor.grupo_acesso_name() == "DADOS" 
    assert servidor.tipo_uso == "DESENVOLVIMENTO"
    assert servidor.nome_completo() == "[ SERVER1 - DADOS - DESENVOLVIMENTO ] TESTE DO EQUIPAMENTO"


def test_servidor_equipamento() -> None:
    servidor = mixer.blend(Servidor, nome='server1', marca='HP', modelo='GEN 10')
    assert str(servidor) == 'server1'
    equipamento = Equipamento.objects.get(pk=servidor.id)
    assert servidor.id == equipamento.id
    assert equipamento.nome() == 'server1'

    equipamento_parte = mixer.blend(EquipamentoParte, marca='HP', modelo='GEN 10', patrimonio="10" )
    assert equipamento_parte.tipo == "Equipamento Físico" 
    equipamento = Equipamento.objects.get(pk=equipamento_parte.id)
    assert equipamento.nome() ==  'HP GEN 10'
    assert str(equipamento) == '[ EQUIPAMENTO FÍSICO ] HP GEN 10'


def test_rede() -> None:
    rede = mixer.blend(Rede, rede="rede", ip="192.168.0")
    assert str(rede) == "rede | 192.168.0"