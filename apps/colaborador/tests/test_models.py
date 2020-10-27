import pytest
from mixer.backend.django import mixer
from apps.core.models import Divisao, Group
from apps.colaborador.models import Colaborador, Vinculo
from apps.core.models import GrupoTrabalho, GrupoAcesso
from django.core.exceptions import ValidationError

pytestmark = pytest.mark.django_db


@pytest.mark.django_db
def test_create_colaborador() -> None:
    colaborador = mixer.blend(Colaborador, first_name="Colaborador", last_name="Fulano de tal")
    colaborador.username = None
    colaborador.clean()
    colaborador.save()
    assert colaborador.username == "colaborador.tal"
    colaborador = Colaborador.objects.get(username="colaborador.tal")
    assert str(colaborador) == "Colaborador Fulano de tal"

    colaborador_1 = mixer.blend(Colaborador, first_name="Colaborador", last_name="Fulano de tal")
    colaborador_1.username = None
    colaborador_1.clean()
    colaborador_1.save()
    assert colaborador_1.username == "colaborador.fulano"

    colaborador_2 = mixer.blend(Colaborador, first_name="Colaborador", last_name="Fulano de tal")
    colaborador_2.username = None
    colaborador_2.clean()
    colaborador_2.save()
    assert colaborador_2.username == "colaborador.tal_"

    colaborador_3 = mixer.blend(Colaborador, first_name="Marcelo", last_name="Costa", email="fulano.colaborador@inpe.br")
    colaborador_3.username = None
    colaborador_3.clean()
    colaborador_3.save()
    assert colaborador_3.username == "fulano.colaborador"

    colaborador_4 = mixer.blend(Colaborador, first_name="Colaborador", last_name="Fulano de tal", email="colaborador.fulano@inpe.br")
    colaborador_4.username = None
    with pytest.raises(ValidationError) as excinfo:
        colaborador_4.clean()
        assert "Username já existe" in str(excinfo.value)


def test_detail_colaborador() -> None:
    colaborador = mixer.blend(Colaborador, first_name="Colaborador", last_name="Fulano de tal", cpf="999.999.999-99", documento_tipo="RG", documento="88.888.888-8")
    assert colaborador.full_name == "Colaborador Fulano de tal"
    assert colaborador.get_documento_principal() == "CPF: <b>999.999.999-99</b>"
    colaborador.cpf = None
    assert colaborador.get_documento_principal() == "RG: <b>88.888.888-8</b>"


def test_colaborador_chefia() -> None:
    colaborador = mixer.blend(Colaborador)
    colaborador.save()
    colaborador.chefia()
    assert colaborador.is_active == True


def test_colaborador_suporte() -> None:
    group = mixer.blend(Group, name="Colaborador")
    group.save()
    colaborador = mixer.blend(Colaborador)
    colaborador.save()
    colaborador.suporte()
    assert colaborador.is_staff == True
    assert colaborador.groups.filter(name="Colaborador").exists() == True


def test_create_vinculo() -> None:
    vinculos = mixer.cycle(4).blend(Vinculo, vinculo=(vinculo for vinculo in ("Bolsista", "Servidor", "Terceiro", "Estagiário")))
    assert vinculos[3].vinculo == "Estagiário"
    assert str(vinculos[3]) == "Estagiário"


@pytest.mark.django_db
def test_create_colaborador_grupoacesso() -> None:
    colaborador = mixer.blend(Colaborador)
    grupo = mixer.blend(GrupoTrabalho, grupo="Grupo dados", grupo_sistema="dados")
    grupo_acesso = GrupoAcesso(tipo="Desenvolvimento", grupo_trabalho=grupo)
    grupo_acesso.save()
    colaborador_grupoacesso = colaborador.colaboradorgrupoacesso_set.create(grupo_acesso=grupo_acesso)
    assert str(colaborador_grupoacesso).upper() == str(grupo_acesso)
    assert colaborador_grupoacesso.status() == "Aguardando Aprovação"
    colaborador_grupoacesso.aprovacao = 1
    assert colaborador_grupoacesso.status() == "Acesso Aprovado"
