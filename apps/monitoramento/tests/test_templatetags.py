import pytest
from apps.monitoramento.templatetags import echart_safe

def test_echart_safe() -> None:
    assert echart_safe({'t1':'False','t2':'True'}) == "{'t1': 'false', 't2': 'true'}"
