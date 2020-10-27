# -*- coding: utf-8 -*-
from django.db import models
from apps.infra.models import StorageAreaGrupoTrabalho, Storage
from apps.monitoramento.managers import StorageHistoricoManager, AreaManager, QuotaManager


class Area(models.Model):
    area = models.CharField(max_length=255, default="Volume")
    snap = models.DecimalField(verbose_name="Snap", max_digits=20, decimal_places=2)
    porcentagem_snap = models.IntegerField(verbose_name="Snap (%)")
    snapshot_autodelete = models.CharField(max_length=50, blank=True, null=True)
    snapshot_size_used = models.IntegerField(verbose_name="Snap Usado (%)")
    snapshot_policy = models.CharField(max_length=255, blank=True, null=True)
    total_disco = models.DecimalField(max_digits=20, decimal_places=2)
    disco = models.DecimalField(max_digits=20, decimal_places=2)
    disco_used = models.DecimalField(max_digits=20, decimal_places=2)
    porcentagem_disco_used = models.DecimalField(max_digits=20, decimal_places=0)
    path = models.CharField(max_length=255, blank=True, null=True)
    node = models.CharField(max_length=255, blank=True, null=True)
    aggregate = models.CharField(max_length=255, blank=True, null=True)
    export_policy = models.CharField(max_length=255, blank=True, null=True)
    deduplication = models.DecimalField(verbose_name="Snap", max_digits=20, decimal_places=2, null=True)
    porcentagem_deduplication = models.CharField(max_length=255, blank=True, null=True)
    svm_name = models.CharField(max_length=255, blank=True, null=True)
    storage_grupo_trabalho = models.ForeignKey(StorageAreaGrupoTrabalho, on_delete=models.CASCADE)
    objects = AreaManager()

    def __str__(self):
        return self.area


class StorageHistorico(models.Model):
    disco_used = models.DecimalField(max_digits=20, decimal_places=2)
    storage_grupo_trabalho = models.ForeignKey(StorageAreaGrupoTrabalho, on_delete=models.CASCADE)
    atualizacao = models.DateTimeField("Atualização", blank=True, null=True)
    objects = StorageHistoricoManager()

    def __str__(self):
        return str(self.atualizacao)


class QuotaUtilizada(models.Model):
    limite = models.DecimalField(verbose_name="Limite", max_digits=20, decimal_places=0, blank=True, null=True)
    quota = models.DecimalField(verbose_name="Quota", max_digits=20, decimal_places=0, blank=True, null=True)
    usado = models.DecimalField(verbose_name="Usado", max_digits=20, decimal_places=0, blank=True, null=True)
    storage_grupo_trabalho = models.OneToOneField(StorageAreaGrupoTrabalho, on_delete=models.CASCADE)
    objects = QuotaManager()

    def area(self):
        return self.storage_grupo_trabalho.storage_area.area

    def porcentagem(self):
        if self.usado == 0 or self.quota == 0:
            return 0
        return int(self.usado * 100 / self.quota)


class QuotaUtilizadaLista(models.Model):
    tipo = models.CharField(max_length=50, blank=True, null=True)
    conta = models.CharField(max_length=50, blank=True, null=True)
    usado = models.DecimalField(verbose_name="Usado", max_digits=20, decimal_places=0, blank=True, null=True)
    detalhe = models.CharField(max_length=50, blank=True, null=True)
    quota_utilizada = models.ForeignKey(QuotaUtilizada, on_delete=models.CASCADE)

    def get_tipo(self):
        if self.tipo == "U":
            return "Usuário"
        else:
            return "Grupo"
