from django.db import models
from django.db.models import Avg, Count, Sum


class AreaManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("storage_grupo_trabalho")

    def aggregate_grupo_disco_sum(self):
        return super().get_queryset().values("storage_grupo_trabalho_id").annotate(Sum("disco_used"), Sum("disco"))

    def aggregate_divisao_disco_sum(self):
        return super().get_queryset().values("storage_grupo_trabalho__grupo__divisao_id").annotate(Sum("disco_used"), Sum("disco"))

    def aggregate_all_snap_disco_used_deduplication_sum(self):
        return super().get_queryset().aggregate(Sum("snap"), Sum("disco"), Sum("disco_used"), Sum("deduplication"), Count("area"))

    def distinct_id_divisoes(self):
        return super().get_queryset().values("storage_grupo_trabalho__grupo__divisao__id").all().distinct()
    
    def distinct_id_storages(self):
        return super().get_queryset().values("storage_grupo_trabalho__storage_area__storage__id").all().distinct()



class QuotaManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("storage_grupo_trabalho")

    def aggregate_grupo_quota_sum(self):
        return super().get_queryset().values("storage_grupo_trabalho__storage_area__storage_id", "storage_grupo_trabalho__grupo_id").annotate(Sum("usado"), Sum("quota"))

    def aggregate_all_quotado_used_sum(self):
        return super().get_queryset().aggregate(Sum("quota"), Sum("usado"), Count("id"))


class StorageHistoricoManager(models.Manager):
    def aggregate_grupo_historico_disco_sum(self):
        return super().get_queryset().values("storage_grupo_trabalho_id", "atualizacao").annotate(Avg("disco_used"))

class NagiosServicosManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().prefetch_related("servidor_set")