
import json
import matplotlib.cm as cm
import matplotlib.colors as colors
import matplotlib.pyplot as plt
import numpy as np
import scipy.interpolate as inter
from datetime import datetime
from apps.infra.models import (LINHAS, Equipamento, EquipamentoParte, Rack, Rede, Servidor)
from django.conf import settings
from django.db.models import Q
from paho.mqtt import client, subscribe


class DatacenterSensor:
    temperatura = 0
    umidade = 0
    posicao_grid = 0
    atualizacao = 0
    tipo = None
    predio = None

    def get_status(self):
        if self.temperatura > 28 or (self.umidade < 30 or self.umidade > 60):
            return "red"
        elif self.temperatura > 25 or (self.umidade < 40 or self.umidade > 55):
            return "yellow"
        else:
            return "blue"

    def get_col(self):
        return self.posicao_grid[1]

    def get_index(self):
        return LINHAS.index(self.posicao_grid[0])
    
    def get_posicao_numerico(self):
        return [self.posicao_grid[1],self.get_index()]

    def __init__(self, predio, posicao_grid, tipo, umidade=0, temperatura=0, atualizacao=0):
        self.temperatura = temperatura
        self.umidade = umidade
        self.posicao_grid = posicao_grid
        self.tipo = tipo
        self.predio = predio
        self.atualizacao = atualizacao

    def __str__(self):
        return f"{self.predio}{self.posicao_grid[0]}{self.posicao_grid[1]}"


class DatacenterArea:
    posicao_linha_inicial = 0
    posicao_linha_final = 0
    posicao_coluna_inicial = 0
    posicao_coluna_final = 0
    
    @property
    def tipo(self):
        return "area_map"

    def __init__(self, pli, plf, pci, pcf):
        self.posicao_linha_inicial = pli
        self.posicao_linha_final = plf
        self.posicao_coluna_inicial = pci
        self.posicao_coluna_final = pcf


class DatacenterSensores:
    def __init__(self, predio):
        self.sensores = []
        self.datacenter_sensor = None
        self.escala = []
        self.predio = predio
        self.buscar_dados(F"area/{predio.predio_sistema}/sensor/#", predio.sensores)
        self.criar_grid()

    def criar_grid(self):
        grid_x, grid_y = np.mgrid[range(self.predio.colunas + 1 ), range(self.predio.linhas + 1 )]
        pontos_grid = np.array([x.get_posicao_numerico() for x in self.sensores])
        temperaturas = np.array([x.temperatura for x in self.sensores])
        datacenter_sensor_grid = inter.griddata(pontos_grid, temperaturas, (grid_x, grid_y), method="linear", fill_value=0)
        self.datacenter_sensor = datacenter_sensor_grid.astype(int)

    def buscar_dados(self, topic, quantidade):
        mosquitto_msg = subscribe.simple( topic, hostname=settings.MOSQUITTO_SERVER, port=int(settings.MOSQUITTO_PORT), msg_count=quantidade)
        for msg in mosquitto_msg:
            data = json.loads(msg.payload)
            self.sensores.append(DatacenterSensor(self.predio.predio_sistema, data['posicao'].split("_") , tipo=data['tipo'], umidade=data['umidade'], temperatura=data['temperatura'], atualizacao=datetime.fromtimestamp(data['update'])))

    def definir_escala(self):
        temperaturas = np.unique(self.datacenter_sensor)
        norm = colors.Normalize(vmin=np.min(10), vmax=np.max(30), clip=True)
        mapper = cm.ScalarMappable(norm=norm)
        mapper.set_cmap(cmap=plt.cm.RdBu_r)
        escala = {temperatura: ("#{:02x}{:02x}{:02x}".format(*mapper.to_rgba(temperatura, bytes=True))) for temperatura in temperaturas}
        return escala

    def matriz_datacenter(self):
        escala = self.definir_escala()
        matriz_datacenter = [[{"temperatura": self.datacenter_sensor[x][y], "escala": escala[self.datacenter_sensor[x][y]]} for x in range(self.predio.colunas + 1)] for y in range(self.predio.linhas + 1 )]
        return matriz_datacenter


class DataCenterMap:
    def __init__(self, predio, id_rack=None) :
        self.id_rack = 0
        self.sensores = []
        self.predio = predio
        self.id_rack = id_rack
        self.racks = Rack.objects.filter(predio=predio)

    def draw_datacenter(self, sensor=False):
        total_linhas = self.predio.linhas
        total_colunas = self.predio.colunas
        areas = [DatacenterArea(*[int(i) for i in area]) for area in self.predio.get_areas()]
        # Monta o piso com ou sem sensor
        if sensor and self.predio.sensores > 0:
            datacenter_sensor = DatacenterSensores(self.predio)
            self.sensores = datacenter_sensor.sensores
            matriz_datacenter = datacenter_sensor.matriz_datacenter()
        else:
            matriz_datacenter = [[0 for x in range( total_colunas + 1)] for y in range( total_linhas +1 )]
        #numera as linhas e colunas
        for coluna in range(total_colunas):
            matriz_datacenter[0][coluna] = {"index_coluna": coluna}
            matriz_datacenter[total_linhas][coluna] = {"index_coluna": coluna}
        matriz_datacenter[total_linhas][total_colunas] = {"index_coluna": "-"}
        matriz_datacenter[0][total_colunas] = {"index_coluna": "-"}
        for linha in range(total_linhas):
            matriz_datacenter[linha][0] = {"index_linha": LINHAS[linha]}
            matriz_datacenter[linha][total_colunas] = {"index_linha": LINHAS[linha]}
        matriz_datacenter[total_linhas][0] = {"index_coluna": "-"}
        matriz_datacenter[0][0] = {"index_coluna": "-"}
        # adicona os racks
        for rack in self.racks.iterator():
            for linha in range(rack.linha_inicial(), rack.linha_final() + 1):
                for coluna in range( rack.coluna_inicial(), rack.coluna_final() + 1):
                    if rack.id == self.id_rack:
                        matriz_datacenter[linha][coluna] = {"edit": "red lighten-4"}
                    else:
                        matriz_datacenter[linha][coluna] = {"rack": rack.id}
            matriz_datacenter[rack.posicao_linha_inicial_numero()][rack.posicao_coluna_inicial].update({"name": rack.posicao_linha_inicial.upper()})
            matriz_datacenter[rack.linha_nome()][rack.coluna_nome()].update({"name": rack.posicao_coluna_inicial })
        #adicona as areas fora 
        for area in areas:
            for linha in range(area.posicao_linha_inicial, area.posicao_linha_final):
                for coluna in range(area.posicao_coluna_inicial, area.posicao_coluna_final):
                    matriz_datacenter[linha][coluna] = {"area": area.tipo}
        return matriz_datacenter

class RackMap:
    def __init__(self, id_rack, search=None):
        self.id_rack = 0
        self.id_rack = id_rack
        self.search = search

    def draw_rack(self):
        rack = Rack.objects.get(pk=self.id_rack)
        tamanho = int(rack.tamanho) if rack.tamanho else 44
        # coluna de posicoes
        rack_posicoes = [x + 1 for x in range(tamanho)]
        # coluna de equipamentos
        rack_equipamentos = [x + 1 for x in range(tamanho)]
        # adicionando o equipamento na coluna de equipamentos
        equipamentos =  Equipamento.objects.filter(Q(rack=rack.pk) & (Q(tipo='Servidor Físico') | Q(tipo='Equipamento Físico'))).order_by('rack__posicao')
        for equipamento in equipamentos:
            for tamanho_posicao in range(equipamento.rack_posicao, equipamento.rack_posicao + equipamento.rack_tamanho):
                # adicionando o tamanho no equipamento
                if tamanho_posicao == equipamento.rack_posicao:
                    rack_equipamentos[tamanho_posicao - 1] = {"equipamento": equipamento}
                    if self.search and self.search.lower() in str(equipamento).lower():
                        rack_equipamentos[tamanho_posicao - 1].update({"search": "green darken-3"})
                else:
                    rack_equipamentos[tamanho_posicao - 1] = {"continuacao": equipamento.id}
            rack.comsumo_servidores += int(equipamento.consumo)
        # adicionando o kvm
        if rack.kvm_posicao:
            rack_equipamentos[rack.kvm_posicao -1 ] = {"kvm": "kvm"}
        rack.posicoes = rack_posicoes[::-1]
        rack.equipamentos = rack_equipamentos[::-1]
        return rack

