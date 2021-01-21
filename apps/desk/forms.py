from apps.core.models import GrupoPortal
from django import forms
from apps.desk.models import Ticket, Problema


class TicketForm(forms.ModelForm):
    descricao = forms.CharField(widget=forms.Textarea, label="Descrição")
    fila =  forms.ModelChoiceField(GrupoPortal.objects.none())
    problema =  forms.ModelChoiceField(Problema.objects.none())

    class Meta:
        model = Ticket
        fields = ['fila', 'problema', 'origem', 'colaborador', 'equipamento', 'primeiro_atendimento', 'descricao' ]
        widgets = {"colaborador": forms.Select(attrs={"data-live-search": "True"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        grupos_portal_ids = set([problema.grupo_portal_id for problema in Problema.objects.all()])
        self.fields['fila'] = forms.ModelChoiceField(GrupoPortal.objects.filter(id__in=grupos_portal_ids), label="Fila de Atendimento")
        