from django.conf import settings
from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from apps.colaborador.views import PasswordResetConfirmView


urlpatterns = [
    path("", TemplateView.as_view(template_name="core/home.html"), name="home"),
    path("colaborador/", include("apps.colaborador.urls.noauth")),
    path("monitoramento/", include("apps.monitoramento.urls")),
    path("conta/", include("apps.colaborador.urls.auth")),
    path("admin/administrador/", include("apps.core.urls.auth")),
    path("estrutura/", include("apps.core.urls.noauth")),
    path("infra/", include("apps.infra.urls")),
    path("biblioteca/", include("apps.biblioteca.urls")),
    path("garb/", include("garb.urls")),
    path("conta/password_reset/", auth_views.PasswordResetView.as_view(html_email_template_name="registration/password_reset_email_html.html"), name="password_reset"),
    path("conta/reset/<uidb64>/<token>/", PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    path('conta/', include('django.contrib.auth.urls')),
    path('celery-progress/', include('celery_progress.urls')),
    path("admin/", admin.site.urls),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


if settings.DEBUG and "debug_toolbar" in settings.INSTALLED_APPS:
    import debug_toolbar

    urlpatterns = [path("__debug__/", include(debug_toolbar.urls)),] + urlpatterns
