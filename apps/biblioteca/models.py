from django.core.validators import FileExtensionValidator
from django.db import models
from django.contrib.auth.models import Group


class Documento(models.Model):
    documento = models.CharField(max_length=255)
    upload = models.FileField(upload_to='documento/', validators=[FileExtensionValidator(allowed_extensions=['pdf'])])
    descricao = models.TextField('descrição', blank=True, null=True)
    criado = models.DateTimeField( 'criado em', auto_now_add=True, auto_now=False)
    modificado = models.DateTimeField( 'modificado em', auto_now_add=False, auto_now=True)
    grupo = models.ManyToManyField(Group, blank=True)


    class Meta :
        ordering = ['modificado','documento']

    def __str__(self):
        return f"{self.documento}"
