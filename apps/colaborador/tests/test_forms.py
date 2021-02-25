import pytest

from apps.colaborador.forms import ColaboradorForm, SecretariaNegarForm, ResponsavelNegarForm, DivisaoChoiceField
from apps.core.tests.base import *

pytestmark = pytest.mark.django_db


@pytest.mark.django_db
def test_form_colaborador_valido(responsavel_grupo, colaborador) -> None:
    
    data = colaborador.__dict__
    data.update(
        {
            "check_me_out1": True,
            "check_me_out2": True,
            "check_me_out3": True,
            "documento_tipo": "RG",
            "estado_civil": "Solteiro",
            "sexo": "Masculino",
            "predio": colaborador.predio.id,
            "vinculo": colaborador.vinculo.id,
            "divisao": colaborador.divisao.id,
            "responsavel": responsavel_grupo.id,
            "email": "fulano2@test.com",
        }
    )
    form = ColaboradorForm(data=data)
    colaborador_save = form.save_sendmail("http", "sss.cptec.inpe.br")
    assert colaborador_save.first_name == colaborador.first_name
    assert form.is_valid() is True


def test_form_colaborador_erro(colaborador) -> None:
    colaborador.email = "fulano@test.com"
    colaborador.save()
    form = ColaboradorForm(data={})
    assert form.is_valid() is False
    data = {"email": "fulano@test.com"}
    form = ColaboradorForm(data=data)
    assert form.errors["last_name"] == ["Este campo é obrigatório."]
    assert form.errors["email"] == ["Email já existe"]


def test_form_secretaria_negar_colaborador_ok(colaborador) -> None:
    colaborador.is_active = False
    colaborador.save()
    form = SecretariaNegarForm(data={"colaborador": colaborador.id, "motivo": "teste"})
    assert form.is_valid() is True
    assert form.cleaned_data.get("motivo") == "teste"
    assert form.colaborador_obj.id == colaborador.id
    colaborador_removido = form.sendmail()
    assert colaborador_removido.id == colaborador.id


def test_form_secretaria_negar_colaborador_erro_id() -> None:
    form = SecretariaNegarForm(data={"colaborador": 0, "motivo": None})
    assert form.is_valid() is False
    assert form.errors["colaborador"] == ["Colaborador não encontrado"]


def test_form_responsavel_negar_colaborador_erro_id() -> None:
    form = ResponsavelNegarForm(data={"colaborador_grupoacesso": 120, "motivo": "teste"})
    assert form.is_valid() is False
    assert form.errors["colaborador_grupoacesso"] == ["Solicitação não encontrada"]

def test_form_field_divisao() -> None:
    divisao = mixer.blend(Divisao)
    choice = DivisaoChoiceField(Divisao.objects.all())
    assert choice.label_from_instance(divisao) == f"{divisao.divisao} - {divisao.divisao_completo}"