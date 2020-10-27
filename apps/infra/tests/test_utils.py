import datetime
import pytest
from mixer.backend.django import mixer
from apps.infra.utils.datacenter import  DatacenterSensor, DatacenterArea
from apps.core.models import Predio

pytestmark = pytest.mark.django_db

def test_datacenter_sensores() -> None:
    predio =  mixer.blend(Predio, sensores=16, predio_sistema="CPT")
    datacebter_sensor = DatacenterSensor(predio.predio_sistema, ["AA", 19], "M", 50, 26, datetime.datetime.now())
    assert datacebter_sensor.get_status() == "yellow"
    datacebter_sensor.temperatura = 20
    assert datacebter_sensor.get_status() == "blue"
    datacebter_sensor.temperatura = 30
    assert datacebter_sensor.get_status() == "red"
    assert datacebter_sensor.get_col() == 19
    assert datacebter_sensor.get_index() == 1
    assert datacebter_sensor.get_posicao_numerico() == [19,1]
    assert str(datacebter_sensor) == "CPTAA19"

def test_datacenter_area() -> None:
    assert DatacenterArea(1, 36, 1, 19).tipo == "area_map"
