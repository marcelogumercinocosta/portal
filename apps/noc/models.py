from django.db import models

class Checklist(models.Model):
    turno = models.CharField(max_length=20)
    criado = models.DateTimeField( 'criado em', auto_now_add=True, auto_now=False)
    enviado = models.DateTimeField( blank=True, null=True)
    responsaveis = models.ManyToManyField('colaborador.Colaborador', through="ChecklistResponsaveis")
    alerta_monitoramento = models.ManyToManyField('infra.ServidorNagiosServico', blank=True, through="ChecklistServidorNagiosServico")
    outros = models.TextField('Geral', blank=True, null=True)

    class Meta :
        ordering = ['-criado','-turno',]

    def __str__(self):
        if self.criado:
            return f"{self.turno} | {self.criado.strftime('%Y-%m-%d %H:%M')}"
        else:
            return f"{self.turno}"


class ChecklistServidorNagiosServico(models.Model):
    checklist = models.ForeignKey("noc.Checklist", on_delete=models.CASCADE)
    alerta_monitoramento = models.ForeignKey("infra.ServidorNagiosServico",  on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.checklist} | {self.alerta_monitoramento}"
class ChecklistResponsaveis(models.Model):
    checklist = models.ForeignKey("noc.Checklist", on_delete=models.CASCADE)
    responsavel = models.ForeignKey("colaborador.Colaborador", on_delete=models.CASCADE)

    def __str__(self):
        return self.responsavel.full_name

class ChecklistEmail(models.Model):
    email = models.CharField(max_length=255)