import pytest
from apps.core.tasks import create_context, send_email_template_task, send_email_task


def test_context() -> None:
    datain = [['field1','value1'], ['field2','value2'],['field3','value3']]
    assert create_context(datain) == {'field1':'value1', 'field2':'value2', 'field3':'value3'}


def test_send_email_template_task() -> None:
    template = "colaborador/email/suporte_aviso.html"
    datain = [['field1','value1'], ['field2','value2'],['field3','value3']]
    list_send_email = ['teste@email.com']
    assert send_email_template_task('subject', template, list_send_email , datain) == ( "subject | " + " ".join(str(e) for e in list_send_email)) 


def test_send_email_task() -> None:
    list_send_email = ['teste@email.com']
    assert send_email_task('subject', 'teste da task', list_send_email) == ( "subject | " + " ".join(str(e) for e in list_send_email)) 