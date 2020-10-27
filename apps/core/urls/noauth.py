from django.urls import path
from apps.core.views import EstruturaGruposView, CoreStatusView

app_name = "core_open"

urlpatterns = [
    path("grupos/", EstruturaGruposView.as_view(), name="grupos"),
    path("status/", CoreStatusView.as_view(), name="status"),
]
