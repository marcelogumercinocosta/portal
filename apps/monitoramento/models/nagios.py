from django.db import models


class NagiosServicos(models.Model):
    servico = models.CharField("Serviço", max_length=255)
    comando = models.CharField("comando Nagios", max_length=255)
    tempo = models.IntegerField("Tempo de verificação")
    padrao = models.BooleanField("Ativar por padrão", default=False)
    
    class Meta:
        verbose_name = "Nagios Serviço"
        verbose_name_plural = "Nagios Serviços"
        ordering = ("servico",)

    def __str__(self):
        return self.servico

    