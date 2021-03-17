from __future__ import absolute_import, unicode_literals

from celery import Celery, shared_task, states
from celery_progress.backend import ProgressRecorder
from datetime import datetime
from XenAPI import Session
from django.conf import settings
import fabric  
import time


@shared_task(bind=True)
def create_vm_task(self,vm, vm_descricao, template, memoria, cpu):
    progress_recorder = ProgressRecorder(self)
    user = settings.XEN_AUTH_USER
    password = settings.XEN_AUTH_PASSWORD
    memoria = int(memoria) * 1024 * 1024 * 1024
    server = 'tentilhao'
    vm_ip = "150.163.147.169"
    template_origem = "tapera"
    template_origem_ip = "150.163.147.180"
    total = 100
    try:
        progress_recorder.set_progress(5, total, description=f"Conetando no XEN")
        session = Session(f"http://{server}.cptec.inpe.br")
        session.xenapi.login_with_password(user, password)
    except OSError as err:
        raise OSError(1, f"OS error: {err}")
    try:
        progress_recorder.set_progress(10, total, description=f"Carregando Template")
        template_ref = (session.xenapi.VM.get_by_name_label(template))[0]
        progress_recorder.set_progress(20, total, description=f"Criando novo Servidor")
        vm_ref = session.xenapi.VM.clone(template_ref, vm)
        progress_recorder.set_progress(30, total, description=f"Corrigindo Memória")
        session.xenapi.VM.set_memory(vm_ref,"17188651008")
        progress_recorder.set_progress(35, total, description=f"Corrigindo CPU")
        session.xenapi.VM.set_VCPUs_max(vm_ref,16)
        session.xenapi.VM.set_VCPUs_at_startup(vm_ref,16)
        progress_recorder.set_progress(40, total, description=f"Corrigindo Descrição")
        session.xenapi.VM.set_name_description(vm_ref,vm_descricao)
        progress_recorder.set_progress(45, total, description=f"Corrigindo Nome do Disco")
        vdbs_ref = session.xenapi.VM.get_VBDs(vm_ref)
        for vdb_ref in vdbs_ref:
            if session.xenapi.VBD.get_device(vdb_ref) == 'xvda':
                break
        vdi_ref = session.xenapi.VBD.get_VDI(vdb_ref)
        session.xenapi.VDI.set_name_label(vdi_ref,f"DSK_SYS_{vm}".upper())
        progress_recorder.set_progress(50, total, description=f"Provisionando")
        session.xenapi.VM.provision(vm_ref)
        progress_recorder.set_progress(60, total, description=f"Iniciando")
        session.xenapi.VM.start(vm_ref, False, False)
        progress_recorder.set_progress(70, total, description=f"Aguardando Métricas")
        vgm = session.xenapi.VM.get_guest_metrics(vm_ref)
        while session.xenapi.VM_guest_metrics.get_os_version(vgm) == {}:
            time.sleep(1)
        progress_recorder.set_progress(75, total, description=f"Executando Comandos de Troca IP")
        time.sleep(10)
        command = fabric.Connection(template_origem_ip, port=22, user="root", connect_kwargs={'password': '!=S@63r#S'})
        command.run(f"sed -i 's/{template_origem}/{vm}/g' /etc/hostname")
        command.run(f"sed -i 's/- {template_origem_ip}\/24/- {vm_ip}\/24/g' /etc/netplan/00-installer-config.yaml")
        command.run(f"sed -i 's/{template_origem}/{vm}/g' /etc/hosts")
        command.run(f"sed -i 's/{template_origem_ip}/{vm_ip}/g' /etc/hosts")
        command.run(f"hostnamectl set-hostname {vm}.cptec.inpe.br")
        command.run(f"sed -i 's/{template_origem_ip}/{vm_ip}/g' /etc/ssh/sshd_config")
        progress_recorder.set_progress(85, total, description=f"          Reiniciando")
        session.xenapi.VM.clean_reboot(vm_ref)
        vgm = session.xenapi.VM.get_guest_metrics(vm_ref)
        while session.xenapi.VM_guest_metrics.get_os_version(vgm) == {}:
            time.sleep(1)
        progress_recorder.set_progress(90, total, description=f"          Executando Comandos FreeIPA")
        time.sleep(15)
        command = fabric.Connection(vm_ip, port=22, user="root", connect_kwargs={'password': '!=S@63r#S'})
        command.run("ipa-client-install --domain=cptec.inpe.br --server=viracopos.cptec.inpe.br -f -q -w !=S@63r#S -p admin --force-join --no-ntp --enable-dns-updates --unattended")
        command.run(f"ipa-client-automount --server=viracopos.cptec.inpe.br --location=mount_{vm} --unattended")
        progress_recorder.set_progress(95, total, description=f"          Desabilitando ssh root")
        command.run("sed -i 's/PermitRootLogin yes/PermitRootLogin no/g' /etc/ssh/sshd_config")
        command.run("service sshd restart")
        progress_recorder.set_progress(total, total, description=f"{vm} OK")
        return f"{vm} OK"
    except Exception as e:
        self.update_state(state=states.FAILURE, meta={'custom': str(e)})
        return f"Error: {str(e)}"
    finally:
        session.xenapi.session.logout()