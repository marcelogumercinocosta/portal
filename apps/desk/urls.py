from apps.desk.views import ProblemasOptionsView
from django.contrib.auth.decorators import login_required
from django.urls import path

app_name = "desk"

urlpatterns = [
    path("problema/<int:pk>/options/", ProblemasOptionsView.as_view(), name="problemas_options"),
]
