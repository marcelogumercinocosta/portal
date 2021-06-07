import math
from datetime import datetime, timedelta
import pandas as pd
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.views.generic.base import TemplateView
from sklearn.linear_model import LinearRegression

from apps.core.models import Divisao, GrupoTrabalho
from apps.monitoramento.utils import Echarts, AxisData, AxisBase, Tooltip, Line, Grid
from apps.infra.models import Storage, StorageAreaGrupoTrabalho
from apps.monitoramento.models import (Area, QuotaUtilizada, StorageHistorico)
from garb.views import ViewContextMixin



class TotalStorageView(ViewContextMixin, TemplateView):
    template_name = "monitoramento/storage/total_storage.html"
    title = "Total de Armazenamento por Storage"

    def get_context_data(self, **kwargs):
        storages = Storage.objects.all()
        context = super(TotalStorageView, self).get_context_data(**kwargs)
        context["storages"] = storages
        return context

class TotalGrupoView(ViewContextMixin, TemplateView):
    template_name = "monitoramento/storage/total_grupo.html"
    title = "Total de Armazenamento por Grupo de Trabalho"

    def get_context_data(self, **kwargs):
        grupos = GrupoTrabalho.objects.all()
        context = super(TotalGrupoView, self).get_context_data(**kwargs)
        context["grupos"] = grupos
        return context

class ArmazenamentoView(ViewContextMixin, TemplateView):
    template_name = "monitoramento/storage/armazenamento.html"
    title = "ARMAZENAMENTO"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        storages_das_areas = [divisao['storage_grupo_trabalho__storage_area__storage__id'] for divisao in Area.objects.distinct_id_storages()] 
        context["storages"] = Storage.objects.filter(pk__in=storages_das_areas)
        return context


class NetappModelView(TemplateView):
    template_name = "monitoramento/storage/netapp_model.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # consulta o Netapp Atenção no Id
        storage = get_object_or_404(Storage, id=kwargs["pk"])
        divisoes = []
        divisoes_das_areas = [divisao['storage_grupo_trabalho__grupo__divisao__id'] for divisao in Area.objects.distinct_id_divisoes()]
        # Lista as divisoes
        for divisao in Divisao.objects.filter(pk__in=divisoes_das_areas):
            # Consulta agregada na tabela de Areas buscando discos por divisao  filtrada pelo ID da divisao
            areas_divisao = Area.objects.aggregate_divisao_disco_sum().filter(storage_grupo_trabalho__grupo__divisao_id=divisao.id)[0]
            # Consulta agregada na tabela de StorageAreas buscando quota por divisao  filtrada pelo ID da divisao
            quota_divisao = StorageAreaGrupoTrabalho.objects.aggregate_divisao_quota_sum().filter(grupo__divisao_id=divisao.id, storage_area__storage_id=storage.id)[0]
            quota_total_kb = quota_divisao["quota__sum"] * 1024 * 1024 * 1024 * 1024
            area_total_usado_porcentagem = int((areas_divisao["disco_used__sum"] * 100) / quota_total_kb)
            area_total_liberado_porcentagem = int((areas_divisao["disco__sum"] * 100) / quota_total_kb) - area_total_usado_porcentagem
            divisoes.append(
                {
                    "obj": divisao,
                    "area_total_usado": areas_divisao["disco_used__sum"],
                    "area_total_liberado": areas_divisao["disco__sum"],
                    "quota_total": quota_total_kb,
                    "area_total_usado_porcentagem": area_total_usado_porcentagem,
                    "area_total_liberado_porcentagem": area_total_liberado_porcentagem,
                }
            )
        context["title"] = f'{storage.marca} {storage.modelo}'.upper()
        context["quotado"] = StorageAreaGrupoTrabalho.objects.aggregate_all_quota_sum().filter(storage_area__storage_id=storage.id)[0]["quota__sum"] * 1024 * 1024 * 1024 * 1024
        area_total = Area.objects.aggregate_all_snap_disco_used_deduplication_sum()
        context["reserva_utilizada"] = area_total["snap__sum"]
        context["liberado"] = area_total["disco__sum"]
        context["utilizado"] = area_total["disco_used__sum"]
        context["deduplicacao"] = area_total["deduplication__sum"]
        context["volumes"] = area_total["area__count"]
        context["divisoes"] = divisoes
        context["storage"] = storage
        return context


class NetappLisView(TemplateView):
    template_name = "monitoramento/storage/netapp_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        storage = get_object_or_404(Storage, id=4)
        grupo = get_object_or_404(GrupoTrabalho, id=kwargs["pk"])
        try:
            storage_area_grupo_trabalho = StorageAreaGrupoTrabalho.objects.get(storage_area__storage_id=storage.id, grupo_id=grupo.id)
            try:
                combined_alerts = Area.objects.filter((Q(porcentagem_disco_used__gte=95) | Q(snapshot_size_used__gte=95)), storage_grupo_trabalho_id=storage_area_grupo_trabalho.id)
                total_areas = Area.objects.aggregate_grupo_disco_sum().filter(storage_grupo_trabalho_id=storage_area_grupo_trabalho.id)[0]
                storage_area_grupo_trabalho.area_total_usado = int(total_areas["disco_used__sum"])
                storage_area_grupo_trabalho.area_total_liberado = int(total_areas["disco__sum"])
                pandas_df_areahistorico_grupo_30d = pd.DataFrame(
                    list(StorageHistorico.objects.aggregate_grupo_historico_disco_sum().filter(storage_grupo_trabalho_id=storage_area_grupo_trabalho.id, atualizacao__gte=datetime.now()  - timedelta(days=30)))
                )
                context["storage_area_grupo_trabalho_previsao_30d"] = self.get_previsao_30d(pandas_df_areahistorico_grupo_30d)
                context["storage_area_grupo_trabalho_grafico_historico"] = self.get_grafico_historico(pandas_df_areahistorico_grupo_30d)
                context["combined_alerts"] = len(combined_alerts)
            except IndexError:
                storage_area_grupo_trabalho.area_total_usado = 0
                storage_area_grupo_trabalho.area_total_liberado = 0
        except ObjectDoesNotExist:
            storage_area_grupo_trabalho = StorageAreaGrupoTrabalho()
            storage_area_grupo_trabalho.grupo = grupo
            storage_area_grupo_trabalho.area_total_usado = 0
            storage_area_grupo_trabalho.area_total_liberado = 0
        context["title"] = grupo.grupo
        context["storage_area_grupo_trabalho"] = storage_area_grupo_trabalho
        return context

    def get_grafico_historico(self, df_area_historico):
        size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
        # iniciliza configuracoes do matplotlib
        # Define tamanho para legenda
        size_indice = df_area_historico.disco_used__avg.max()
        size = size_name[int(math.floor(math.log(size_indice, 1024)))]
        # Transformas os tamanhos de KB para tamanho Human
        df_area_historico["disco_used__avg"] = df_area_historico.disco_used__avg.apply(lambda x: round(int(x) / float(math.pow(1024, int(math.floor(math.log(size_indice, 1024))))), 2))
        # Cria Eixo X dos Ultimos 30 dias
        dti = pd.DataFrame({"atualizacao": pd.date_range((datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"), periods=30, freq="D")})
        # Merge dos date + data
        serie = pd.merge_ordered(dti, df_area_historico).dropna()

        grafico = Echarts()
        grafico.set_color(["#0277bd"])
        x_axis = AxisData("category", "bottom", [x.strftime("%d/%m") for x in pd.to_datetime(serie["atualizacao"], format="T")])
        x_axis.set_axis_label({"rotate": 45, "textStyle": {"fontSize": 8}})
        grafico.add_x_axis(x_axis)
        y_axis = AxisBase("value")
        y_axis.set_min((serie["disco_used__avg"]).min() - 0.01)
        y_axis.set_max((serie["disco_used__avg"]).max() + 0.01)
        grafico.add_y_axis(y_axis)
        grafico.add_series(Line("Utilizado %s" % size, (serie["disco_used__avg"]).tolist()))
        grafico.set_tooltip(Tooltip())
        grafico.set_grid(Grid())
        return grafico

    def get_previsao_30d(self, df_area_historico):
        model = LinearRegression()
        X = df_area_historico.atualizacao.apply(lambda x: x.toordinal()).values.reshape(-1, 1)
        y = df_area_historico.disco_used__avg.values.reshape(-1, 1)
        model.fit(X, y)
        futuro = (datetime.now() + timedelta(days=30)).toordinal()
        return  model.predict([[futuro]])


class XE6QuotaView(TemplateView):
    template_name = "monitoramento/storage/xe6_quota.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # consulta o Netapp Atenção no Id
        storage = get_object_or_404(Storage, id=5)
        # Consulta agregada na tabela de StorageAreas buscando quota por divisao  filtrada pelo ID da divisao
        storage_area_grupo_trabalhos = StorageAreaGrupoTrabalho.objects.filter(storage_area__storage_id=storage.id)
        grupos = [x.grupo for x in storage_area_grupo_trabalhos]
        context["title"] = "XE6 Quota"
        context["grupos"] = sorted(grupos, key=lambda x: (x.divisao.divisao, x.grupo))
        context["storage"] = storage
        total_quota_storage = QuotaUtilizada.objects.aggregate_all_quotado_used_sum()
        context["quotado"] = total_quota_storage["quota__sum"]
        context["utilizado"] = total_quota_storage["usado__sum"]
        context["quotas"] = total_quota_storage["id__count"]
        return context


class XE6QuotaListView(TemplateView):
    template_name = "monitoramento/storage/xe6_quota_list.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        storage = get_object_or_404(Storage, id=5)
        grupo = get_object_or_404(GrupoTrabalho, id=kwargs["pk"])
        quota_utilizadas = QuotaUtilizada.objects.filter(storage_grupo_trabalho__storage_area__storage_id=storage.id, storage_grupo_trabalho__grupo_id=grupo.id)
        total_quotas = QuotaUtilizada.objects.aggregate_grupo_quota_sum().filter(storage_grupo_trabalho__storage_area__storage_id=storage.id, storage_grupo_trabalho__grupo_id=grupo.id)[0]
        storage_area_grupo_trabalho = StorageAreaGrupoTrabalho()
        storage_area_grupo_trabalho.grupo = grupo
        storage_area_grupo_trabalho.area_total_usado = total_quotas["usado__sum"]
        storage_area_grupo_trabalho.quota = total_quotas["quota__sum"] / 1024 / 1024 / 1024 / 1024  # quota dividida devido ajuste storage_grupo_trabalho
        context["title"] = grupo.grupo
        context["storage_area_grupo_trabalho"] = storage_area_grupo_trabalho
        context["quota_utilizadas"] = quota_utilizadas

        grupo = get_object_or_404(GrupoTrabalho, id=kwargs["pk"])
        return context
