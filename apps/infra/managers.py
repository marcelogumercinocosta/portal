from django.db import models
from django.db.models import Sum


class StorageAreaManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("storage")

    def aggregate_storage_sum(self):
        return super().get_queryset().values("storage_id").annotate(Sum("capacidade"))


class StorageAreaGrupoTrabalhoManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("grupo", "storage_area")

    def aggregate_divisao_quota_sum(self):
        return super().get_queryset().values("grupo__divisao_id", "storage_area__storage_id").annotate(Sum("quota"))

    def aggregate_all_quota_sum(self):
        return super().get_queryset().values("storage_area__storage_id").annotate(Sum("quota"))


class EquipamentoManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().prefetch_related("grupos_acesso")


class EquipamentoGrupoAcessoManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("equipamento","equipamento__servidor")


class ServidorManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().prefetch_related("equipamento_ptr_id")