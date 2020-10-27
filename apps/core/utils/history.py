import random
import string
from builtins import range

from django.contrib.admin.models import ADDITION, LogEntry
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.utils.encoding import force_str, force_text
from django.utils.http import urlsafe_base64_decode

from apps.colaborador.models import Colaborador



class HistoryCore:
    def __init__(self, request=None):
        self.request = request

    def confirmar_assinatura(self, grupo):
        LogEntry.objects.log_action(user_id=self.request.user.id, content_type_id=ContentType.objects.get_for_model(grupo).pk, object_id=grupo.pk, object_repr=force_str(grupo), action_flag=ADDITION, change_message=("Assinatura OK"))

    def update_grupo_acesso(self, grupo, assunto):
        LogEntry.objects.log_action(user_id=self.request.user.id, content_type_id=ContentType.objects.get_for_model(grupo).pk, object_id=grupo.pk, object_repr=force_str(grupo), action_flag=ADDITION, change_message=(assunto))

    def responsavel_grupo_acesso(self, colaborador, grupo_acesso):
        LogEntry.objects.log_action( user_id=self.request.user.pk,
            content_type_id=ContentType.objects.get_for_model(colaborador).pk,
            object_id=colaborador.pk,
            object_repr=force_str(colaborador),
            action_flag=ADDITION,
            change_message=(f"Acesso aos recursos do Grupo de Trabalho {grupo_acesso.grupo_acesso} por ser responsavel"),
        )

        LogEntry.objects.log_action( user_id=self.request.user.pk,
            content_type_id=ContentType.objects.get_for_model(grupo_acesso).pk,
            object_id=grupo_acesso.pk,
            object_repr=force_str(grupo_acesso),
            action_flag=ADDITION,
            change_message=(f"Acesso aos recursos do Grupo de Trabalho por {colaborador.full_name} por ser responsavel"),
        )