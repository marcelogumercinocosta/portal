from __future__ import absolute_import, unicode_literals
from django.core.mail import send_mail

from django.shortcuts import get_object_or_404
from apps.infra.models import Servidor, TemplateVM

from celery import Celery, shared_task, states
from celery_progress.backend import ProgressRecorder
from XenAPI import Session
from django.conf import settings

import fabric  
import time

def get_comandos(origem, destino):
    comandos_final = {'1': [], '2': [], '3': []}
    template_origem, template_origem_ip = origem.host_principal
    vm, vm_ip = destino.host_principal
    template_ips = origem.origens.all()
    vm_ips = destino.hostname_ip.all()
    key_ip = 0
    variaveis = {"{template_origem}": template_origem, 
                "{template_origem_ip}": template_origem_ip,
                "{vm}": vm, 
                "{vm_ip}": vm_ip,
                "{freeipa_server}": settings.IPA_AUTH_SERVER,
                "{freeipa_server_replica}": settings.IPA_AUTH_SERVER_REPLICA,
                "{freeipa_password}": settings.IPA_AUTH_PASSWORD,
                "{freeipa_admin}": settings.IPA_AUTH_USER,
                }
    
    for comando in origem.template_comandos.all().exclude(configuracao=2):
        comando_novo = comando.comando
        for item, valor in variaveis.items():
            comando_novo = comando_novo.replace(item, valor)
        comandos_final[str(comando.configuracao)].append(comando_novo)
    for key_ip in range(len(template_ips)):
        template_origem_ip = template_ips[key_ip].ip
        vm_ip = vm_ips[key_ip].ip
        for comando in origem.template_comandos.filter(configuracao=2):
            comando_novo = comando.comando
            comando_novo = comando_novo.replace('{template_origem_ip}', template_origem_ip).replace('{vm_ip}', vm_ip)
            comandos_final[str(comando.configuracao)].append(comando_novo)
    return comandos_final


@shared_task(bind=True)
def create_vm_task(self, servidor, vm_id,  template_id, memoria, cpu):
    origem = get_object_or_404(TemplateVM, id=template_id)
    destino = get_object_or_404(Servidor, id=vm_id)
    template = origem.nome
    template_origem, template_origem_ip = origem.host_principal
    vm, vm_ip = destino.host_principal
    vm_descricao = f"[ {destino.tipo_uso} - {destino.grupo_acesso_name()} ] {destino.descricao}"
    progress_recorder = ProgressRecorder(self)
    user = settings.XEN_AUTH_USER
    password = settings.XEN_AUTH_PASSWORD
    root = settings.SERVERS_ROOT
    root_password = settings.SERVERS_PASSWORD
    memoria = str(int(memoria) * 1024 * 1024 * 1024)
    cpu = int(cpu)
    total = 200
    print(template)
    try:
        progress_recorder.set_progress(1, total, description="Conetando no XEN")
        session = Session(f"http://{servidor}.cptec.inpe.br")
        session.xenapi.login_with_password(user, password)
    except OSError as err:
        raise OSError(1, f"OS error: {err}")
    try:
        progress_recorder.set_progress(4, total, description="Carregando Template")
        template_ref = session.xenapi.VM.get_by_name_label(template)[0]
        progress_recorder.set_progress(6, total, description="Criando nova VM")
        vm_ref = session.xenapi.VM.clone(template_ref, vm)
        progress_recorder.set_progress(7, total, description="Corrigindo Memória")
        session.xenapi.VM.set_memory(vm_ref, memoria)
        progress_recorder.set_progress(8, total, description="Corrigindo CPU")
        session.xenapi.VM.set_VCPUs_max(vm_ref,16)
        session.xenapi.VM.set_VCPUs_at_startup(vm_ref,cpu)
        progress_recorder.set_progress(9, total, description="Corrigindo Descrição")
        session.xenapi.VM.set_name_description(vm_ref,vm_descricao)
        progress_recorder.set_progress(10, total, description="Corrigindo Nome do Disco")
        vdbs_ref = session.xenapi.VM.get_VBDs(vm_ref)
        for vdb_ref in vdbs_ref:
            if session.xenapi.VBD.get_device(vdb_ref) == 'xvda':
                break
        vdi_ref = session.xenapi.VBD.get_VDI(vdb_ref)
        session.xenapi.VDI.set_name_label(vdi_ref,f"DSK_SYS_{vm}".upper())
        progress_recorder.set_progress(11, total, description="Provisionando")
        session.xenapi.VM.provision(vm_ref)
        progress_recorder.set_progress(12, total, description="Iniciando")
        session.xenapi.VM.start(vm_ref, False, False)
        progress_recorder.set_progress(15, total, description="Aguardando Métricas")
        vgm = session.xenapi.VM.get_guest_metrics(vm_ref)
        contador_progress_temporario = 15
        while session.xenapi.VM_guest_metrics.get_os_version(vgm) == {}:
            contador_progress_temporario +=1
            progress_recorder.set_progress(contador_progress_temporario, total, description="Aguardando Métricas")
            time.sleep(1)
        time.sleep(10)
        progress_recorder.set_progress(100, total, description="Executando Comandos Iniciais")
        comandos = get_comandos(origem, destino)
        command = fabric.Connection(template_origem_ip, port=22, user=root, connect_kwargs={'password': root_password})
        contador_progress_temporario = 100
        for comando in comandos["1"]:
            contador_progress_temporario +=1
            progress_recorder.set_progress(contador_progress_temporario, total, description="Executando Comandos Iniciais")
            command.run(comando)
        for comando in comandos["2"]:
            contador_progress_temporario +=1
            progress_recorder.set_progress(contador_progress_temporario, total, description="Executando Comandos de Rede")
            command.run(comando)
        progress_recorder.set_progress(contador_progress_temporario, total, description="Reiniciando")
        session.xenapi.VM.clean_reboot(vm_ref)
        vgm = session.xenapi.VM.get_guest_metrics(vm_ref)
        while session.xenapi.VM_guest_metrics.get_os_version(vgm) == {}:
            progress_recorder.set_progress(contador_progress_temporario, total, description="Reiniciando")
            contador_progress_temporario +=1
            time.sleep(1)
        time.sleep(15)
        progress_recorder.set_progress(contador_progress_temporario, total, description="Executando Comandos Finais")
        command = fabric.Connection(vm_ip, port=22, user=root, connect_kwargs={'password': root_password})
        for comando in comandos["3"]:
            contador_progress_temporario +=2
            progress_recorder.set_progress(contador_progress_temporario, total, description="Executando Comandos Finais")
            command.run(comando)
        progress_recorder.set_progress(199, total, description="Desabilitando ssh root")
        progress_recorder.set_progress(total, total, description=f"{vm} Criada")
    except Exception as e:
        self.update_state(state=states.FAILURE, meta={'custom': str(e)})
        send_mail('ERRO na Criação de VM', f"{vm} - {str(e)}" , settings.EMAIL_HOST_USER, [settings.EMAIL_SYSADMIN, ])
        return f"Error: {str(e)}"
    finally:
        session.xenapi.session.logout()
    destino.vm_remover = True
    destino.vm_ambiente_virtual = origem.ambiente_virtual
    destino.save()
    send_mail('Criação de VM OK',f'{vm} criada com sucesso!' , settings.EMAIL_HOST_USER, [settings.EMAIL_SUPORTE, settings.EMAIL_SYSADMIN, ])
    return f"{vm} OK"


@shared_task(bind=True)
def delete_vm_task(self, servidor, vm_name):
    user = settings.XEN_AUTH_USER
    password = settings.XEN_AUTH_PASSWORD
    try:
        session = Session(f"http://{servidor}.cptec.inpe.br")
        session.xenapi.login_with_password(user, password)
    except OSError as err:
        raise OSError(1, f"OS error: {err}")
    try:
        vm_ref = session.xenapi.VM.get_by_name_label(vm_name)[0]
        session.xenapi.VM.hard_shutdown(vm_ref)
        vdbs_ref = session.xenapi.VM.get_VBDs(vm_ref)
        for vdb_ref in vdbs_ref:
            vdi_ref = session.xenapi.VBD.get_VDI(vdb_ref)
            if vdi_ref != "OpaqueRef:NULL":
                session.xenapi.VDI.destroy(vdi_ref)
        session.xenapi.VM.destroy(vm_ref)
        send_mail('Remoção de VM OK',f'{vm_name} removida com sucesso!' , settings.EMAIL_HOST_USER, [settings.EMAIL_SUPORTE, settings.EMAIL_SYSADMIN, ])
        return f"{vm_name} DELETE"
    except Exception as e:
        send_mail('ERRO na Remoção de VM', str(e) , settings.EMAIL_HOST_USER, [settings.EMAIL_SUPORTE, settings.EMAIL_SYSADMIN, ])
        return f"Error: {str(e)}"
        

    finally:
        session.xenapi.session.logout()