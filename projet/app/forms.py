from django import forms
from .models import UploadedModel, Equipment

class UploadModelForm(forms.ModelForm):
    class Meta:
        model = UploadedModel
        fields = ['file', 'nomenclature', 'equipement']

    def __init__(self, *args, **kwargs):
        super(UploadModelForm, self).__init__(*args, **kwargs)
        self.fields['equipement'].queryset = Equipment.objects.all()
        self.fields['equipement'].required = True

    def clean_file(self):
        file = self.cleaned_data.get('file')
        valid_extensions = ['.obj', '.fbx', '.3ds', '.stl', '.dae']
        if not any(file.name.lower().endswith(ext) for ext in valid_extensions):
            raise forms.ValidationError("Unsupported file extension. Please upload a 3D model file.")
        return file

    def clean_nomenclature(self):
        nomenclature = self.cleaned_data.get('nomenclature')
        parts = nomenclature.split('_')
        if len(parts) != 4:
            raise forms.ValidationError("Nomenclature must follow the pattern <Source>_<Type>_<Subtype>_<Differentiator_n>.")
        source, type_, subtype, differentiator = parts
        if source.lower() == 'generico' and not source:
            raise forms.ValidationError("For generic objects, the <Source> must contain the word 'Generico'.")
        return nomenclature
