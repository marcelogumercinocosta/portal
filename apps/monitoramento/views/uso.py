from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from django.core.exceptions import EmptyResultSet
from django.shortcuts import get_object_or_404
from django.views.generic.base import TemplateView
from pykafka.exceptions import KafkaException, NoBrokersAvailableError

from apps.infra.models import Supercomputador
from apps.monitoramento.models import (SupercomputadorHistorico,
                                       SupercomputadorNode,
                                       SupercomputadorRack)
from apps.monitoramento.utils import (AxisBase, AxisData, Echarts, Grid, Kafka,
                                      LineArea, Tooltip)
from garb.views import ViewContextMixin


class SupercomputadorView(ViewContextMixin, TemplateView):
    template_name = "monitoramento/uso/supercomputador.html"
    title = "Supercomputadores Jobs e Nodes"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        supercomputadores = Supercomputador.objects.all()
        context["supercomputadores"] = supercomputadores
        return context


class SupercomputadorNodesView(TemplateView):
    template_name = "monitoramento/uso/supercomputador_nodes.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        supercomputador = get_object_or_404(Supercomputador, id=kwargs["pk"])
        try:
            kafka_client_nodes = Kafka(supercomputador.kafka_topico_realtime, 1)
            nodes_bruto = kafka_client_nodes.get_kafka_topic()[0]
            supercomputador.set_update(nodes_bruto["update"])
            racks_bruto = np.unique(np.array([x["rack"] for x in nodes_bruto["nodes"]]))
            for rack_nome in racks_bruto:
                rack = SupercomputadorRack(rack_nome)
                for node_bruto in [x for x in nodes_bruto["nodes"] if x["rack"] == rack_nome]:
                    node = SupercomputadorNode(node_bruto)
                    rack.add_no(node)
                supercomputador.add_rack(rack)
            context["supercomputador"] = supercomputador
            context["users"] = np.unique(np.array([x["usuario"] for x in nodes_bruto["nodes"]]))
        except (RuntimeError, TypeError, NameError, IndexError, EmptyResultSet,  KafkaException, NoBrokersAvailableError):
            context["supercomputador"] = None
            context["users"] = None
        return context


class SupercomputadorHistView(TemplateView):
    template_name = "monitoramento/uso/supercomputador_hist.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        supercomputador = get_object_or_404(Supercomputador, id=kwargs["pk"])
        try:
            kafka_client_historico = Kafka(supercomputador.kafka_topico_historico, 290)
            kafka_client_historico.get_kafka_topic_last()
            nodes_bruto = kafka_client_historico.get_kafka_topic()
            context["grafico"] = self.get_grafico_historico(pd.DataFrame(nodes_bruto))
            context["numero"] = SupercomputadorHistorico(nodes_bruto[-1])
            context["supercomputador"] = supercomputador
            return context
        except (RuntimeError, TypeError, NameError, IndexError, KafkaException, NoBrokersAvailableError) as e:
            context["grafico"] = None
            context["numero"] = None
            context["supercomputador"] = None
        return context

    def get_grafico_historico(self, df_nodes_bruto):
        # corrigindo a data de timestamp para datetime
        df_nodes_bruto["atualizacao"] = pd.to_datetime(df_nodes_bruto["update"], unit="s")
        df_nodes_bruto["atualizacao"] = df_nodes_bruto["atualizacao"].apply(lambda x: x.replace(second=0))
        # somando as colunas
        df_nodes_bruto["service"] = df_nodes_bruto["service"] + df_nodes_bruto["admindown"] + df_nodes_bruto["suspect"]
        df_nodes_bruto["running"] = df_nodes_bruto["running"] + df_nodes_bruto["allocated_interactive"] + df_nodes_bruto["waiting"]
        df_nodes_bruto["free"] = df_nodes_bruto["free"] + df_nodes_bruto["free_batch"]
        # removevendo as colunas sem uso
        df_nodes_bruto = df_nodes_bruto.loc[:, ["atualizacao", "service", "running", "free", "down", "jobs"]]
        # Cria Eixo X dos Ultimos 6 Horas
        last_time = df_nodes_bruto["atualizacao"].iloc[-1]
        dti = pd.DataFrame({"atualizacao": pd.date_range(start=(last_time - timedelta(hours=24)).strftime("%Y-%m-%d %H:%M:00"), end=last_time)}).fillna(0)
        # Merge dos date + data
        serie = pd.merge_ordered(dti, df_nodes_bruto).fillna(0)
        grafico = Echarts()
        grafico.set_color(["red", "#ffa726", "green", "#0277bd"])
        x_axis = AxisData("category", "bottom", [x.strftime("%H:%M") for x in pd.to_datetime(serie["atualizacao"], format="T")])
        x_axis.set_axis_label({"rotate": 45, "textStyle": {"fontSize": 8}})
        grafico.add_x_axis(x_axis)
        y_axis = AxisBase("value")
        y_axis.set_max((serie["service"] + serie["down"] + serie["running"] + serie["free"]).max())
        grafico.add_y_axis(y_axis)
        grafico.add_series(LineArea("down", (serie["down"]).tolist()))
        grafico.add_series(LineArea("service", serie["service"].tolist()))
        grafico.add_series(LineArea("running", (serie["running"]).tolist()))
        grafico.add_series(LineArea("free", (serie["free"]).tolist()))
        grafico.set_tooltip(Tooltip())
        grafico.set_grid(Grid())
        return grafico
