from django.contrib.auth.decorators import login_required
from django.urls import path
from apps.infra.views import CriarServidorLocalView, CriarVmProgressView, CriarVmView, DataCenterJSONView, DataCenterMapView, DataCenterRackDetailView, DataCenterView, RackQRCodeView, RackDetailView, OcorrenciaNewView, RackServerDetailView, CriarServidorLdapView, DataCenterPredioView, DataCenterMapEditView

app_name = "infra"

urlpatterns = [
    path("datacenter/", DataCenterView.as_view(), name="datacenter"),
    path("datacenter/predio/<int:pk>/", DataCenterPredioView.as_view(), name="datacenter_predio"),
    path("datacenter/map/<int:pk>/", DataCenterMapView.as_view(), name="datacenter_map"),
    path("datacenter/search", DataCenterJSONView.as_view(), name="datacenter_search"),
    path("datacenter/map/edit/<int:pk>/", login_required(DataCenterMapEditView.as_view()), name="datacenter_map_edit"),
    path("datacenter/rack/detail", DataCenterRackDetailView.as_view(), name="datacenter_rack_detail"),
    path("datacenter/rack/qrcode/<int:pk>", RackQRCodeView.as_view(), name="rack_qrcode"),
    path("datacenter/rack/qrcode/<int:pk>/detail/", RackDetailView.as_view(), name="rack_detail"),
    path("datacenter/rack/server/<int:pk>/detail/", RackServerDetailView.as_view(), name="rack_server_detail"),
    path("ocorrencia/criar/", OcorrenciaNewView.as_view(), name="ocorrencia_criar"),
    path("servidor/<int:pk>/criarservidorldap/", login_required(CriarServidorLdapView.as_view()), name="criar_servidor_ldap"),
    path("servidor/<int:pk>/criarservidorlocal/", login_required(CriarServidorLocalView.as_view()), name="criar_servidor_local"),
    path("servidor/<int:pk>/criarVM/", login_required(CriarVmView.as_view()), name="criar_vm"),
    path("servidor/<int:pk>/<template_id>/<task_id>/criarVM/progress", login_required(CriarVmProgressView.as_view()), name="criar_vm_progress"),
]
