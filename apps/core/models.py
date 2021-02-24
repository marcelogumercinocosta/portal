import datetime

from django.contrib.auth.models import Group
from django.db import models
from apps.core.managers import ColaboradorGrupoAcessoManager, DivisaoManager, GrupoAcessoManager, GrupoTrabalhoManager, ResponsavelGrupoTrabalhoManager


class Predio(models.Model):
    predio = models.CharField("Prédio", null=True, max_length=255)
    predio_sistema = models.CharField("Abreviação", null=True, max_length=255, unique=True)
    linhas = models.IntegerField(default=0)
    colunas = models.IntegerField(default=0)
    sensores = models.IntegerField(default=0, help_text="Número de sensores no datacenter")
    areas = models.CharField("Areas neutras", max_length=255, null=True, blank=True, help_text="Conjunto de areas neutras no mapa: (1, 36, 1, 19)/(36, 43, 1, 4)/(43, 46, 1, 30)")

    class Meta:
        verbose_name = "Prédio"
        verbose_name_plural = "Prédios"
        ordering = ["predio"]

    def __str__(self):
        return self.predio

    def get_areas(self):
        areas = []
        if self.areas:
            for area in self.areas.replace("(", "").replace(")", "").split("/"):
                areas.append(area.split(","))
        return areas


class Divisao(models.Model):
    divisao = models.CharField("divisão", max_length=255)
    divisao_completo = models.CharField("Nome Completo", max_length=255, null=True, blank=False)
    email = models.EmailField(null=True, max_length=255)
    coordenacao = models.CharField("Coordenação", max_length=255, null=True, blank=False)
    chefe = models.ForeignKey('colaborador.Colaborador', verbose_name="Chefe", null=True, blank=True, related_name="chefe_user", on_delete=models.PROTECT)
    chefe_ativo = models.BooleanField("Ativo", default=False, blank=True, null=True)
    chefe_substituto = models.ForeignKey('colaborador.Colaborador', verbose_name="Chefe Substituto", null=True, blank=True, related_name="chefe_user_2", on_delete=models.PROTECT)
    chefe_substituto_ativo = models.BooleanField("Ativo", default=False, blank=True, null=True)

    objects = DivisaoManager()

    class Meta:
        ordering = ["divisao"]
        verbose_name = "Divisão"
        verbose_name_plural = "Divisões"

    def __str__(self):
        return self.divisao

    @property
    def color(self):
        cor = ["green", "red", "blue", "orange", "lime", "teal", "brown"]
        return cor[self.id - 1]

    def emails_to(self):
        emails = [self.email]
        if self.chefe_ativo:
            emails.append(self.chefe.email)
        if self.chefe_substituto_ativo:
            emails.append(self.chefe_substituto.email)
        return emails


class GrupoTrabalho(models.Model):
    grupo = models.CharField("Grupo", max_length=255)
    grupo_sistema = models.CharField("Grupo no sistema", max_length=255, unique=True)
    gid = models.IntegerField(default=0)
    share = models.BooleanField("Share", default=False, blank=True, null=True)
    operacional = models.BooleanField("Operacional", default=False, blank=True, null=True)
    desenvolvimento = models.BooleanField("Desenvolvimento", default=False, blank=True, null=True)
    pesquisa = models.BooleanField("Pesquisa", default=False, blank=True, null=True)
    documento = models.BooleanField("Documento", default=False, blank=True, null=True)
    data_criado = models.DateField("Data de Criação", null=True)
    confirmacao = models.BooleanField("Confirmação de Assinatura", default=False, null=True)
    divisao = models.ForeignKey("core.Divisao", verbose_name="Divisão", on_delete=models.PROTECT)
    responsavel = models.ManyToManyField("colaborador.Colaborador", verbose_name="Responsável", through="ResponsavelGrupoTrabalho")
    objects = GrupoTrabalhoManager()

    class Meta:
        ordering = [
            "divisao",
            "grupo",
        ]
        verbose_name = "Grupo de Trabalho"
        verbose_name_plural = "Grupos de Trabalho"

    def __str__(self):
        return f"{self.divisao} | {self.grupo.upper()}"

    def get_sudo(self):
        return f"sudo_{self.grupo_sistema}"

    def save(self, *args, **kwargs):
        self.confirmacao = False
        return super().save(*args, **kwargs)

    def save_confirm(self, *args, **kwargs):
        self.confirmacao = True
        return super().save(*args, **kwargs)


class GrupoAcesso(models.Model):
    grupo_acesso = models.CharField("Regra de Acesso", max_length=255)
    hbac_freeipa = models.CharField("HBAC no FreeIPA", max_length=255)
    tipo = models.CharField("tipo", max_length=255)
    data = models.DateTimeField(auto_now_add=True)
    grupo_trabalho = models.ForeignKey("core.GrupoTrabalho", on_delete=models.PROTECT)
    tipos = {"OPERACIONAL": "oper", "DESENVOLVIMENTO": "dev", "PESQUISA": "pesq", "DOCUMENTO": "doc"}
    objects = GrupoAcessoManager()

    class Meta:
        verbose_name = "Grupo de Acesso"
        verbose_name_plural = "Grupos de Acesso"
        ordering = [
            "grupo_acesso",
        ]

    def __str__(self):
        return self.grupo_acesso

    def __init__(self, id=None, grupo_acesso=None, hbac_freeipa=None, tipo=None, grupo_trabalho_id=None, data=None, grupo_trabalho=None):
        super().__init__(id, grupo_acesso, hbac_freeipa, tipo, grupo_trabalho_id, data)
        if grupo_trabalho:
            self.tipo = tipo.upper()
            self.grupo_trabalho = grupo_trabalho
            self.grupo_acesso = f"{grupo_trabalho.grupo_sistema.upper()} | {self.tipo}"
            self.hbac_freeipa = f"hbac_srv_{grupo_trabalho.grupo_sistema}_{self.tipos[self.tipo]}"

    @property
    def description(self):
        info = self.grupo_acesso.split(" | ")
        return f"HBAC Rule de {info[1]} do Grupo {info[0]}"

    @property
    def automountmap(self):
        return f"auto.{self.grupo_trabalho.grupo_sistema}_{self.tipos[self.tipo]}"


class GrupoPortal(Group):
    class Meta:
        proxy = True
        verbose_name = "Grupo no Portal"
        verbose_name_plural = "Grupos no Portal"


class ResponsavelGrupoTrabalho(models.Model):
    responsavel = models.ForeignKey("colaborador.Colaborador", verbose_name="Responsável", on_delete=models.CASCADE)
    grupo = models.ForeignKey("core.GrupoTrabalho", on_delete=models.CASCADE)
    objects = ResponsavelGrupoTrabalhoManager()

    class Meta:
        ordering = ["responsavel"]
        verbose_name = "Responsável"
        verbose_name_plural = "Responsáveis"

    def __str__(self):
        return f"{self.responsavel.full_name} | {self.grupo.grupo}"


class ColaboradorGrupoAcesso(models.Model):
    colaborador = models.ForeignKey("colaborador.Colaborador", on_delete=models.CASCADE)
    grupo_acesso = models.ForeignKey("core.GrupoAcesso", on_delete=models.CASCADE)
    aprovacao = models.IntegerField("status", default=0)
    atualizacao = models.DateTimeField("Data de Atualização", auto_now=True)
    objects = ColaboradorGrupoAcessoManager()

    class Meta:
        ordering = ["grupo_acesso"]
        verbose_name = "Grupo de Acesso"
        verbose_name_plural = "Grupos de Acesso"
    
    def __str__(self):
        return self.grupo_acesso.grupo_acesso

    def status(self):
        if self.aprovacao == 1:
            return "Acesso Aprovado"
        return "Aguardando Aprovação"

