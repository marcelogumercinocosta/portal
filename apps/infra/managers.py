from django.db import models
from django.db.models import Sum


class StorageAreaManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("storage").prefetch_related("storageareagrupotrabalho_set")

    def aggregate_storage_sum(self):
        return super().get_queryset().values("storage_id").annotate(Sum("capacidade"))


class StorageAreaGrupoTrabalhoManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("grupo", "storage_area", "storage_area__storage","grupo__divisao")

    def aggregate_divisao_quota_sum(self):
        return super().get_queryset().values("grupo__divisao_id", "storage_area__storage_id").annotate(Sum("quota"))

    def aggregate_all_quota_sum(self):
        return super().get_queryset().values("storage_area__storage_id").annotate(Sum("quota"))


class EquipamentoManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().prefetch_related("grupos_acesso").select_related('servidor')

class ServidorManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("equipamento_ptr","equipamento_ptr__grupos_acesso").prefetch_related('servidorhostnameip_set','nagios_servicos')

class EquipamentoGrupoAcessoManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("equipamento","equipamento__servidor")


class SupercomputadorManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("equipamento_ptr").prefetch_related("ocorrencia_set")

class StorageManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("equipamento_ptr").prefetch_related("storagearea_set","ocorrencia_set")

class EquipamentoParteManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("equipamento_ptr").prefetch_related("ocorrencia_set")

class HostnameIPManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("tipo")


class ServidorNagiosServicoManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("servidor", "servidor__equipamento_ptr", "servidor__equipamento_ptr__grupos_acesso").prefetch_related("nagios_servico")


class OcorrenciaServicoManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("equipamento","checklist")