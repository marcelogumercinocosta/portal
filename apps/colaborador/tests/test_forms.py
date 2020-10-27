import time

import pytest
from django.contrib.auth.models import Group
from mixer.backend.django import mixer

from apps.colaborador.forms import ColaboradorForm, SuporteForm, SecretariaNegarForm, SuporteForm, ResponsavelNegarForm
from apps.colaborador.models import Colaborador, Vinculo
from apps.core.models import Divisao, Predio

pytestmark = pytest.mark.django_db


@pytest.fixture
@pytest.mark.django_db
def responsavel() -> Colaborador:
    group = mixer.blend(Group, name="Responsavel")
    group.save()
    responsavel = mixer.blend(Colaborador)
    responsavel.groups.add(Group.objects.get(name="Responsavel"))
    responsavel.save()
    return responsavel


@pytest.fixture
@pytest.mark.django_db
def colaborador() -> Colaborador:
    colaborador = mixer.blend(Colaborador, email="fulano@test.com")
    colaborador.save()
    return colaborador


@pytest.fixture
@pytest.mark.django_db
def colaborador2() -> Colaborador:
    colaborador2 = mixer.blend(Colaborador, email="tal@test.com")
    return colaborador2


@pytest.fixture
@pytest.mark.django_db
def vinculo() -> Vinculo:
    vinculo = mixer.blend(Vinculo)
    vinculo.save()
    return vinculo


@pytest.fixture
@pytest.mark.django_db
def divisao() -> Divisao:
    divisao = mixer.blend(Divisao, email="divisao@divsao.com")
    divisao.save()
    return divisao


@pytest.fixture
@pytest.mark.django_db
def predio() -> Predio:
    predio = mixer.blend(Predio)
    predio.save()
    return predio



@pytest.mark.django_db
def test_form_colaborador_valid(responsavel, colaborador2, vinculo, divisao, predio) -> None:
    data = colaborador2.__dict__
    data.update(
        {
            "check_me_out1": True,
            "check_me_out2": True,
            "check_me_out3": True,
            "documento_tipo": "RG",
            "estado_civil": "Solteiro",
            "sexo": "Masculino",
            "predio": predio.id,
            "vinculo": vinculo.id,
            "divisao": divisao.id,
            "responsavel": responsavel.id,
            "email": "fulano2@test.com",
        }
    )
    form = ColaboradorForm(data=data)
    colaborador_save = form.save_sendmail("http", "sss.cptec.inpe.br")
    assert colaborador_save.first_name == colaborador2.first_name
    assert form.is_valid() is True


def test_form_colaborador_error(colaborador) -> None:
    form = ColaboradorForm(data={})
    assert form.is_valid() is False

    data = {"email": "fulano@test.com"}
    form = ColaboradorForm(data=data)
    assert form.errors["first_name"] == ["Este campo é obrigatório."]
    assert form.errors["email"] == ["Email já existe"]


def test_form_secretaria_negar_ok(colaborador) -> None:
    form = SecretariaNegarForm(data={"colaborador": colaborador.id, "motivo": "teste"})
    assert form.is_valid() is True
    assert form.cleaned_data.get("motivo") == "teste"
    assert form.colaborador_obj.id == colaborador.id
    colaborador_removido = form.sendmail()
    assert colaborador_removido.id == colaborador.id


def test_form_secretaria_negar_error_id() -> None:
    form = SecretariaNegarForm(data={"colaborador": 0, "motivo": None})
    assert form.is_valid() is False
    assert form.errors["colaborador"] == ["Colaborador não encontrado"]


def test_form_responsavel_negar_error_id() -> None:
    form = ResponsavelNegarForm(data={"colaborador_grupoacesso": 120, "motivo": "teste"})
    assert form.is_valid() is False
    assert form.errors["colaborador_grupoacesso"] == ["Solicitação não encontrada"]