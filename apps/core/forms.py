from django import forms
from django.db.models import Q
from django.forms.models import ModelChoiceField

from apps.colaborador.models import Colaborador
from apps.core.models import Divisao, GrupoTrabalho, ResponsavelGrupoTrabalho
from django.core.exceptions import ValidationError


class UserChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return f"{obj.first_name} {obj.last_name} | {obj.email}"


class GrupoTrabalhoForm(forms.ModelForm):
    share = forms.BooleanField(required=False)
    operacional = forms.BooleanField(required=False, label="Operacional")
    desenvolvimento = forms.BooleanField(required=False, label="Desenvolvimento")
    pesquisa = forms.BooleanField(required=False, label="Pesquisa")
    documento = forms.BooleanField(required=False, label="Documento")

    class Meta:
        model = GrupoTrabalho
        fields = "__all__"


class ResponsavelGrupoTrabalhoInLineForm(forms.ModelForm):
    responsavel = forms.ModelChoiceField(queryset=Colaborador.objects.filter(is_staff=True, groups__name="Responsavel").distinct(), label="Responsável", widget=forms.Select(attrs={"data-live-search": "True"}))

    class Meta:
        model = ResponsavelGrupoTrabalho
        fields = ("responsavel",)


class DivisaoForm(forms.ModelForm):
    chefe = UserChoiceField(queryset=Colaborador.objects.filter(is_staff=True, groups__name="Chefia da Divisão").distinct(), required=True)
    chefe_substituto = UserChoiceField(queryset=Colaborador.objects.filter(is_staff=True, groups__name="Chefia da Divisão").distinct(), required=True)

    chefe_ativo = forms.BooleanField(required=False, label="Chefe Ativo")
    chefe_substituto_ativo = forms.BooleanField(required=False, label="Chefe Substituto Ativo")
    email = forms.EmailField(required=True, label="Email Secretaria")

    class Meta:
        model = Divisao
        fields = ['divisao', 'divisao_completo', 'email', 'coordenacao', 'chefe', 'chefe_ativo','chefe_substituto', 'chefe_substituto_ativo']

    def clean_chefe_ativo(self):
        chefe_ativo = self.cleaned_data.get("chefe_ativo")
        chefe_substituto_ativo = self.cleaned_data.get("chefe_substituto_ativo")
        if ( not chefe_ativo and not chefe_substituto_ativo):
            raise ValidationError("Precisa ter um chefe ativo")
        return chefe_ativo

    def clean_chefe_substituto_ativo(self):
        chefe_ativo = self.cleaned_data.get("chefe_ativo")
        chefe_substituto_ativo = self.cleaned_data.get("chefe_substituto_ativo")
        if ( not chefe_ativo and not chefe_substituto_ativo):
            raise ValidationError("Precisa ter um chefe ativo")
        return chefe_substituto_ativo