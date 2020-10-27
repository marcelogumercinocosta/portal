import datetime
import pytest
from apps.core.templatetags import templatetags


def test_to_replace_dot() -> None:
    assert templatetags.to_replace_dot('marcelo.costa') == "marcelo_costa"


def test_to_replace_dot() -> None:
    assert templatetags.to_replace_dot('marcelo.costa') == "marcelo_costa"


def test_get_size_human() -> None:
    assert templatetags.get_size_human(13194139533312) == "12,0 TB"
    assert templatetags.get_size_human(0) == "0B"


def test_get_size_human_size() -> None:
    assert templatetags.get_size_human_size(13194139533312) == "TB"
    assert templatetags.get_size_human_size(0) == "B"


def test_get_size_human_number() -> None:
    assert templatetags.get_size_human_number(13194139533312) == "12,0"
    assert templatetags.get_size_human_number(0) == "0"


def test_get_size_human_tb() -> None:
    assert templatetags.get_size_human_TB(13194139533312) == "12,0 TB"
    assert templatetags.get_size_human_TB(0) == "0B"


def test_add_days() -> None:
    assert templatetags.add_days(10) == datetime.date.today() + datetime.timedelta(days=10)


def test_echart_safe() -> None:
    assert templatetags.echart_safe({'t1':'False','t2':'True'}) == "{'t1': 'false', 't2': 'true'}"
