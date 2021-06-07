from django.db import models


class GrupoTrabalhoManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("divisao").prefetch_related("responsavelgrupotrabalho_set", "grupoacesso_set","storageareagrupotrabalho_set")


class ResponsavelGrupoTrabalhoManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("responsavel")


class GrupoAcessoManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().prefetch_related("grupo_trabalho","equipamentogrupoacesso_set")


class DivisaoManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset()

class ColaboradorGrupoAcessoManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("colaborador")