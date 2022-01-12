from django.db.models.base import Model
from django.forms import ModelForm,TextInput, Select, DateInput
from django.forms.fields import DateField
from home.models import Asset, Portfolio

class AssetForm(ModelForm):
    class Meta:
        model = Asset
        exclude = ('current_price',)
        widgets = {
            'name': TextInput(attrs={
                'type': 'None',
                'class': "form-control",
                'style': 'max-width: 300px;',
                'placeholder': 'BTCUSD'
                }),
            'purchase_date': DateInput(attrs={
                'class': "form-control",
                }),
            'size': TextInput(attrs={
                'class': "form-control",
                }),
            'entry_price': TextInput(attrs={
                'class': "form-control",
                }),              
            'type': Select(attrs={
                'class': "form-control",
                'onchange': "showOptionsFields()",
                'id':'asset-type'
                }),
            'portfolio': Select(attrs={
                'class': "form-control",
                }),    
            'option_type': Select(attrs={
                'class': "form-control",
                }),
            'option_strike': TextInput(attrs={
                'class': "form-control",
                }),
            'option_expiry': DateInput(attrs={
                'class': "form-control",
                }),                      
        }

class PortfolioForm(ModelForm):
    class Meta:
        model = Portfolio
        fields = '__all__'
        widgets = {
            'name': TextInput(attrs={
                'class': "form-control",
                }),
            'type': Select(attrs={
                'class': "form-control",
                }),    
            'cash': TextInput(attrs={
                'class': "form-control",
                }),             
        }