import numpy as np
from django.contrib import messages
from apps.core.utils.freeipa import FreeIPA
from apps.infra.models import (Equipamento, Rede, Servidor, StorageGrupoAcessoMontagem)


class Automount:
    def __init__(self, client_feeipa: FreeIPA, servidor: Servidor, request):
        self.client_feeipa = client_feeipa
        self.servidor = servidor
        self.request = request
        ips = (np.unique([ hostname.tipo.ip for hostname in servidor.hostname_ip.all()]))
        self.rede = Rede.objects.filter(ip__in=ips).order_by("-prioridade_montagem")[0]


    def adicionar_grupos(self, grupos_acesso:[]):
        for grupo_acesso in grupos_acesso:
            self.client_feeipa.hbacrule_add_members_host(grupo_acesso.hbac_freeipa, self.servidor.freeipa_name)
            self.client_feeipa.sudorule_add_members_host(grupo_acesso.grupo_trabalho.get_sudo(), host=self.servidor.freeipa_name)
            if self.client_feeipa.automountmap_add_indirect(self.servidor.freeipa_name_mount, grupo_acesso.automountmap, '/-'):
                storage_grupoacesso_montagens = StorageGrupoAcessoMontagem.objects.filter(tipo=grupo_acesso.tipo, automount='auto.grupo', grupo_trabalho__id=grupo_acesso.grupo_trabalho.id, rede__id=self.rede.id)
                if storage_grupoacesso_montagens.exists():
                    for key in storage_grupoacesso_montagens: 
                        self.client_feeipa.automountkey_add(self.servidor.freeipa_name_mount, grupo_acesso.automountmap, key.montagem, key.mount_information)
                else:
                    messages.add_message(self.request, messages.WARNING, f"Não existe montagem para {grupo_acesso.grupo_acesso}! ")

    def remover_grupos(self, grupos_acesso:[]):
        for grupo_acesso in grupos_acesso:
            self.client_feeipa.hbacrule_remove_members_host(grupo_acesso.hbac_freeipa, self.servidor.freeipa_name)
            self.client_feeipa.sudorule_remove_members_host(grupo_acesso.grupo_trabalho.get_sudo(), host=self.servidor.freeipa_name)
            if self.client_feeipa.automountlocation_find_count(cn=self.servidor.freeipa_name_mount) == 1:
                if self.client_feeipa.automountmap_find_count(automountlocationcn=self.servidor.freeipa_name_mount, automountmapname=grupo_acesso.automountmap):
                    self.client_feeipa.automountkey_del(self.servidor.freeipa_name_mount, 'auto.master', '/-', grupo_acesso.automountmap)
                    self.client_feeipa.automountmap_del(self.servidor.freeipa_name_mount, grupo_acesso.automountmap)
                else:
                    messages.add_message(self.request, messages.WARNING, f"Não existe montagem para {grupo_acesso.grupo_acesso}! ")
            else:
                messages.add_message(self.request, messages.WARNING, f"Não existe montagem para {self.servidor.freeipa_name_mount}! ")

    def adicionar_oper(self):
        storage_grupoacesso_montagens = StorageGrupoAcessoMontagem.objects.filter( automount='auto.oper', rede__id=self.rede.id)
        if storage_grupoacesso_montagens.exists() and self.client_feeipa.automountmap_add_indirect(self.servidor.freeipa_name_mount, 'auto.oper', '/oper'):
            for key in storage_grupoacesso_montagens:
                self.client_feeipa.automountkey_add(self.servidor.freeipa_name_mount,'auto.oper', key.montagem, key.mount_information)
    
    def adicionar_home(self):
        storage_grupoacesso_montagens = StorageGrupoAcessoMontagem.objects.filter( automount='auto.home', rede__id=self.rede.id)
        if storage_grupoacesso_montagens.exists() and self.client_feeipa.automountmap_add_indirect(self.servidor.freeipa_name_mount, 'auto.home', '/home'):
            for key in storage_grupoacesso_montagens:
                self.client_feeipa.automountkey_add(self.servidor.freeipa_name_mount,'auto.home', key.montagem, key.mount_information)
