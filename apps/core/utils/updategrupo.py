from django.contrib import messages
from apps.infra.models import EquipamentoGrupoAcesso, StorageGrupoAcessoMontagem
import datetime
from django.shortcuts import get_object_or_404
from apps.core.models import GrupoAcesso, ColaboradorGrupoAcesso


class UpdateGrupoAcesso:
    
    def __init__(self, client_feeipa, history_core):
        self.client_feeipa = client_feeipa
        self.history_core = history_core

    def update_acesso(self, grupo_trabalho):
        tipos = ["pesquisa", "desenvolvimento", "operacional", "documento"]
        for tipo  in tipos:
            grupo_acesso = GrupoAcesso()
            grupo_acesso.make(tipo, grupo_trabalho)
            if getattr(grupo_trabalho, tipo):
                if self.client_feeipa.hbacrule_find_count(cn=grupo_acesso.hbac_freeipa) == 0:
                    self.client_feeipa.set_hbac_group(grupo_acesso)
                    grupo_acesso.save()
                    self.history_core.update_grupo_acesso(grupo=grupo_trabalho, assunto=f"Novo grupo de acesso: {grupo_acesso.hbac_freeipa}")
            else:
                if self.client_feeipa.hbacrule_find_count(cn=grupo_acesso.hbac_freeipa) == 1:
                    grupo_acesso = get_object_or_404(GrupoAcesso, grupo_acesso=grupo_acesso.grupo_acesso)
                    grupo_acesso.delete()
                    self.client_feeipa.hbacrule_delete(grupo_acesso.hbac_freeipa)
                    self.history_core.update_grupo_acesso(grupo=grupo_trabalho, assunto=f"Delete grupo de acesso: {grupo_acesso.hbac_freeipa}")
        if grupo_trabalho.data_criado == None : grupo_trabalho.data_criado = datetime.datetime.now()
        grupo_trabalho.save_confirm()

class UpdateColaboradorGrupo:
    def __init__(self, client_feeipa, history_core):
        self.client_feeipa = client_feeipa
        self.history_core = history_core

    def update_user(self, grupo_trabalho):
        responsaveis = grupo_trabalho.responsavelgrupotrabalho_set.all().exclude(responsavel__username='admin.portal')
        grupos_acesso = GrupoAcesso.objects.filter(grupo_trabalho=grupo_trabalho)
        for responsavel in responsaveis:
            for grupo_acesso in grupos_acesso:
                if  not ColaboradorGrupoAcesso.objects.filter(colaborador=responsavel.responsavel, grupo_acesso=grupo_acesso):
                    colaborador_grupoacesso = ColaboradorGrupoAcesso(colaborador_id=responsavel.responsavel.pk, grupo_acesso_id=grupo_acesso.pk, aprovacao=1)
                    colaborador_grupoacesso.save()
                    self.history_core.responsavel_grupo_acesso(colaborador=responsavel.responsavel,  grupo_acesso=grupo_acesso)
                    self.client_feeipa.add_user_group_hhac(responsavel.responsavel.username, grupo_acesso.hbac_freeipa, grupo_trabalho.grupo_sistema)

class UpdateGrupoVerificaDisco:

    def verifica_disco(self, grupo_trabalho, request):
        discos_verificado = True
        discos = [montagem.tipo for montagem in  StorageGrupoAcessoMontagem.objects.filter(grupo_trabalho=grupo_trabalho,svm_name='svm_int')]
        if grupo_trabalho.pesquisa and not discos.count('PESQUISA') >= 3:
            discos_verificado = False
        if grupo_trabalho.operacional and not discos.count('OPERACIONAL') >= 3:
            discos_verificado = False
        if grupo_trabalho.desenvolvimento and not discos.count('DESENVOLVIMENTO') >= 3:
            discos_verificado = False
        if grupo_trabalho.documento and not discos.count('DOCUMENTO') >= 3:
            discos_verificado = False
        discos = [montagem.tipo for montagem in  StorageGrupoAcessoMontagem.objects.filter(grupo_trabalho=grupo_trabalho, svm_name='svm_share')]
        if grupo_trabalho.share and not len(discos) >= 1:
            discos_verificado = False
        if not discos_verificado:
            messages.add_message(request, messages.ERROR, "Verifique os tipos selecionados para o grupo, não estão compativeis com os discos, Crie os discos, verifique scripts do netapp ou coloque opções corretas!")
        return discos_verificado

    def verifica_equipamento_grupoacesso(self, grupo_trabalho, request):
        equipamento_verificado = True
        tipos = [equipamentogrupoacesso.grupo_acesso.tipo for equipamentogrupoacesso in  EquipamentoGrupoAcesso.objects.filter(grupo_acesso__grupo_trabalho=grupo_trabalho)]
        if not grupo_trabalho.pesquisa and tipos.count('PESQUISA') > 0:
            equipamento_verificado = False
        if not grupo_trabalho.operacional and tipos.count('OPERACIONAL') > 0:
            equipamento_verificado = False
        if not grupo_trabalho.desenvolvimento and tipos.count('DESENVOLVIMENTO') > 0:
            equipamento_verificado = False
        if not equipamento_verificado:
            messages.add_message(request, messages.ERROR, "Um Grupo de Acesso desse Grupo de Trabalho esta  vinculado a algum Servidor, Remova o grupo de acesso correspondente antes!")
        return equipamento_verificado

