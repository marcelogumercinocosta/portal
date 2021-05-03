
from apps.biblioteca.models import Documento
import pytest
from django.test import RequestFactory
from django.urls import reverse
from apps.biblioteca.admin import DocumentoAdmin, GroupInLine
from apps.core.tests.base import *

pytestmark = pytest.mark.django_db

def test_admin_colaborador_secretaria_visualizar( admin_site, secretaria):
    documento = mixer.blend(Documento)
    documento.save()
    request = RequestFactory().get(reverse('admin:biblioteca_documento_change', args=(documento.id,)))
    request.user = secretaria
    model_admin = DocumentoAdmin(Documento, admin_site)
    model_admin.change_view(request=request, object_id=str(documento.pk))
    assert model_admin.inlines == [GroupInLine]
