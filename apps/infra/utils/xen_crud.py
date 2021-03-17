from __future__ import absolute_import, unicode_literals
from apps.infra.tasks import create_vm_task
from apps.infra.models import AmbienteVirtual
from apps.infra.forms import AmbienteVirtualServidorInLineForm

from celery import Celery, shared_task
from datetime import datetime
from XenAPI import Failure, Session
from django.conf import settings
from django.contrib import messages
import fabric  
import time


class XenCrud:

    def __init__(self, servidor, request=None):
        self.servers = AmbienteVirtual.objects.get(pk=1).servidor.all()
        self.server = 'tentilhao'
        self.user = settings.XEN_AUTH_USER
        self.password = settings.XEN_AUTH_PASSWORD
        self.vm = servidor.nome
        self.vm_descricao = f"[ {servidor.tipo_uso} - {servidor.grupo_acesso_name()} ] {servidor.descricao}"
        self.request = request

    # Login
    def login(self):
        
        try:
            self.session = Session(f"http://{self.server}.cptec.inpe.br")
            self.session.xenapi.login_with_password(self.user, self.password)
        except Failure as err:
            id_server = int(self.servers.index(self.server)) + 1
            if id_server < len(self.servers):
                if err.details[0] == "HOST_IS_SLAVE":
                    self.session = Session("http://" + err.details[1])
                    self.server = self.servers[id_server ]
                    self.login()
            else:
                raise Failure( f"Failure error: {err}")
        except OSError as err:
            raise OSError(1, f"OS error: {err}")
        return self
    
    def create_vm(self, template, memoria, cpu):
        self.template = template
        self.vm_origem = "tapera"
        self.login()
        vm_ref_verificacao_template = self.session.xenapi.VM.get_by_name_label(self.vm_origem)
        vm_ref_verificacao_vm = self.session.xenapi.VM.get_by_name_label(self.vm)
        if self.session.xenapi.VM.get_power_state(vm_ref_verificacao_template[0]) == "Halted" and len(vm_ref_verificacao_vm) == 0:
            messages.add_message(self.request, messages.SUCCESS, f"XEN: Criando a nova VM")
            return create_vm_task.delay(self.vm, self.vm_descricao, template, memoria, cpu)
        else:
            messages.add_message(self.request, messages.WARNING, f"XEN: O Servidor de Origem do Template está Ligado ou já existe o VM com esse hostname")
            return False
    
    def verificar_vm(self):
        self.login()
        if len(self.session.xenapi.VM.get_by_name_label(self.vm)) == 0:
            return True
        