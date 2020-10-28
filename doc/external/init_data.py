#!../env/bin/python3

import datetime
import getpass
import os
import sys

import django
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core import exceptions


def password():
    password_field = None
    while password_field is None:
        password = getpass.getpass()
        password2 = getpass.getpass('Password (again): ')
        if password != password2:
            print("Error: Your passwords didn't match.")
            # Don't validate passwords that don't match.
            continue
        if password.strip() == '':
            print("Error: Blank passwords aren't allowed.")
            # Don't validate blank passwords.
            continue
        try:
            validate_password(password2)
        except exceptions.ValidationError as err:
            print('\n'.join(err.messages))
            response = input('Bypass password validation and create user anyway? [y/N]: ')
            if response.lower() != 'y':
                continue
        password_field = password
    return password_field

def main():
    sys.path.append(os.path.abspath("./"))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", os.environ["django_settings_module"])
    django.setup()

    from django.contrib.auth.models import User, Group, Permission
    from apps.colaborador.models import Colaborador, Vinculo
    from apps.core.models import Divisao, Predio

    predio = Predio()
    predio.predio ="CPTEC"
    predio.predio_sistema ="CPT"
    predio.linhas=46
    predio.colunas=66
    predio.sensores=16
    predio.areas="(1, 36, 1, 19)/(36, 43, 1, 4)/(43, 46, 1, 30)" 
    predio.save()


    for divisao in ["SESSS", "DIDMD", "DIDOP", "DIDSA", "SESAA", "PGMET", "CG"]:
        obj_divisao = Divisao()
        obj_divisao.divisao = divisao
        obj_divisao.email = "marcelogc@gmail.com"
        obj_divisao.save()

    colaborador = Colaborador()
    colaborador.username = "admin.portal"
    colaborador.email = "sysadmin.sss@inpe.br"
    colaborador.first_name = "Administrador"
    colaborador.last_name = "do Portal"
    colaborador.data_nascimento = datetime.date.today()
    colaborador.telefone = "(12) 31868476"
    colaborador.ramal = "8476"
    colaborador.bairro = "CPTEC"
    colaborador.cidade = "Cachoeira Paulsita"
    colaborador.cep = "12630-000"
    colaborador.endereco = "Rodovia Presidente Dutra KM 41"
    colaborador.numero = "s/n"
    colaborador.estado = "SP"
    colaborador.predio_id = 1
    colaborador.data_inicio = datetime.date.today()
    colaborador.nacionalidade = "Brasileira"
    colaborador.sexo = "Masculino"
    colaborador.divisao = Divisao.objects.get(divisao='SESSS')
    colaborador.vinculo = Vinculo.objects.get(vinculo='Administrador')
    colaborador.set_password(password())
    colaborador.save()
    colaborador.is_superuser = True
    colaborador.is_active = True
    colaborador.is_staff = True
    colaborador.save()
    print(f"colaborador Save")
    
    colaborador.groups.add(Group.objects.get(name="Responsavel"))
    colaborador.groups.add(Group.objects.get(name="Secretaria"))
    colaborador.groups.add(Group.objects.get(name="Suporte"))
    colaborador.groups.add(Group.objects.get(name="Colaborador"))
    colaborador.groups.add(Group.objects.get(name="Chefia da Divisão"))
    colaborador.save()
    print(f"colaborador add Groups")

    permission_default = {'Secretaria':['change_divisao', 'view_divisao', 'view_colaborador','secretaria_colaborador'],
                        'Suporte':['add_grupotrabalho','change_grupotrabalho','delete_grupotrabalho','view_grupotrabalho','add_responsavelgrupotrabalho','change_responsavelgrupotrabalho',
                                    'delete_responsavelgrupotrabalho','view_responsavelgrupotrabalho','view_grupoacesso','view_equipamento','add_rack','change_rack','delete_rack','view_rack','add_servidor',
                                    'change_servidor','delete_servidor','view_servidor','view_supercomputador','view_storageareagrupotrabalho','add_ocorrencia','change_ocorrencia','delete_ocorrencia',
                                    'view_ocorrencia','add_hostnameip','change_hostnameip','delete_hostnameip','view_hostnameip','add_equipamentogrupoacesso','change_equipamentogrupoacesso',
                                    'delete_equipamentogrupoacesso','view_equipamentogrupoacesso','view_storagegrupoacessomontagem','add_servidorhostnameip','change_servidorhostnameip',
                                    'delete_servidorhostnameip','view_servidorhostnameip','add_equipamentoparte','change_equipamentoparte','delete_equipamentoparte','view_equipamentoparte',
                                    'change_colaborador','view_colaborador','suporte_colaborador',],
                        'Colaborador':['view_colaboradorgrupoacesso', 'view_conta'],
                        'Responsavel':['responsavel_colaborador'],}
    for key, values  in permission_default.items():
        group = Group.objects.get(name=key)
        for permission in values:
            print(f"add {permission} in {key}")
            group.permissions.add(Permission.objects.get(codename=permission))
            group.save()

    for divisao in Divisao.objects.all():
        divisao.chefe = colaborador.user_ptr
        divisao.chefe_substituto = colaborador.user_ptr
        divisao.save()

if __name__ == "__main__":
    main()


