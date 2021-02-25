import random
import string
from builtins import range
import requests
from django.conf import settings
from django.contrib import messages
from python_freeipa import Client
from django import http
import logging


class FreeIPA(Client):
    def __init__(self, request=None):
        self._host = settings.IPA_AUTH_SERVER
        self._base_url = "https://{0}/ipa".format(self._host)
        self._verify_ssl = settings.IPA_AUTH_SERVER_SSL_VERIFY
        self._version = settings.IPA_AUTH_SERVER_API_VERSION
        self._session = requests.Session()
        self._log = logging.getLogger(__name__)
        self.login(settings.IPA_AUTH_USER, settings.IPA_AUTH_PASSWORD)
        self.request = request

    def set_novasenha(self, colaborador, password):
        try:
            params = {"userpassword": password}
            self._request("user_mod", colaborador.username, params)
            if self.request: messages.add_message(self.request, messages.SUCCESS, "Uma nova senha foi gerada com sucesso!")
            return True
        except Exception as e:
            if self.request: messages.add_message(self.request, messages.ERROR, "Erro na mudança de senha: " + str(e))
        return False

    def set_colaborador(self, colaborador, password):
        if self.user_create(
            colaborador.username,
            colaborador.first_name,
            colaborador.last_name,
            colaborador.full_name,
            colaborador.uid,
            colaborador.uid,
            display_name=colaborador.username,
            noprivate=False,
            mail=colaborador.email,
            home_directory="/users/" + colaborador.username,
            disabled=False,
            user_password=password,
            login_shell="/bin/bash",
            telephone_number=colaborador.ramal,
            job_title=colaborador.vinculo.vinculo,
        ):
            if colaborador.data_fim:
                params = {"krbprincipalexpiration": colaborador.data_fim.strftime('%Y%m%d%H%M%SZ')}
                self._request("user_mod", colaborador.username, params)
            return True
        return False

    def set_grupo(self, grupo):
        description = "Conta de Group User do Grupo " + grupo.grupo.upper()
        if self.group_create(grupo.grupo_sistema, grupo.gid, description=description):
            if self.set_colaborador_grupo(grupo):
                return self.set_sudo(grupo)
        return False

    def set_host(self, servidor, description=None, force=True):
        if self.host_create(servidor.freeipa_name, description, force):
            if self.automountlocation_add(servidor.freeipa_name_mount):
                if self.hostgroup_add_member_host('hg_srv_all',servidor.freeipa_name):
                    return True
        return False

    def set_colaborador_grupo(self, grupo):
        if (self.group_find_count(cn=grupo.grupo_sistema) == 1) and (self.user_create(
            grupo.grupo_sistema,
            grupo.divisao.divisao,
            grupo.grupo.upper(),
            grupo.divisao.divisao + "|" + grupo.grupo.upper(),
            grupo.gid,
            grupo.gid,
            job_title="Sudo",
            telephone_number=8476,
            noprivate=True,
            display_name=grupo.grupo_sistema,
            home_directory="/scripts/" + grupo.grupo_sistema,
            login_shell="/bin/false",
            mail=settings.EMAIL_SYSADMIN,
        )):
            return self.group_add_member_group(grupo.grupo_sistema, users=grupo.grupo_sistema)
        if self.request: messages.add_message(self.request, messages.ERROR, "Erro na criação do usario do grupo")
        return False

    def set_sudo(self, grupo):
        description = "Sudo do User Group " + grupo.grupo.upper()
        if (self.group_find_count(cn=grupo.grupo_sistema) == 1) and (self.sudorule_create(grupo.get_sudo(), description)):
            if self.sudorule_add_members_group(grupo.get_sudo(), grupo.grupo_sistema):
                if self.sudorule_add_runasuser(grupo.get_sudo(), grupo.grupo_sistema):
                    self.sudorule_add_option(grupo.get_sudo(), "!authenticate")
                    self.sudorule_add_allow_command(grupo.get_sudo())
                    return True
        if self.request: messages.add_message(self.request, messages.ERROR, "Erro na criação do sudo")
        return False

    def remove_grupo(self, grupo):
        if (self.group_find_count(cn=grupo.grupo_sistema) == 1) and ( self.group_delete(grupo.grupo_sistema)):
            if self.sudorule_delete(grupo.get_sudo()):
                return self.user_delete(grupo.grupo_sistema)
        if self.request: messages.add_message(self.request, messages.ERROR, "Erro remoção do grupo")
        return False

    def set_hbac_group(self, grupo_acesso):
        if (self.group_find_count(cn=grupo_acesso.grupo_trabalho.grupo_sistema) == 1)  and (self.hbacrule_create(grupo_acesso.hbac_freeipa, grupo_acesso.description)):
            return self.hbacrule_add_members_service(grupo_acesso.hbac_freeipa, hbacsvcgroups="hbac_grp_servicos_padrao")
        if self.request: messages.add_message(self.request, messages.ERROR, "Erro criaçao do Hbac")
        return False

    def add_user_group_hhac(self, user, hbac_freeipa, grupo_sistema):
        if (self.hbacrule_find_count(hbac_freeipa) == 1) and (self.hbacrule_add_members_user(hbac_freeipa, user)):
            if self.group_add_member_group(grupo_sistema, user):
                return True
        return False

    def remove_hbac_group_rule(self, grupo_acesso):
        return self.hbacrule_delete(grupo_acesso.hbac_freeipa)

    def __execute_freeipa(self, message, *args):
        try:
            self._request(*args)
            if self.request: messages.add_message(self.request, messages.SUCCESS, f"FreeIPA:  {message}")
            return True
        except Exception as e:
            if self.request: messages.add_message(self.request, messages.WARNING, "FreeIPA: " + str(e))
            return False

    def group_create(self, group, gidnumber, description, **kwargs):
        params = {"all": True, "gidnumber":gidnumber, "description":description, "nonposix":False, "external":False, "no_members":False }
        return self.__execute_freeipa(f"group {group} created ", "group_add", group, params)

    def group_delete(self, groupname):
        return self.__execute_freeipa(f"group {groupname} deleted", "group_del", groupname)

    def group_find_count(self, criteria=None, **kwargs):
        params = {"all": True, "sizelimit": 0}
        params.update(kwargs)
        return self._request("group_find", criteria, params)["count"]

    def user_create(
        self,
        username,
        first_name,
        last_name,
        full_name,
        uidnumber,
        gidnumber,
        display_name=None,
        noprivate=False,
        mail=None,
        job_title=None,
        telephone_number=None,
        login_shell=None,
        disabled=False,
        home_directory=None,
        user_password=None,
        random_pass=False,
        **kwargs,
    ):
        params = {
            "all": True,
            "givenname": first_name,
            "sn": last_name,
            "cn": full_name,
            "displayname": display_name,
            "noprivate": noprivate,
            "mail": mail,
            "title": job_title,
            "nsaccountlock": disabled,
            "random": random_pass,
            "homedirectory": home_directory,
            "loginshell": login_shell,
            "userpassword": user_password,
            "telephonenumber": telephone_number,
            "gidnumber": gidnumber,
            "uidnumber": uidnumber,
        }
        params.update(kwargs)
        return self.__execute_freeipa(f"user {username} created ", "user_add", username, params)

    def user_mod(self, username, email=None, ramal=None, **kwargs):
        params = {"all": True, "mail": email, "telephonenumber":ramal }
        params.update(kwargs)
        return  self.__execute_freeipa(f"user {username} modified", "user_mod",  username, params)

    def user_delete(self, username, skip_errors=False, soft_delete=False):
        params = {  "continue": skip_errors,  "preserve": soft_delete}
        return self.__execute_freeipa(f"user {username} deleted", "user_del", username, params)

    def user_find_show(self, criteria=None, allattr=False,  raw=False, **kwargs):
        params = { "all": allattr, "raw": raw}
        params.update(kwargs)
        return self._request("user_find", criteria, params)

    def group_add_member_group(self, group, users=None, groups=None, **kwargs):
        params = { "all": True, "raw": True, "user": users, "group": groups }
        params.update(kwargs)
        return self.__execute_freeipa(f"added {users} on group {group}", "group_add_member", group, params)

    def sudorule_create(self, sudorule, description):
        params = {"description": description}
        return self.__execute_freeipa(f"sudorule {sudorule} created", "sudorule_add", sudorule, params)

    def sudorule_add_option(self, sudorule, option):
        params = {"ipasudoopt": option}
        return self.__execute_freeipa(f"sudorule {sudorule} add option {option}", "sudorule_add_option", sudorule, params)

    def sudorule_add_members_group(self, sudorule, group):
        params = {"group": group}
        return self.__execute_freeipa(f"added {group} on sudorule {sudorule}", "sudorule_add_user", sudorule, params)

    def hostgroup_add_member_host(self, hostgroup, host):
        params = { "all": True, "raw": True, "host": host}
        return self.__execute_freeipa(f"added {host} on hostgroup {hostgroup}", "hostgroup_add_member", hostgroup, params)

    def sudorule_add_members_host(self, sudorule, host=None, hostgroups=None):
        params = {"host": host, "hostgroup": hostgroups}
        return self.__execute_freeipa(f"added {host} on sudorule {sudorule}", "sudorule_add_host", sudorule, params)

    def sudorule_remove_members_host(self, sudorule, host=None, hostgroups=None):
        params = {"host": host, "hostgroup": hostgroups}
        return self.__execute_freeipa(f"removed {hostgroups} on sudorule {sudorule}", "sudorule_remove_host", sudorule, params)

    def sudorule_add_runasuser(self, sudorule, user):
        params = {"user": user}
        return self.__execute_freeipa(f"added {user} on sudorule {sudorule}", "sudorule_add_runasuser", sudorule, params)

    def sudorule_add_allow_command(self, sudorule):
        params = {"sudocmdgroup": "sudo_cmd_default_usuarios"}
        return self.__execute_freeipa(f"added sudocmdgroup sudo_cmd_default_usuarios on sudorule {sudorule}", "sudorule_add_allow_command", sudorule, params)

    def sudorule_delete(self, sudorule):
        return self.__execute_freeipa(f"sudorule {sudorule} deleted", "sudorule_del", sudorule)

    def sudorule_find_count(self, criteria=None, allattr=True, no_members=False, sizelimit=0, raw=False, **kwargs):
        params = { "all": allattr,  "no_members": no_members,  "sizelimit": sizelimit, "raw": raw}
        params.update(kwargs)
        return self._request("sudorule_find", criteria, params)["count"]
    
    def sudorule_find_show(self, criteria=None, allattr=True, no_members=False, rights=False, raw=False, **kwargs):
        params = { "all": allattr, "no_members": no_members, "rights": rights, "raw": raw}
        params.update(kwargs)
        return self._request("sudorule_show", criteria, params)

    def host_find_count(self, criteria=None, **kwargs):
        params = {"all": True, "sizelimit": 0}
        params.update(kwargs)
        return self._request("host_find", criteria, params)["count"]

    
    def host_find_show(self, criteria=None, allattr=False, rights=False,  raw=False, **kwargs):
        params = { "all": allattr, "rights": rights, "raw": raw}
        params.update(kwargs)
        return self._request("host_show", criteria, params)

    def automountlocation_find_count(self, criteria=None, **kwargs):
        params = {"all": True, "sizelimit": 0}
        params.update(kwargs)
        return self._request("automountlocation_find", criteria, params)["count"]
    
    def automountmap_find_count(self, criteria=None, automountmapname=None, **kwargs):
        params = {"all": True, "sizelimit": 0, "automountmapname": automountmapname}
        params.update(kwargs)
        return self._request("automountmap_find", criteria, params)["count"]

    def automountkey_find_count(self, automountlocationcn, automountmapautomountmapname):
        params = {"all": True, "sizelimit": 0, 'automountmapautomountmapname':automountmapautomountmapname}
        return self._request("automountkey_find", automountlocationcn, params)["count"]

    def host_create(self, host, description=None, force=True, **kwargs):
        params = {"all": True, "description": description, "force":force}
        params.update(kwargs)
        return  self.__execute_freeipa(f"host {host} created ", "host_add",  host, params)

    def host_delete(self, host):
        return  self.__execute_freeipa(f"host {host} deleted", "host_del",  host)

    def host_mod(self, host, description=None, **kwargs):
        params = {"all": True, "description": description}
        params.update(kwargs)
        return  self.__execute_freeipa(f"host {host} modified", "host_mod",  host, params)

    def hbacrule_create(self, hbac, description, **kwargs):
        params = {"description": description}
        params.update(kwargs)
        return  self.__execute_freeipa(f"hbacrule {hbac} created ", "hbacrule_add", hbac, params)

    def hbacrule_add_members_host(self, hbac, host=None, hostgroups=None):
        params = {"host": host, "hostgroup": hostgroups}
        return  self.__execute_freeipa(f"added host {host} in hbacrule {hbac}", "hbacrule_add_host", hbac, params)

    def hbacrule_add_members_service(self, hbac, hbacsvcs=None, hbacsvcgroups=None):
        params = {"hbacsvc": hbacsvcgroups, "hbacsvcgroup": hbacsvcgroups}
        return  self.__execute_freeipa(f"service added in the hbacrule {hbac} ", "hbacrule_add_service", hbac, params)

    def hbacrule_add_members_user(self, hbac, user):
        params = {"user": user}
        return  self.__execute_freeipa(f"{user} added in the hbacrule {hbac} ", "hbacrule_add_user", hbac, params)

    def automountlocation_add(self, automountlocation):
        return  self.__execute_freeipa(f"automountlocation {automountlocation} add ", "automountlocation_add", automountlocation)

    def automountlocation_del(self, automountlocation):
        return  self.__execute_freeipa(f"automountlocation {automountlocation} del", "automountlocation_del", automountlocation)

    def automountmap_add_indirect(self, automountlocation, automountmap, key, allattr=False,  raw=False,  **kwargs):
        params = {  "key": key, "all": allattr,   "raw": raw, "automountmapname": automountmap }
        params.update(kwargs)
        message = f"automountmap {automountmap} added in the {automountlocation} "
        return  self.__execute_freeipa(message, "automountmap_add_indirect", automountlocation, params)

    def automountkey_add(self, automountlocation, automountmap, automountkey, automountinformation, allattr=False,  raw=False, **kwargs):
        params = { "all": allattr, "raw": raw, "automountmapautomountmapname": automountmap, "automountkey": automountkey, "automountinformation": automountinformation }
        params.update(kwargs)
        message = f"automountkey {automountkey} added in the {automountmap} "
        return  self.__execute_freeipa(message, "automountkey_add", automountlocation, params)

    def automountmap_del(self, automountlocation, automountmap):
        message = f"automountmap {automountmap} deleted in the {automountlocation}"
        params = {"automountmapname": automountmap}
        return  self.__execute_freeipa(message, "automountmap_del", automountlocation, params)

    def automountkey_del(self, automountlocation, automountmap, key, automountinformation ):
        message = f"automountkey {key} deleted in the {automountmap} in {automountlocation}"
        params = {"automountmapautomountmapname": automountmap, 'automountkey':key, 'continue': True, "automountinformation":automountinformation}
        return  self.__execute_freeipa(message, "automountkey_del", automountlocation, params)

    def hbacrule_remove_members_host(self, hbac, host=None, hostgroups=None):
        params = {"host": host, "hostgroup": hostgroups}
        message = f"{host} removed from hbacrule {hbac} ",
        return  self.__execute_freeipa(message, "hbacrule_remove_host",  hbac, params)

    # def hbacrule_remove_members_user(self, hbac, user):
    #     params = {"user": user,}
    #     return  self.__execute_freeipa(f"{user} removed from hbacrule {hbac} ", "hbacrule_remove_user",  hbac, params)

    def hbacrule_show(self, criteria=None, allattr=True, rights=False,  raw=False, **kwargs):
        params = { "all": allattr, "rights": rights, "raw": raw}
        params.update(kwargs)
        return self._request("hbacrule_show", criteria, params)

    def hbacrule_find_count(self, criteria=None, allattr=True, no_members=False, sizelimit=0, raw=False, **kwargs):
        params = {  "all": allattr, "no_members": no_members,  "sizelimit": sizelimit,  "raw": raw}
        params.update(kwargs)
        return self._request("hbacrule_find", criteria, params)["count"]

    def hbacrule_delete(self, hbac):
        return  self.__execute_freeipa(f"hbacrule {hbac} deleted", "hbacrule_del", hbac)

    def user_find_count(self, criteria=None, **kwargs):
        params = {"all": True, "sizelimit": 0}
        params.update(kwargs)
        return self._request("user_find", criteria, params)["count"]