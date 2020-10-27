from django.urls import path
from apps.colaborador.views import InicioView, NovoView, SucessoView
from django.contrib.auth import views as auth_views

app_name = "colaborador_open"

urlpatterns = [
    path("inicio/", InicioView.as_view(), name="inicio"),
    path("inicio/novo/", NovoView.as_view(), name="novo"),
    path("sucesso/", SucessoView.as_view(), name="sucesso"),
]
