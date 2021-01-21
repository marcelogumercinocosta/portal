from apps.core.models import GrupoPortal
import json

from django.core import serializers
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.generic import View

from apps.desk.models import Problema


class ProblemasOptionsView(View):

    def get(self, request, format=None, **kwargs):
        fila = get_object_or_404(GrupoPortal, id=kwargs["pk"])
        problemas = json.loads(serializers.serialize('json',Problema.objects.filter(grupo_portal_id=fila.pk)))
        print(problemas)
        return JsonResponse(problemas,safe=False)
