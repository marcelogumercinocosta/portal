import time

import pytest
from django.contrib.auth.models import Group, Permission
from mixer.backend.django import mixer
from apps.infra.forms import HostnameChoiceField, HostnameIPForm, ServidorForm, EquipamentoParteForm, OcorrenciaInLineForm
from apps.infra.models import HostnameIP, Rede, Servidor, EquipamentoParte, Ocorrencia
from apps.core.models import Predio

pytestmark = pytest.mark.django_db


def test_hostname_choicefield_error() -> None:
    rede =  mixer.blend(Rede, ip="192.168.0", rede="Rede do Servidor")
    hostname =  mixer.blend(HostnameIP, hostname="servidor1",  ip="192.168.0.12",  reservado=False, tipo=rede)
    choice = HostnameChoiceField(HostnameIP.objects.all())
    assert choice.label_from_instance(hostname) == "servidor1 | 192.168.0.12 | Rede do Servidor" 


@pytest.mark.django_db
def test_form_hostname() -> None:
    rede =  mixer.blend(Rede, ip="192.168.0", rede="Rede do Servidor")
    data = {"tipo": rede.id, "ip":"192.168.0.12", "hostname":"servidor1"}
    form = HostnameIPForm(data=data)
    assert form.is_valid() is True
    data.update({"ip": "10.10.0.12"})
    form = HostnameIPForm(data=data)
    assert form.is_valid() is False
    assert form.errors == {'ip': ['Precisa de um ip válido']}


@pytest.mark.django_db
def test_form_servidor() -> None:
    predio =  mixer.blend(Predio)
    rede =  mixer.blend(Rede, ip="192.168.0", rede="Rede do Servidor")
    hostname =  mixer.blend(HostnameIP, hostname="servidor1",  ip="192.168.0.12",  reservado=False, tipo=rede)

    data = mixer.blend(Servidor, nome=hostname.id, descricao="Servidor de TESTE", tipo_uso='OPERACIONAL', tipo='Servidor Físico', patrimonio='').__dict__
    data.update({"predio":predio.pk}) 
    form = ServidorForm(data=data)
    assert form.fields["patrimonio"].required == True 
    assert form.is_valid() is False

    data = mixer.blend(Servidor, nome=hostname.id, descricao="Servidor de TESTE", tipo_uso='OPERACIONAL', tipo='Servidor Virtual').__dict__
    data.update({"predio":predio.pk}) 
    form = ServidorForm(data=data)
    assert form.is_valid() is True
    assert form.fields["patrimonio"].required == False 


@pytest.mark.django_db
def test_form_equipamento_parte() -> None:
    equipamento =  mixer.blend(EquipamentoParte,).__dict__
    form = EquipamentoParteForm(data=equipamento)
    assert form.is_valid() is False
    assert form.fields["patrimonio"].required == True 

def test_form_ocorrencia() -> None:
    equipamento = mixer.blend(EquipamentoParte,)
    ocorrencia = mixer.blend(Ocorrencia, descricao="teste", ocorrencia='100', equipamento=equipamento)
    data = ocorrencia.__dict__
    data.update({"equipamento": equipamento.id})
    form = OcorrenciaInLineForm(data=data)
    tste = form.fields["ocorrencia"].widget.attrs["readonly"]
    assert form.fields["ocorrencia"].widget.attrs["readonly"] == "readonly" 