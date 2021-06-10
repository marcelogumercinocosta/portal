
from apps.colaborador.models import Colaborador
from django import forms
from django.db.models import Q
from apps.noc.models import Checklist, ChecklistResponsaveis, ChecklistServidorNagiosServico

class ChechlistForm(forms.ModelForm):
    
    TURNO = (
        ("Turno 1", "Turno 1"),
        ("Turno 2", "Turno 2"),
        ("Turno 3", "Turno 3"),
        ("Turno 4", "Turno 4"),
        ("Turno Extra", "Turno Extra"),
    )
    turno = forms.ChoiceField(choices = TURNO, initial='Analisando') 

    class Meta:
        model = Checklist
        fields = ["turno","outros"]
        widgets = {"outros": forms.Textarea(attrs={"cols": 80, "rows": 4})}


class ChechlistResponsaveisInlineForm(forms.ModelForm):
    responsavel = forms.ModelChoiceField(queryset=Colaborador.objects.filter(Q(groups__name="NOC") | Q(groups__name="Servicedesk") ).distinct(), label="Responsável", widget=forms.Select(attrs={"data-live-search": "True"}),required=False,)

    class Meta:
        model = ChecklistResponsaveis
        fields = ["responsavel"]

class ChecklistServidorNagiosServicoInlineForm(forms.ModelForm):
    class Meta:
        model = ChecklistServidorNagiosServico
        fields = ["alerta_monitoramento"]
        widgets = {"alerta_monitoramento": forms.Select(attrs={"data-live-search": "True"})}