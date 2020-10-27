from django.urls import path
from django.views.generic import TemplateView
from apps.monitoramento.views.monitoramento import FerramentaView
from apps.monitoramento.views.storage import NetappLisView, NetappView, NetappModelView, XE6QuotaListView, XE6QuotaView
from apps.monitoramento.views.uso import SupercomputadorHistView, SupercomputadorNodesView, SupercomputadorView
from apps.monitoramento.views.vm import XenPoolListView, XenPoolView, XenView

app_name = "monitoramento"

urlpatterns = [
    path("ferramentas/", FerramentaView.as_view(), name="ferramentas"),
    path("rnp/", TemplateView.as_view(template_name="monitoramento/rnp/rnp_home.html"), name="rnp_home"),
    
    path("xen/pool/", XenView.as_view(), name="vms_xen"),
    path("xen/pool/<int:pk>", XenPoolView.as_view(), name="vms_xen_pool"),
    path("xen/pool/<int:pk>/list/", XenPoolListView.as_view(), name="vms_xen_pool_list"),

    path("netapp/", NetappView.as_view(), name="storage_netapp"),
    path("netapp/<int:pk>/model/", NetappModelView.as_view(), name="storage_netapp_model"),
    path("netapp/<int:pk>/list/", NetappLisView.as_view(), name="storage_netapp_list"),

    path("xe6quota/", XE6QuotaView.as_view(), name="storage_xe6quota"),
    path("xe6quota/<int:pk>/list/", XE6QuotaListView.as_view(), name="storage_xe6quota_list"),
    
    path("supercomputador/", SupercomputadorView.as_view(), name="uso_supercomputador"),
    path("supercomputador/<int:pk>/nodes/", SupercomputadorNodesView.as_view(), name="uso_supercomputador_nodes"),
    path("supercomputador/<int:pk>/hist/", SupercomputadorHistView.as_view(), name="uso_supercomputador_hist"),
]
