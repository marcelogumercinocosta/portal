from django.contrib.auth.models import Group
from django.db import models
from django.utils import timezone
from apps.core.managers import GrupoTrabalhoManager, ResponsavelGrupoTrabalhoManager, GrupoAcessoManager, DivisaoManager, ColaboradorGrupoAcessoManager
from django.contrib.auth.models import User
import datetime

class Predio(models.Model):
    predio = models.CharField("Prédio", null=True, max_length=255)
    predio_sistema = models.CharField("Abreviação", null=True, max_length=255, unique=True)
    linhas = models.IntegerField(default=0)
    colunas = models.IntegerField(default=0)
    sensores = models.IntegerField(default=0, help_text='Número de sensores no datacenter')
    areas = models.CharField("Areas neutras", max_length=255, null=True, blank=True,)

    class Meta :
        verbose_name = "Prédio"
        verbose_name_plural = "Prédios"
        ordering = ['predio']

    def __str__(self):
        return self.predio

    def get_areas(self):
        quadros = []
        if self.areas:
            for quadro in self.areas.replace("(","").replace(")","").split("/"):
                quadros.append(quadro.split(","))
        return quadros

class Divisao(models.Model):
    divisao = models.CharField("divisão", max_length=255)
    email = models.EmailField( null=True, max_length=255)
    chefe = models.ForeignKey(User, verbose_name='Chefe', null=True, related_name='chefe_user', on_delete=models.PROTECT)
    chefe_ativo = models.BooleanField('Chefe Ativo', default=False, blank=True, null=True)
    chefe_substituto = models.ForeignKey(User, verbose_name='Chefe Substituto',  null=True, related_name='chefe_user_2', on_delete=models.PROTECT)
    chefe_substituto_ativo = models.BooleanField('Chefe Substituto Ativo', default=False, blank=True, null=True)
    objects = DivisaoManager()

    class Meta:
        verbose_name = "Divisão"
        verbose_name_plural = "Divisões"
        ordering = ["divisao"]

    @property
    def color(self):
        cor = ["green", "red", "blue", "orange", "lime", "teal", "brown"]
        return cor[self.id - 1]

    def emails(self):
        emails = [self.email]
        if self.chefe_ativo:
            emails.append(self.chefe.email)
        if self.chefe_substituto_ativo:
            emails.append(self.chefe_substituto.email)
        return emails

    def __str__(self):
        return self.divisao

from apps.colaborador.models import Colaborador


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
    divisao = models.ForeignKey(Divisao, verbose_name="Divisão", on_delete=models.PROTECT)
    confirmacao = models.BooleanField("Confirmação de Assinatura", default=False, null=True)
    responsavel = models.ManyToManyField(Colaborador, verbose_name="Responsável", through="ResponsavelGrupoTrabalho")
    objects = GrupoTrabalhoManager()

    class Meta:
        ordering = [
            "divisao",
            "grupo",
        ]
        verbose_name = "Grupo de Trabalho"
        verbose_name_plural = "Grupos de Trabalho"

    def get_sudo(self):
        return f"sudo_{self.grupo_sistema}"

    def save(self, *args, **kwargs):
        self.confirmacao = False
        return super().save(*args, **kwargs)

    def save_confirm(self, *args, **kwargs):
        self.confirmacao = True
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.divisao} | {self.grupo.upper()}"


class GrupoAcesso(models.Model):
    grupo_acesso = models.CharField("Regra de Acesso", max_length=255)
    hbac_freeipa = models.CharField("HBAC no FreeIPA", max_length=255)
    tipo = models.CharField("tipo", max_length=255)
    data = models.DateTimeField(default=timezone.now)
    grupo_trabalho = models.ForeignKey(GrupoTrabalho, on_delete=models.PROTECT)
    tipos = {"OPERACIONAL": "oper", "DESENVOLVIMENTO": "dev", "PESQUISA": "pesq", "DOCUMENTO": "doc"}
    objects = GrupoAcessoManager()

    class Meta:
        verbose_name = "Grupo de Acesso"
        verbose_name_plural = "Grupos de Acesso"
        ordering = [
            "grupo_acesso",
        ]

    def __init__(self, id=None,  grupo_acesso=None, hbac_freeipa=None,  tipo=None, grupo_trabalho_id=None, data=None, grupo_trabalho=None):
        super().__init__(id, grupo_acesso, hbac_freeipa, tipo, grupo_trabalho_id, data)
        if grupo_trabalho:
            self.tipo = tipo.upper()
            self.grupo_trabalho = grupo_trabalho
            self.grupo_acesso = f"{grupo_trabalho.grupo_sistema.upper()} | {self.tipo}"
            self.hbac_freeipa = f"hbac_srv_{grupo_trabalho.grupo_sistema}_{self.tipos[self.tipo]}"

    @property
    def description(self):
        info = self.grupo_acesso.split(" | ");
        return f"HBAC Rule de {info[1]} do Grupo {info[0]}"

    @property
    def automountmap(self):
        return f"auto.{self.grupo_trabalho.grupo_sistema}_{self.tipos[self.tipo]}"

    def save(self, *args, **kwargs):
        self.data = datetime.datetime.now()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.grupo_acesso


class GrupoPortal(Group):
    class Meta:
        proxy = True
        verbose_name = "Grupo no Portal"
        verbose_name_plural = "Grupos no Portal"


class ResponsavelGrupoTrabalho(models.Model):
    from apps.colaborador.models import Colaborador

    responsavel = models.ForeignKey(Colaborador, verbose_name="Responsável", on_delete=models.CASCADE)
    grupo = models.ForeignKey(GrupoTrabalho, on_delete=models.CASCADE)
    objects = ResponsavelGrupoTrabalhoManager()

    class Meta:
        ordering = ["responsavel"]
        verbose_name = "Responsável"
        verbose_name_plural = "Responsáveis"

    def __str__(self):
        return f"{self.responsavel.full_name} | {self.grupo.grupo}"


class ColaboradorGrupoAcesso(models.Model):
    colaborador = models.ForeignKey(Colaborador, on_delete=models.CASCADE)
    grupo_acesso = models.ForeignKey(GrupoAcesso, on_delete=models.CASCADE)
    aprovacao = models.IntegerField("status", default=0)
    atualizacao = models.DateTimeField("Data de Atualização", null=True)
    objects = ColaboradorGrupoAcessoManager()

    class Meta:
        ordering = ["grupo_acesso"]
        verbose_name = "Grupo de Acesso"
        verbose_name_plural = "Grupos de Acesso"

    def status(self):
        if self.aprovacao == 1:
            return "Acesso Aprovado"
        return "Aguardando Aprovação"
    
    def save(self, *args, **kwargs):
        self.atualizacao = timezone.now()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.grupo_acesso.grupo_acesso