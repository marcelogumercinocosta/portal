from datetime import datetime, timedelta
from django.core.exceptions import NON_FIELD_ERRORS, EmptyResultSet, ObjectDoesNotExist
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from apps.infra.managers import EquipamentoManager, StorageAreaGrupoTrabalhoManager, StorageAreaManager

LINHAS = [ "-", "AA", "AB", "AC", "AD", "AE", "AF", "AG", "AH", "AI", "AJ", "AK", "AL", "AM", 
            "AN", "AO", "AP", "AQ", "AR", "AS", "AT", "AU", "AV", "AW", "AX", "AY", "AZ", "BA", 
            "BB", "BC", "BD", "BE", "BF", "BG", "BH", "BI", "BJ", "BK", "BL", "BM", "BN", "BO", 
            "BP", "BQ", "BR", "BS"]


class Rack(models.Model):
    rack = models.CharField("Rack", max_length=255)
    marca = models.CharField("Marca", max_length=255)
    modelo = models.CharField("Modelo", max_length=255)
    serie = models.CharField("Serial", max_length=255)
    patrimonio = models.CharField("Patrimônio", max_length=255)
    posicao_linha_inicial = models.CharField("Linha Inicial", max_length=2, null=True)
    posicao_linha_final = models.CharField("Linha Final", max_length=2, null=True)
    posicao_coluna_inicial = models.PositiveIntegerField("Coluna Inicial", validators=[MinValueValidator(1), MaxValueValidator(64)], null=True)
    posicao_coluna_final = models.PositiveIntegerField("Coluna Final", validators=[MinValueValidator(1), MaxValueValidator(64)], null=True)
    pdu1 = models.CharField("Primeiro PDU", max_length=255, blank=True, null=True)
    pdu2 = models.CharField("Segundo PDU", max_length=255, blank=True, null=True)
    consumo = models.IntegerField("Consumo Limite")
    tamanho = models.IntegerField("Tamanho (U)", default=44)
    kvm_posicao = models.IntegerField(verbose_name="Posição do KVM", blank=True, null=True)
    predio = models.ForeignKey("core.Predio", verbose_name="Prédio", null=True, on_delete=models.PROTECT)
    posicoes = None
    equipamentos = None
    comsumo_servidores = 0

    class Meta:
        ordering = ["predio", "posicao_linha_inicial", "posicao_coluna_inicial"]
    
    def __str__(self):
        return self.rack

    def linha_inicial(self):
        return min(LINHAS.index(self.posicao_linha_inicial), LINHAS.index(self.posicao_linha_final))

    def linha_final(self):
        return max(LINHAS.index(self.posicao_linha_inicial), LINHAS.index(self.posicao_linha_final))

    def coluna_inicial(self):
        return min(self.posicao_coluna_inicial, self.posicao_coluna_final)

    def coluna_final(self):
        return max(self.posicao_coluna_inicial, self.posicao_coluna_final)

    def posicao_linha_inicial_numero(self):
        return LINHAS.index(self.posicao_linha_inicial)

    def coluna_nome(self):
        if LINHAS.index(self.posicao_linha_inicial) != LINHAS.index(self.posicao_linha_final) and self.posicao_coluna_inicial != self.posicao_coluna_final:
            return self.posicao_coluna_inicial
        elif LINHAS.index(self.posicao_linha_inicial) == LINHAS.index(self.posicao_linha_final) and self.posicao_coluna_inicial < self.posicao_coluna_final:
            return self.posicao_coluna_inicial + 1
        elif LINHAS.index(self.posicao_linha_inicial) == LINHAS.index(self.posicao_linha_final) and self.posicao_coluna_inicial > self.posicao_coluna_final:
            return self.posicao_coluna_inicial - 1
        else:
            return self.posicao_coluna_inicial

    def linha_nome(self):
        if LINHAS.index(self.posicao_linha_inicial) == LINHAS.index(self.posicao_linha_final):
            return LINHAS.index(self.posicao_linha_inicial)
        elif LINHAS.index(self.posicao_linha_inicial) > LINHAS.index(self.posicao_linha_final):
            return LINHAS.index(self.posicao_linha_inicial) - 1
        else:
            return LINHAS.index(self.posicao_linha_inicial) + 1

    def disponivel(self):
        return int(self.consumo) - int(self.comsumo_servidores)

    def save(self, *args, **kwargs):
        self.rack = f"{self.predio.predio_sistema}{self.posicao_linha_inicial}{self.posicao_coluna_inicial}"
        super(Rack, self).save(*args, **kwargs)


class Equipamento(models.Model):
    TIPOS_USO = (
        ("", ""),
        ("OPERACIONAL", "OPERACIONAL"),
        ("DESENVOLVIMENTO", "DESENVOLVIMENTO"),
        ("PESQUISA", "PESQUISA"),
        ("DOCUMENTO", "DOCUMENTO"),
    )

    marca = models.CharField("Marca", max_length=255, null=True)
    modelo = models.CharField("Modelo", max_length=255, null=True)
    serie = models.CharField("Serial", max_length=255, null=True)
    patrimonio = models.CharField("Patrimônio", max_length=255, null=True)
    descricao = models.CharField("Descrição", max_length=255, null=True)
    garantia = models.CharField("Garantia", max_length=255, null=True, blank=True)
    status = models.CharField("Status", default="Ativo", max_length=255, null=True)
    rack = models.ForeignKey(Rack, verbose_name="Rack", on_delete=models.PROTECT, null=True, blank=False)
    rack_tamanho = models.IntegerField(default=2, verbose_name="Tamanho em U", null=True)
    rack_posicao = models.IntegerField(default=0, verbose_name="Posição no Rack", null=True)
    consumo = models.CharField("Consumo nominal (Watts)", max_length=255, null=True)
    tipo = models.CharField(verbose_name="Tipo", max_length=255)
    tipo_uso = models.CharField(verbose_name="Tipo de Uso", choices=TIPOS_USO, max_length=255)
    predio = models.ForeignKey("core.Predio", verbose_name="Prédio", null=True, on_delete=models.PROTECT)
    grupos_acesso = models.ManyToManyField("core.GrupoAcesso", verbose_name="Grupos de Acesso", through="EquipamentoGrupoAcesso")
    objects = EquipamentoManager()

    def __str__(self):
        return self.nome_completo()

    def nome(self):
        try:
            return self.servidor.nome
        except ObjectDoesNotExist:
            return f"{self.marca} {self.modelo}"

    def grupo_acesso_name(self):
        return " | ".join([x.grupo_acesso.replace(" | OPERACIONAL", "").replace(" | DESENVOLVIMENTO", "").replace(" | PESQUISA", "") for x in self.grupos_acesso.all()])

    def nome_completo(self):
        if self.tipo == "Servidor Físico" or self.tipo == "Servidor Virtual":
            grupos = " | ".join([x.grupo_acesso.replace(" | OPERACIONAL", "").replace(" | DESENVOLVIMENTO", "").replace(" | PESQUISA", "") for x in self.grupos_acesso.all()])
            if grupos:
                return f"[ {self.servidor.nome.upper()} - {grupos} - {self.tipo_uso} ] {self.descricao}"
            else:
                return f"[ {self.servidor.nome.upper()} - {self.tipo_uso} ] {self.descricao}"
        else:
            return f"[ {self.tipo.upper()} ] {self.marca} {self.modelo}"


class Supercomputador(Equipamento):
    arquitetura = models.CharField("Arquitetura", max_length=255, blank=True, null=True)
    nos = models.CharField("Nós Computacionais", max_length=255, blank=True, null=True)
    desempenho_pico = models.CharField("Desempenho Pico", max_length=255, blank=True, null=True)
    desempenho_efetivo = models.CharField("Desempenho Efetivo", max_length=255, blank=True, null=True)
    memoria = models.CharField("Memória", max_length=255, blank=True, null=True)
    kafka_topico_realtime = models.CharField("Kafka Tópico Realtime", max_length=255, blank=True, null=True)
    kafka_topico_historico = models.CharField("Kafka Tópico Histórico", max_length=255, blank=True, null=True)
    racks = []
    update = None

    class Meta:
        verbose_name = "Supercomputador"
        verbose_name_plural = "Supercomputador"

    def __str__(self):
        return f"{self.marca} {self.modelo}"

    def add_rack(self, rack):
        self.racks.append(rack)

    def set_update(self, update):
        limit_time = datetime.now() - timedelta(minutes=10)
        if datetime.fromtimestamp(update) < limit_time:
            raise EmptyResultSet()
        self.update = datetime.fromtimestamp(update)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.racks = []
        self.update = None

    def save(self, *args, **kwargs):
        if not self.pk:
            self.tipo = "Supercomputador"
        super(Supercomputador, self).save(*args, **kwargs)


class Storage(Equipamento):
    aquisicao = models.CharField("Aquisição", max_length=255, blank=True, null=True)
    fonte = models.CharField("Fonte", max_length=255, blank=True, null=True)
    protocolo = models.CharField("Protocolo", max_length=255, blank=True, null=True)
    controladora = models.IntegerField("Número de controladoras", blank=True, null=True)
    atualizacao = models.DateTimeField("atualizacao", blank=True, null=True)

    class Meta:
        verbose_name = "Storage"
        verbose_name_plural = "Storages"

    def __str__(self):
        return f"{self.marca} {self.modelo}"

    def capacidade(self):
        storage_areas = StorageArea.objects.aggregate_storage_sum().filter(storage__id=self.id)
        if storage_areas:
            return storage_areas[0]["capacidade__sum"]
        else:
            return 0

    def save(self, *args, **kwargs):
        if not self.pk:
            self.tipo = "Storage"
        super(Storage, self).save(*args, **kwargs)


class Rede(models.Model):
    rede = models.CharField("Rede", max_length=255)
    ip = models.CharField("IP", max_length=255, unique=True, null=True)
    prioridade_montagem = models.IntegerField(
        "prioridade de montagem", null=True, help_text="A prioridade de montagem é utilizada quando o Portal cria o Automount Locations e o equipamento possui mais de uma rede com NFS de discos, o MAIOR VALOR tem a prioridade"
    )

    def __str__(self):
        return f"{self.rede} | {self.ip}"


class StorageGrupoAcessoMontagem(models.Model):
    node = models.CharField(max_length=255, blank=True, null=True)
    svm_name = models.CharField(max_length=255, blank=True, null=True)
    ip = models.CharField(max_length=255, blank=True, null=True)
    path = models.CharField(max_length=255, blank=True, null=True)
    rede = models.ForeignKey(Rede, on_delete=models.CASCADE)
    tipo = models.CharField(max_length=255, blank=True, null=True)
    namespace = models.CharField(max_length=255, blank=True, null=True)
    montagem = models.CharField(max_length=255, blank=True, null=True)
    automount = models.CharField(max_length=255, blank=True, null=True)
    parametro = models.CharField(max_length=255, blank=True, null=True)
    storage = models.ForeignKey("infra.Storage", on_delete=models.CASCADE, blank=True, null=True)
    grupo_trabalho = models.ForeignKey("core.GrupoTrabalho", on_delete=models.CASCADE, blank=True, null=True)

    @property
    def mount_information(self):
        return f"{self.parametro} {self.ip}:{self.namespace}"


class HostnameIP(models.Model):
    hostname = models.CharField("Hostname", max_length=255)
    tipo = models.ForeignKey("infra.Rede", on_delete=models.PROTECT, blank=True, null=True)
    ip = models.CharField("IP", max_length=255, unique=True, null=True)
    reservado = models.BooleanField("Reservado", default=False, blank=True, null=True)

    class Meta:
        verbose_name = "HostName IP"
        verbose_name_plural = "HostNames e IPs"
        ordering = [
            "hostname",
        ]

    def __str__(self):
        return f"{self.hostname} | {self.ip} | {self.tipo.rede}"


class Servidor(Equipamento):
    nome = models.CharField("hostname", max_length=255, blank=True, null=True)
    configuracao = models.TextField("Configuração", blank=True, null=True)
    vinculado = models.ForeignKey("infra.Equipamento", verbose_name="Equipamento Vinculado", blank=True, null=True, related_name="servidor_vinculo", on_delete=models.PROTECT)
    hostname_ip = models.ManyToManyField("infra.HostnameIP", through="ServidorHostnameIP")
    ldap = models.BooleanField("ldap", default=False, blank=True, null=True)

    class Meta:
        verbose_name = "Servidor"
        verbose_name_plural = "Servidores"
        ordering = ["nome"]

    def __str__(self):
        return self.nome

    @property
    def freeipa_name(self):
        return f"{self.nome}.cptec.inpe.br"

    @property
    def freeipa_name_mount(self):
        return f"mount_{self.nome}"

    def delete(self, using=None, keep_parents=False):
        for server_hostnameip in ServidorHostnameIP.objects.filter(servidor__id=self.pk):
            hostnameip = server_hostnameip.hostnameip
            hostnameip.reservado = False
            hostnameip.save()
        return super().delete(using=using, keep_parents=keep_parents)


class ServidorHostnameIP(models.Model):
    servidor = models.ForeignKey("infra.Servidor", on_delete=models.CASCADE)
    hostnameip = models.ForeignKey("infra.HostnameIP", verbose_name="Hostname", on_delete=models.PROTECT)

    class Meta:
        unique_together = (("hostnameip"),)
        verbose_name = "Hostname"
        verbose_name_plural = "Hostnames"
        ordering = [
            "servidor__rack_posicao",
        ]

    def __str__(self):
        return self.hostnameip.hostname


class StorageArea(models.Model):
    _TIPO = (
        ("Disk Space", "Disk Space"),
        ("Quota", "Quota"),
    )
    area = models.CharField("Area", max_length=255)
    tipo = models.CharField(max_length=255, choices=_TIPO)
    storage = models.ForeignKey(Storage, verbose_name="Storage", on_delete=models.CASCADE)
    capacidade = models.DecimalField("Capacidade (T)", max_digits=8, decimal_places=2, blank=True, null=True)
    objects = StorageAreaManager()

    class Meta:
        verbose_name = "StorageArea"
        verbose_name_plural = "StorageArea"

    def __str__(self):
        return f"{self.storage} - {self.area}"


class StorageAreaGrupoTrabalho(models.Model):
    quota = models.DecimalField("Quota (T)", max_digits=8, decimal_places=2, blank=True, null=True)
    storage_area = models.ForeignKey("infra.StorageArea", verbose_name="Area", on_delete=models.PROTECT)
    grupo = models.ForeignKey("core.GrupoTrabalho", verbose_name="Grupo", on_delete=models.PROTECT)
    objects = StorageAreaGrupoTrabalhoManager()
    area_total_usado = 0
    area_total_liberado = 0

    class Meta:
        verbose_name = "Storage"
        verbose_name_plural = "Storage"

    def __str__(self):
        return f"{self.grupo} - {self.storage_area}"

    def quota_KB(self):
        if self.quota:
            return self.quota * 1024 * 1024 * 1024 * 1024
        return 0

    def area_total_usado_porcentagem(self):
        if self.quota:
            return int((self.area_total_usado * 100) / self.quota_KB())
        return 0

    def area_total_liberado_corrigido_porcentagem(self):
        if self.quota:
            return int((self.area_total_liberado * 100) / self.quota_KB()) - self.area_total_usado_porcentagem()
        return 0

    def area_total_liberado_porcentagem(self):
        if self.quota:
            return int((self.area_total_liberado * 100) / self.quota_KB())
        return 0


class EquipamentoParte(Equipamento):
    configuracao = models.TextField("Configuração", blank=True, null=True)
    vinculado = models.ForeignKey("infra.Equipamento", verbose_name="Equipamento Vinculado", blank=True, null=True, related_name="equipamentoparte_vinculo", on_delete=models.PROTECT)
    nome = None
    nome_inline = None

    class Meta:
        verbose_name = "Parte de Equipamento"
        verbose_name_plural = "Partes de Equipamento"

    def __str__(self):
        return f"{self.tipo} - {self.marca} {self.modelo}"

    def save(self, *args, **kwargs):
        if not self.pk:
            self.tipo = "Equipamento Físico"
        super(EquipamentoParte, self).save(*args, **kwargs)


class EquipamentoGrupoAcesso(models.Model):
    equipamento = models.ForeignKey("infra.Equipamento", on_delete=models.CASCADE)
    grupo_acesso = models.ForeignKey("core.GrupoAcesso", on_delete=models.PROTECT)

    class Meta:
        verbose_name = "Grupo Acesso do Equipamento"
        verbose_name_plural = "Grupos Acesso do Equipamento"
        ordering = [
            "grupo_acesso__grupo_acesso",
        ]

    def __str__(self):
        return self.grupo_acesso.grupo_acesso


class Ocorrencia(models.Model):
    ocorrencia = models.CharField("Ocorrência", max_length=255, blank=True, null=True)
    descricao = models.CharField("Descrição", max_length=255, blank=True, null=True)
    data = models.DateTimeField("data", default=datetime.now)
    equipamento = models.ForeignKey(
        "infra.Equipamento",
        verbose_name="Equipamento",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )

    class Meta:
        verbose_name = "Ocorrência"
        verbose_name_plural = "Ocorrências"
        ordering = [
            "-data",
        ]

    def __str__(self):
        return f"{self.ocorrencia} {self.descricao}"

    def get_status(self):
        if self.ocorrencia is None:
            return "bg-danger"
        else:
            return "bg-warning"


class AmbienteVirtual(models.Model):
    nome = models.CharField("nome", max_length=255)
    virtualizador = models.CharField("virtualizador", max_length=255)
    versao = models.CharField("versao", max_length=255)
    servidor = models.ManyToManyField("infra.Servidor")

    def __str__(self):
        return f"{self.nome} ({self.virtualizador} { self.versao})"
