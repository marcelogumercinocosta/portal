import pytest
from mixer.backend.django import mixer
from apps.colaborador.models import Colaborador
from apps.core.models import Divisao, GrupoTrabalho, Divisao, GrupoAcesso, Group
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.auth.models import Permission


pytestmark = pytest.mark.django_db

@pytest.mark.django_db
@pytest.fixture(autouse=True)
def set_permission() -> None:
    group = mixer.blend(Group, name="Chefia")
    chefia_colaborador = Permission.objects.get(codename="chefia_colaborador")
    group.permissions.add(chefia_colaborador)
    group.save()

    group = mixer.blend(Group, name="Colaborador")
    group.save()

@pytest.fixture
@pytest.mark.django_db
def chefia_1() -> Colaborador:
    chefia = mixer.blend(Colaborador, first_name="Chefe1", last_name="Divisao", email="chefe1.divisao@inpe.br")
    chefia.groups.add(Group.objects.get(name="Chefia"))
    chefia.save()
    return chefia

@pytest.fixture
@pytest.mark.django_db
def chefia_2() -> Colaborador:
    chefia = mixer.blend(Colaborador, first_name="Chefe2", last_name="Divisao", email="chefe2.divisao@inpe.br")
    chefia.groups.add(Group.objects.get(name="Chefia"))
    chefia.save()
    return chefia

def test_create_divisao(chefia_1, chefia_2) -> None:
    divisao = mixer.blend(Divisao, divisao="DIV", chefe=chefia_1, chefe_substituto=chefia_2, email="divisao@inpe.br")
    divisao.chefe_ativo = True
    divisao.save()
    assert divisao.color == "blue"
    assert str(divisao) == "DIV"
    divisao.chefe_substituto_ativo = True
    assert divisao.emails() == [divisao.email, chefia_1.email, chefia_2.email ]

@pytest.mark.django_db
def test_create_grupo_trabalho() -> None:
    divisao = mixer.blend(Divisao)
    grupo_trabalho = mixer.blend(GrupoTrabalho, grupo="Grupo dados", grupo_sistema="dados", divisao=divisao)
    grupo_trabalho.confirmacao = True
    grupo_trabalho.save()
    assert grupo_trabalho.get_sudo() == "sudo_dados"
    assert grupo_trabalho.confirmacao == False
    assert str(grupo_trabalho) == (f"{divisao.divisao} | GRUPO DADOS")
    grupo_trabalho.save_confirm()
    assert grupo_trabalho.confirmacao == True
    with pytest.raises(IntegrityError) as excinfo:
        mixer.blend(GrupoTrabalho, grupo="Grupo dados", grupo_sistema="dados", divisao=divisao)
        assert "IntegrityError" in str(excinfo.value)


def test_create_grupo_acesso() -> None:
    grupo = mixer.blend(GrupoTrabalho, grupo="Grupo dados", grupo_sistema="dados")
    grupo_acesso = GrupoAcesso(tipo="Desenvolvimento", grupo_trabalho=grupo)
    assert str(grupo_acesso) == "DADOS | DESENVOLVIMENTO" 
    assert grupo_acesso.description == "HBAC Rule de DESENVOLVIMENTO do Grupo DADOS"
    assert grupo_acesso.hbac_freeipa == "hbac_srv_dados_dev"


def test_set_responsavel() -> None:
    grupo = mixer.blend(GrupoTrabalho, grupo="Grupo")
    colaborador = mixer.blend(Colaborador, first_name="Colaborador", last_name="Fulano de tal")
    responsavel_grupotrabalho = grupo.responsavelgrupotrabalho_set.create(responsavel=colaborador)
    assert str(responsavel_grupotrabalho) == "Colaborador Fulano de tal | Grupo"
