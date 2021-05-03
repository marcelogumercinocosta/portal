from django.contrib.auth.decorators import login_required
from django.urls import path
from apps.biblioteca.views import DocumentosListView

app_name = "biblioteca"

urlpatterns = [
    path("documento/", DocumentosListView.as_view(), name="documentos"),
]
