import re
from django import forms
from django.db.models import Q
from django.forms import ModelChoiceField
from garb.forms import GarbForm, GarbModelForm

from apps.core.models import GrupoAcesso, GrupoTrabalho, Predio
from apps.infra.models import Equipamento, EquipamentoGrupoAcesso, EquipamentoParte, HostnameIP, Ocorrencia, Rack, Servidor, ServidorHostnameIP, StorageAreaGrupoTrabalho, Rede, TemplateComando, TemplateVM
from django.core.exceptions import ValidationError


class HostnameChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return f"{obj.hostname} | {obj.ip} | {obj.tipo.rede}"


class OcorrenciaForm(forms.ModelForm):
    class Meta:
        model = Ocorrencia
        descricao = forms.CharField()
        fields = ["equipamento", "descricao"]
        widgets = {"equipamento": forms.HiddenInput(), "descricao": forms.Textarea(attrs={"cols": 80, "rows": 2})}


class ServidorForm(forms.ModelForm):
    TIPOS_SERVIDOR = (
        ("", ""),
        ("Servidor Físico", "Servidor Físico"),
        ("Servidor Virtual", "Servidor Virtual"),
    )
    
    vm_remover = forms.BooleanField(required=False, label="Remover VM ")
    tipo = forms.ChoiceField(choices=TIPOS_SERVIDOR, )
    rack = forms.ModelChoiceField(queryset=Rack.objects.all(), label="Rack", required=False,)
    nome = HostnameChoiceField(queryset=HostnameIP.objects.filter(reservado=False).order_by('tipo'), label="Hostname", required=True, widget=forms.Select(attrs={"data-live-search": "True"}))
    vinculado = forms.ModelChoiceField(queryset=Equipamento.objects.filter(Q(tipo='storage') | Q(tipo='Supercomputador')), required=False, widget=forms.Select(attrs={"data-live-search": "True"}))

    class Meta:
        model = Servidor
        fields = ["nome", "tipo", "tipo_uso", "predio", "descricao", "marca", "modelo", "serie", "patrimonio", "garantia", "consumo", "rack", "rack_tamanho", "vinculado", "status"]

    def __init__(self, *args, **kwargs):
        super(ServidorForm, self).__init__(*args, **kwargs)
        if self.data.get("tipo") == "Servidor Virtual":
            self.fields["rack"].required = False
            self.fields["rack_tamanho"].required = False
            self.fields["marca"].required = False
            self.fields["modelo"].required = False
            self.fields["consumo"].required = False
            self.fields["serie"].required = False
            self.fields["patrimonio"].required = False


class HostnameIPForm(forms.ModelForm):
    reservado = forms.BooleanField(required=False)

    def clean_ip(self):
        ip = self.cleaned_data.get("ip")
        rede = str(self.cleaned_data.get("tipo")).split(' | ')[1]
        regular_expression_ip = re.match(r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$", ip)
        if bool(regular_expression_ip) and all(map(lambda n: 0 <= int(n) <= 255, regular_expression_ip.groups())) and rede in ip:
            return ip
        raise ValidationError("Precisa de um ip válido")

    class Meta:
        model = HostnameIP
        fields = "__all__"


class RackForm(forms.ModelForm):
    class Meta:
        model = Rack
        fields = ["marca", "modelo", "serie", "patrimonio", "predio", "consumo", "pdu1", "pdu2", "tamanho", "kvm_posicao", "posicao_linha_inicial", "posicao_linha_final", "posicao_coluna_inicial", "posicao_coluna_final"]
        widgets = {"posicao_linha_inicial": forms.HiddenInput(), "posicao_linha_final": forms.HiddenInput(), "posicao_coluna_inicial": forms.HiddenInput(), "posicao_coluna_final": forms.HiddenInput()}


class HostnameIPInLineForm(forms.ModelForm):
    hostnameip = forms.ModelChoiceField(queryset=HostnameIP.objects.filter(reservado=False))

    class Meta:
        model = ServidorHostnameIP
        fields = ["hostnameip"]
        widgets = {"hostnameip": forms.Select(attrs={"data-live-search": "True"})}


class EquipamentoParteForm(forms.ModelForm):
    rack = forms.ModelChoiceField(queryset=Rack.objects.all(), label="Rack", required=True)
    vinculado = forms.ModelChoiceField(queryset=Equipamento.objects.filter(Q(tipo='storage') | Q(tipo='Supercomputador')), required=False,)
    
    class Meta:
        model = EquipamentoParte
        fields = ["marca", "modelo","tipo_uso", "serie", "patrimonio", "predio", "garantia", "consumo", "rack", "rack_tamanho", "vinculado", "descricao"]


class StorageAreaGrupoTrabalhoInLineForm(forms.ModelForm):
    class Meta:
        model = StorageAreaGrupoTrabalho
        fields = ["storage_area", "quota"]
        widgets = {"storage_area": forms.Select(attrs={"data-live-search": "True"})}



class TemplateComandoInLineForm(forms.ModelForm):
    TIPOS_Comando = (
        ("", ""),
        (1, "Comando Inicial"),
        (2, "Comando de Rede"),
        (3, "Comando Final"),
    )

    configuracao = forms.ChoiceField(choices = TIPOS_Comando) 
    class Meta:
        model = TemplateComando
        fields = ["comando", "configuracao", "prioridade"]
        
class EquipamentoGrupoAcessoForm(forms.ModelForm):
    class Meta:
        model = EquipamentoGrupoAcesso
        fields = ["grupo_acesso"]
        widgets = {"grupo_acesso": forms.Select(attrs={"data-live-search": "True"})}


class OcorrenciaInLineForm(forms.ModelForm):
    class Meta:
        model = Ocorrencia
        fields = ["ocorrencia", "descricao", "data"]

    def __init__(self, *args, **kwargs):
        super(OcorrenciaInLineForm, self).__init__(*args, **kwargs)
        if str(self.instance.ocorrencia) != "":
            self.fields["ocorrencia"].widget.attrs["readonly"] = "readonly"
            self.fields["descricao"].widget.attrs["readonly"] = "readonly"

class AmbienteVirtualServidorInLineForm(forms.ModelForm):
    servidor = forms.ModelChoiceField(Servidor.objects.filter(tipo="Servidor Físico"), widget=forms.Select(attrs={"data-live-search": "True"}))

    class Meta:
        model = Servidor
        fields = ["servidor"]

class ServidorVMForm(GarbForm):
    CPU_CHOICES =( 
        ("1", "1"), 
        ("2", "2"), 
        ("4", "4"), 
        ("8", "8"), 
    ) 
    MEMORIA_CHOICES =( 
        ("2", "2"), 
        ("4", "4"), 
        ("8", "8"), 
        ("16", "16"), 
    ) 

    servidor = forms.IntegerField(widget=forms.HiddenInput())
    template = forms.ModelChoiceField(TemplateVM.objects.all(), widget=forms.Select(attrs={"data-live-search": "True"}))
    cpu = forms.ChoiceField(choices = CPU_CHOICES, initial='4') 
    memoria = forms.ChoiceField(label="Memória GB", initial='8', choices = MEMORIA_CHOICES) 

    class Meta:
        fieldsets = [
            ("Nova VM", {"fields": ("servidor","template", "cpu", "memoria")}),
        ]
    