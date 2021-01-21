from django.db import models
from apps.core.models import GrupoPortal
from apps.infra.models import Equipamento
from apps.colaborador.models import Colaborador

class Problema(models.Model):
    problema = models.CharField(max_length=255)
    sla =  models.IntegerField( default=30,  help_text='Acordo de Nível de Serviço. Mensura o nível de entrega de serviços que um contratante ou cliente, em horas', verbose_name="SLA")
    grupo_portal = models.ForeignKey(GrupoPortal, on_delete=models.CASCADE, verbose_name="Fila de Atendimento") 

    #Metadata
    class Meta :
        ordering = ['grupo_portal']

    def __str__(self):
        return self.problema

class Ticket(models.Model):

    STATUS_CHOICES = (
        (1, 'Aberto'),
        (2, 'Em Atendimento'),
        (3, 'Fechado'),
        (4, 'Cancelado'),
    )

    PRIORIDADE_CHOICES  = (
        (3, 'Alta'),
        (2, 'Normal'),
        (1, 'Baixa')
    )

    ORIGEM_CHOICES  = (
        (1, 'Monitoramento'),
        (2, 'Atendimento')
    )

    ticket = models.AutoField('Número do Ticket', primary_key=True)
    status = models.IntegerField('Status', choices=STATUS_CHOICES, default=1)
    prioridade = models.IntegerField('Prioridade', choices=PRIORIDADE_CHOICES, default=2, blank=2)
    origem = models.IntegerField('origem', choices=ORIGEM_CHOICES)
    primeiro_atendimento = models.CharField(max_length=255, blank=True, help_text='Número da OS externa', verbose_name='Primeiro Atendimento')
    problema = models.ForeignKey(Problema, null=True, on_delete=models.CASCADE) 
    equipamento = models.ManyToManyField(Equipamento, ) 
    colaborador = models.ForeignKey(Colaborador, blank=True, null=True, on_delete=models.SET_NULL)
    operador = models.ForeignKey(Colaborador,  on_delete=models.CASCADE, related_name='operador')

    class Meta :
        ordering = ['-prioridade']

    def __str__(self):
        return f"Ticket {self.ticket}"


class TicketAtualizacao(models.Model):

    STATUS_CHOICES = (
        (1, 'Aberto'),
        (2, 'Em Atendimento'),
        (2, 'Assentamento'),
        (3, 'Aguardando agente externo'),
        (4, 'Em estudo'),
        (5, 'Fechado'),
        (6, 'Cancelado'),
    )

    descricao = models.TextField('Descrição')
    data =  models.DateTimeField('Atualização', auto_now=False)
    operador = models.ForeignKey(Colaborador, blank=True, null=True, on_delete=models.CASCADE)
    status = models.IntegerField('Status', choices=STATUS_CHOICES, default=1)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    

    class Meta :
        ordering = ['-data']

    def __str__(self):
        return self.data