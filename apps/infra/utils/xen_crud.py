from __future__ import absolute_import, unicode_literals
import os

from django.shortcuts import get_object_or_404
from apps.infra.tasks import create_vm_task, delete_vm_task
from XenAPI import Failure, Session
from django.conf import settings
from django.contrib import messages
import socket

class XenCrud:

    def __init__(self, request, vm, ambiente_virtual):
        self.user = settings.XEN_AUTH_USER
        self.password = settings.XEN_AUTH_PASSWORD
        self.request = request
        self.vm = vm
        self.servidores = [servidor.nome for servidor in ambiente_virtual.servidor.all()]
        self.servidor = self.servidores[0]
        

    # Login
    def login(self):
        try:
            self.session = Session(f"http://{self.servidor}.cptec.inpe.br")
            self.session.xenapi.login_with_password(self.user, self.password)
        except Failure as err:
            id_server = int(self.servidores.index(self.servidor)) + 1
            if id_server < len(self.servidores):
                if err.details[0] == "HOST_IS_SLAVE":
                    self.session = Session("http://" + err.details[1])
                    self.servidor = self.servidores[id_server]
                    self.login()
            else:
                raise Failure( f"Failure error: {err}")
        except OSError as err:
            raise OSError(1, f"OS error: {err}")
    
    def create_vm(self, template,  memoria, cpu):
        origem_hostname, origem_ip = template.host_principal
        origem_ping = os.system(f"ping -c 1 -W 1 -q {origem_hostname}.cptec.inpe.br  > /dev/null")
        destino_ping = os.system(f"ping -c 1 -W 1 -q {self.vm.nome}.cptec.inpe.br  > /dev/null") 
        self.login()
        vm_ref_verificacao_vm = self.session.xenapi.VM.get_by_name_label(self.vm.nome)
        if ( origem_ping != 0  and len(vm_ref_verificacao_vm) == 0
            and  destino_ping != 0  and len(template.origens.all()) == len(self.vm.hostname_ip.all())):
            messages.add_message(self.request, messages.SUCCESS, f"XEN: Criando a nova VM")
            return create_vm_task.delay(self.servidor, self.vm.id, template.id, memoria, cpu)
        else:
            messages.add_message(self.request, messages.WARNING, f"XEN: O Servidor de Origem do Template está Ligado ou já existe o VM com esse hostname ou as quantidade de rede não é compatível")
            return False
    
    def delete_vm(self):
        self.login()
        messages.add_message(self.request, messages.WARNING, f"XEN: Deletando VM em segundo plano.")
        return delete_vm_task.delay(self.servidor, self.vm.nome)