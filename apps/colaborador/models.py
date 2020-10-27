import re
from datetime import datetime
from unicodedata import normalize

from django.contrib.auth.models import User
from django.db import models
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.functional import cached_property

from apps.core.models import Divisao, Group, Predio


class Vinculo(models.Model):
    vinculo = models.CharField("vinculo", max_length=255)

    class Meta:
        ordering = ["vinculo"]
        verbose_name = "Vínculo"
        verbose_name_plural = "Vínculos"

    def __str__(self):
        return self.vinculo


class Colaborador(User):
    telefone = models.CharField("telefone", max_length=255)
    data_nascimento = models.DateField(max_length=255, verbose_name="Data de Nascimento")
    documento = models.CharField(max_length=255, verbose_name="Documento")
    documento_tipo = models.CharField(max_length=255, verbose_name="Tipo Documento")
    cpf = models.CharField(max_length=255, blank=True, null=True, verbose_name="CPF")
    bairro = models.CharField(max_length=255)
    cidade = models.CharField(max_length=255)
    cep = models.CharField(max_length=255, verbose_name="CEP")
    endereco = models.CharField(max_length=255, verbose_name="Endereço")
    numero = models.CharField(max_length=255, verbose_name="Número")
    estado = models.CharField(max_length=255)
    predio = models.ForeignKey(Predio, verbose_name="Prédio", null=True, on_delete=models.PROTECT)
    data_inicio = models.DateField("Data de Início")
    data_fim = models.DateField("Data de Fim", null=True, blank=True)
    ramal = models.CharField("Ramal", max_length=255, null=True)
    contato_de_emergencia_nome = models.CharField(max_length=255, null=True, verbose_name="Nome")
    contato_de_emergencia_telefone = models.CharField(max_length=255, null=True, verbose_name="Telefone")
    contato_de_emergencia_parentesco = models.CharField(max_length=255, null=True, verbose_name="Parentesco")
    nacionalidade = models.CharField(max_length=255)
    sexo = models.CharField(max_length=255, null=True)
    area_formacao = models.CharField(max_length=255, verbose_name="Área de Formação")
    empresa = models.CharField(max_length=255, blank=True, null=True, verbose_name="Empresa Terceirizada")
    registro_inpe = models.CharField(max_length=255, null=True, blank=True, verbose_name="Matrícula SIAPE")
    estado_civil = models.CharField(max_length=255, blank=True, null=True)
    externo = models.BooleanField("Usuário Externo", default=False)
    uid = models.IntegerField("UID", default=0)
    vinculo = models.ForeignKey(Vinculo, verbose_name="vínculo", on_delete=models.PROTECT)
    divisao = models.ForeignKey(Divisao, verbose_name="Divisão", on_delete=models.PROTECT)
    responsavel = models.ForeignKey("self", null=True, blank=True, verbose_name="Responsavel", related_name="responsavel_user", on_delete=models.PROTECT)

    class Meta:
        ordering = ["username"]
        verbose_name = "Colaborador"
        verbose_name_plural = "Colaboradores"
        permissions = (
            ("responsavel_colaborador", "Responsável pode aprovar acesso colaborador"),
            ("secretaria_colaborador", "Secretaria pode revisar colaborador"),
            ("suporte_colaborador", "Suporte pode criar o colaborador"),
            ("chefia_colaborador", "Chefia por aprovar colaborador"),
        )

    def __create_user_name(self, name, id_last_name=1):
        nome_corrigido = re.sub(r"\ d[aeiou]\ ", " ", normalize("NFKD", name).encode("ASCII", "ignore").decode("ASCII")).split(" ")
        username = nome_corrigido[0] + "." + nome_corrigido[id_last_name * -1]
        if id_last_name == len(nome_corrigido):
            return nome_corrigido[0] + "." + nome_corrigido[-1] + "_"
        if Colaborador.objects.filter(username=username.lower()).exists():
            id_last_name += 1
            username = self.__create_user_name(name, id_last_name)
        return username

    def __set_user_name(self):
        name = f"{self.first_name} {self.last_name}"
        # Verifica Email do INPE
        if "@inpe.br" in self.email:
            return self.email.replace("@inpe.br", "").lower()
        return self.__create_user_name(name).lower()

    def get_documento_principal(self):
        if self.cpf is None:
            return f"{self.documento_tipo}: <b>{self.documento}</b>"
        return f"CPF: <b>{self.cpf}</b>"

    def clean(self):
        from django.core.exceptions import ValidationError

        if not self.username:
            self.username = self.__set_user_name()
        if Colaborador.objects.filter(username=self.username).exclude(id=self.pk).exists():
            raise ValidationError({"email": ("Username já existe")})
        if Colaborador.objects.filter(email=self.email).exclude(id=self.pk).exists():
            raise ValidationError({"email": ("Email já existe")})
        super().clean()

    def save(self, *args, **kwargs):
        if not self.pk:
            self.is_active = False
        super(Colaborador, self).save(*args, **kwargs)

    def chefia(self):
        self.is_active = True
        self.save()

    def suporte(self):
        self.is_staff = True
        self.groups.add(Group.objects.get(name="Colaborador"))
        self.save()

    @cached_property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Conta(Colaborador):
    class Meta:
        proxy = True
        verbose_name = "Conta"
        verbose_name_plural = "Contas"

