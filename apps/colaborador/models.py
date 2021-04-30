from datetime import datetime, timedelta, date
import re
from unicodedata import normalize
from django.contrib.auth.models import AbstractUser
from django.db import models
from apps.core.models import GrupoPortal


class Vinculo(models.Model):
    vinculo = models.CharField("vínculo", max_length=255)

    class Meta:
        ordering = ["vinculo"]
        verbose_name = "Vínculo"
        verbose_name_plural = "Vínculos"

    def __str__(self):
        return self.vinculo


class Colaborador(AbstractUser):
    telefone = models.CharField("telefone", max_length=255)
    data_nascimento = models.DateField("Data de Nascimento", max_length=255)
    documento = models.CharField("Documento", max_length=255)
    documento_tipo = models.CharField("Tipo Documento", max_length=255)
    cpf = models.CharField("CPF", max_length=255, blank=True, null=True)
    predio = models.ForeignKey("core.Predio", verbose_name="Prédio", null=True, blank=True, on_delete=models.PROTECT)
    data_inicio = models.DateField("Data de Início")
    data_fim = models.DateField("Data de Fim", null=True, blank=True)
    ramal = models.CharField("Ramal", max_length=255, null=True, blank=True)
    empresa = models.CharField("Empresa Terceirizada", max_length=255, blank=True, null=True)
    registro_inpe = models.CharField("Matrícula SIAPE", max_length=255, null=True, blank=True)
    externo = models.BooleanField("Usuário Externo", default=False)
    uid = models.IntegerField("UID", default=0)
    is_active = models.BooleanField('ativo', default=False)
    vinculo = models.ForeignKey("colaborador.Vinculo", verbose_name="vínculo", on_delete=models.PROTECT)
    divisao = models.ForeignKey('core.Divisao', verbose_name="Divisão | Coordenação", on_delete=models.PROTECT)
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

    def chefia_aprovar(self):
        self.is_staff = True
        self.save()

    def suporte_criar(self):
        self.is_active = True
        self.groups.add(GrupoPortal.objects.get(name="Colaborador"))
        self.save()

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class VPN(models.Model):
    recurso = models.CharField('Recurso a ser acessado', max_length=255 )
    data_solicitacao = models.DateField('Data da solicitação', auto_now_add=True, null=True, blank=True)
    data_abertura = models.DateField('Data da Abertura', null=True, blank=True)
    data_validade = models.DateField('Data Validade', null=True, blank=True)
    mac_cabeado = models.CharField('MAC Address Cabeado', max_length=255 ,null=True, blank=True)
    mac_wifi = models.CharField('MAC Address Wireless', max_length=255, null=True, blank=True)
    justificativa = models.CharField('Justificativa', max_length=255 )
    status = models.CharField('Status', default='Solicitada', max_length=255, null=True, blank=True)
    local =  models.CharField('Local de trabalho',  max_length=255, null=True, blank=True)
    colaborador = models.ForeignKey("colaborador.Colaborador", verbose_name="Colaborador", on_delete=models.PROTECT)
    class Meta :
        ordering = ['-data_validade']
        verbose_name = "VPN"
        verbose_name_plural = "VPNs"

    def __str__(self):
        recurso = self.recurso.split(" | ")
        return f"{self.colaborador.username} | {recurso[0]}"

    @property
    def data_fim_vpn(self):
        if self.data_validade:
            if self.data_validade <= datetime.now() + timedelta(days=365):
                return self.data_validade
        else:
            return datetime.now() + timedelta(days=365)

    @property
    def get_mac_cabeado(self):
        if self.mac_cabeado: 
            return self.mac_cabeado
        else:
            return  "___:___:___:___:___"

    @property
    def get_mac_wifi(self):
        if self.mac_wifi: 
            return self.mac_wifi
        else:
            return  "___:___:___:___:___"

    @property
    def get_local(self):
        if self.local: 
            return self.local
        else:
            return  "________________________________"

    @property
    def status_atualizado(self):
        if self.data_validade  < date.today():
            return "Vencida"
        elif self.data_validade > date.today() - timedelta(days=30) :
            return "Vai vencer"
        else:
            return self.status