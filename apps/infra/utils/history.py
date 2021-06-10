import random
import string
from builtins import range

from django.contrib.admin.models import ADDITION, LogEntry
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_str, force_text
from django.utils.http import urlsafe_base64_decode


class HistoryInfra:
    def __init__(self, request=None):
        self.request = request

    def novo_servidor(self, servidor):
        LogEntry.objects.log_action( user_id=self.request.user.pk, 
        content_type_id=ContentType.objects.get_for_model(servidor).pk, 
        object_id=servidor.pk, 
        object_repr=force_str(servidor), action_flag=ADDITION, 
        change_message=("Servidor adicionado no FreeIPA")
        )

    def delete_servidor(self, servidor, hostnameip):
        LogEntry.objects.log_action( user_id=self.request.user.pk, 
        content_type_id=ContentType.objects.get_for_model(hostnameip).pk, 
        object_id=hostnameip.pk, 
        object_repr=force_str(hostnameip), action_flag=ADDITION, 
        change_message=(f"Servidor {servidor.nome_completo()} liberou Hostname")
        )

    def status_servidor(self, servidor):
        LogEntry.objects.log_action( user_id=self.request.user.pk, 
        content_type_id=ContentType.objects.get_for_model(servidor).pk, 
        object_id=servidor.pk, 
        object_repr=force_str(servidor), action_flag=ADDITION, 
        change_message=(f"Alteração do status do Servidor para: {servidor.status} ")
        )
