import time

import pytest
from django.contrib.auth.models import Group, Permission
from mixer.backend.django import mixer
from apps.core.forms import DivisaoForm, UserChoiceField 
from apps.colaborador.models import Colaborador, Vinculo
from apps.core.models import Divisao
from django.core.exceptions import ValidationError

pytestmark = pytest.mark.django_db


@pytest.mark.django_db
@pytest.fixture(autouse=True)
def set_permission() -> None:

    group = mixer.blend(Group, name="Chefia da Divisão")
    chefia_colaborador = Permission.objects.get(codename="chefia_colaborador")
    group.permissions.add(chefia_colaborador)
    group.save()

    group = mixer.blend(Group, name="Colaborador")
    group.save()


@pytest.fixture
@pytest.mark.django_db
def chefia_1() -> Colaborador:
    chefia = mixer.blend(Colaborador, first_name="Chefe1", last_name="Divisao", email="chefe1.divisao@inpe.br", is_staff=True)
    chefia.groups.add(Group.objects.get(name="Chefia da Divisão"))
    chefia.save()
    return chefia

@pytest.fixture
@pytest.mark.django_db
def chefia_2() -> Colaborador:
    chefia = mixer.blend(Colaborador, first_name="Chefe2", last_name="Divisao", email="chefe2.divisao@inpe.br", is_staff=True)
    chefia.groups.add(Group.objects.get(name="Chefia da Divisão"))
    chefia.save()
    return chefia


@pytest.mark.django_db
def test_form_divisao_valid(chefia_1, chefia_2,) -> None:
    divisao = mixer.blend(Divisao, divisao="DIV", chefe_ativo = True, email="divisao@inpe.br")
    divisao.save()
    data = divisao.__dict__
    data.update({"chefe": chefia_1.id,"chefe_substituto":chefia_2.id,})
    form = DivisaoForm(data=data)
    assert form.is_valid() is True


@pytest.mark.django_db
def test_form_divisao_error(chefia_1, chefia_2,) -> None:
    divisao = mixer.blend(Divisao, divisao="DIV", email="divisao@inpe.br")
    divisao.save()
    data = divisao.__dict__
    data.update({"chefe": chefia_1.id,"chefe_substituto":chefia_2.id,})
    form = DivisaoForm(data=data)
    assert form.is_valid() is False
    assert form.errors == {'chefe_ativo': ['Precisa ter um chefe ativo'], 'chefe_substituto_ativo': ['Precisa ter um chefe ativo']}


def test_field_error(chefia_1) -> None:
    choice = UserChoiceField(Colaborador.objects.all())
    assert choice.label_from_instance(chefia_1) == f"{chefia_1.first_name} {chefia_1.last_name} | {chefia_1.email}"


def test_form_field_divisao() -> None:
    divisao = mixer.blend(Divisao)
    choice = DivisaoChoiceField(Divisao.objects.all())
    assert choice.label_from_instance(divisao) == f"{divisao.divisao} - {divisao.divisao_completo}"