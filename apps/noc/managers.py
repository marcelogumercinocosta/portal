from django.db import models
from django.db.models import Sum



class ChecklistServidorNagiosServicoManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().select_related("checklist","alerta_monitoramento__nagios_servico","alerta_monitoramento__servidor")