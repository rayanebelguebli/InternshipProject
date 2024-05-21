from django import forms
from .models import UploadedModel, Equipment

class UploadModelForm(forms.ModelForm):
    equipement = forms.ModelChoiceField(queryset=Equipment.objects.all(), label='Equipement', to_field_name='id')

    class Meta:
        model = UploadedModel
        fields = ['file', 'nomenclature', 'equipement']

    def __init__(self, *args, **kwargs):
        super(UploadModelForm, self).__init__(*args, **kwargs)
        self.fields['equipement'].queryset = Equipment.objects.all().order_by('name')
        self.fields['equipement'].required = True
