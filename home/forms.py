from django.db.models.base import Model
from django.forms import ModelForm,TextInput
from home.models import Asset

class AssetForm(ModelForm):
    class Meta:
        model = Asset
        fields = '__all__'
        widgets = {
            'name': TextInput(attrs={
                'type': 'None',
                'class': "autocomplete",
                'style': 'max-width: 300px;',
                'placeholder': 'Name'
                }),
        }
