from django import forms

from apps.calendarios.models import Calendario


class CalendarioForm(forms.ModelForm):
    class Meta:
        model = Calendario
        fields = ['nome', 'descricao']
        labels = {
            'nome': 'Nome',
            'descricao': 'Descrição',
        }
        widgets = {
            'nome': forms.TextInput(attrs={'autocomplete': 'off'}),
            'descricao': forms.Textarea(attrs={'rows': 4}),
        }
