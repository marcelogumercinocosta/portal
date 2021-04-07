import random
import string
from builtins import range

from django.contrib.admin.models import ADDITION, LogEntry
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.utils.encoding import force_str, force_text
from django.utils.http import urlsafe_base64_decode

from apps.colaborador.models import Colaborador


def gerar_password():
    password = ""
    for ay in list(range(3)):
        i = random.choice(string.ascii_lowercase)
        password += i
    password += random.choice(string.punctuation )
    for ay in list(range(2)):
        o = random.choice(string.digits)
        password += o
    password += random.choice(string.punctuation )
    for ay in list(range(3)):
        u = random.choice(string.ascii_uppercase)
        password += u
    return password


def get_user(uidb64):
    try:
        pk = urlsafe_base64_decode(uidb64).decode()
        user = Colaborador._default_manager.get(pk=pk)
    except (TypeError, ValueError, OverflowError, Colaborador.DoesNotExist, ValidationError):
        user = None
    return user


class HistoryColaborador:
    def __init__(self, request=None):
        self.request = request

    def responsavel(self, colaborador_grupoacesso, status):
        LogEntry.objects.log_action( user_id=self.request.user.pk,
            content_type_id=ContentType.objects.get_for_model(colaborador_grupoacesso.colaborador).pk, object_id=colaborador_grupoacesso.colaborador.pk,
            object_repr=force_str(colaborador_grupoacesso.colaborador), action_flag=ADDITION,
            change_message=(f"Solicitação de acesso aos recursos do Grupo de Trabalho {colaborador_grupoacesso.grupo_acesso.grupo_acesso} - {status}")
        )
        LogEntry.objects.log_action( user_id=self.request.user.pk,
            content_type_id=ContentType.objects.get_for_model(colaborador_grupoacesso.grupo_acesso).pk,
            object_id=colaborador_grupoacesso.grupo_acesso.pk,
            object_repr=force_str(colaborador_grupoacesso.grupo_acesso), action_flag=ADDITION,
            change_message=(f"Solicitação do Colaborador {colaborador_grupoacesso.colaborador.full_name} - {status}"),
        )

    def novo(self, colaborador):
        LogEntry.objects.log_action( user_id=colaborador.pk, 
        content_type_id=ContentType.objects.get_for_model(colaborador).pk, 
        object_id=colaborador.pk, 
        object_repr=force_str(colaborador), action_flag=ADDITION, 
        change_message=("Solicitação de Cadastro")
        )

    def suporte(self, colaborador):
        LogEntry.objects.log_action(
            user_id=self.request.user.pk, content_type_id=ContentType.objects.get_for_model(colaborador).pk, object_id=colaborador.pk, object_repr=force_str(colaborador), action_flag=ADDITION, change_message=("Conta criada pelo suporte")
        )

    def secretaria(self, colaborador):
        LogEntry.objects.log_action( user_id=self.request.user.pk,
            content_type_id=ContentType.objects.get_for_model(colaborador).pk,
            object_id=colaborador.pk,
            object_repr=force_str(colaborador), action_flag=ADDITION,
            change_message=(f"Cadastro revisado pela Secretaria da {colaborador.divisao.divisao}"),
        )

    def chefia(self, colaborador):
        LogEntry.objects.log_action( user_id=self.request.user.pk,
            content_type_id=ContentType.objects.get_for_model(colaborador).pk,
            object_id=colaborador.pk,
            object_repr=force_str(colaborador), action_flag=ADDITION,
            change_message=(f"Cadastro aprovado pela chefia da {colaborador.divisao.divisao}"),
        )

    def solicitacao(self, colaborador, grupo_acesso):
        LogEntry.objects.log_action( user_id=self.request.user.pk,
            content_type_id=ContentType.objects.get_for_model(colaborador).pk,
            object_id=colaborador.pk,
            object_repr=force_str(colaborador),
            action_flag=ADDITION,
            change_message=(f"Solicitação de acesso aos recursos do Grupo de Trabalho {grupo_acesso.grupo_acesso}"),
        )

        LogEntry.objects.log_action( user_id=self.request.user.pk,
            content_type_id=ContentType.objects.get_for_model(grupo_acesso).pk,
            object_id=grupo_acesso.pk,
            object_repr=force_str(grupo_acesso),
            action_flag=ADDITION,
            change_message=(f"Solicitado acesso aos recursos do Grupo de Trabalho por {colaborador.full_name} "),
        )
