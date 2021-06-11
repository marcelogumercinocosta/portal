from apps.noc.views import EnviarCheckListView
from django.urls import path

app_name = "noc"

urlpatterns = [
    path("enviar/<int:pk>/", EnviarCheckListView.as_view(), name="checklist_enviar"),
    
]



