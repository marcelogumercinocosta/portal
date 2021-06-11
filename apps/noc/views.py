from django.core.mail import send_mail
from apps.infra.models import Ocorrencia
from django.conf import settings
from django.template.loader import get_template
from apps.noc.models import Checklist, ChecklistEmail
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import get_object_or_404, render
from django.views.generic.base import RedirectView
from django.urls import reverse_lazy
from django.contrib import messages

class EnviarCheckListView(LoginRequiredMixin, PermissionRequiredMixin, RedirectView):
    permission_required = "noc.change_checklist"

    def get_redirect_url(self, *args, **kwargs):
        checklist = get_object_or_404(Checklist, id=kwargs["pk"])
        context = {'checklist': checklist, 'ocorrencias_abertas': Ocorrencia.objects.all().exclude(status="Fechado").exclude(checklist=checklist)}
        template_email = get_template('noc/email/checklist.html').render(context)
        emails = [checklist_email.email for checklist_email in ChecklistEmail.objects.all()]
        messages.add_message(self.request, messages.SUCCESS, "Checklist enviado!")
        send_mail(f"checklist {checklist}", None, settings.EMAIL_HOST_USER, emails, html_message=template_email)
        return reverse_lazy("admin:noc_checklist_change", kwargs={"object_id": checklist.id, })
