from django import forms
from .models import CallbackRequest

class CallbackRequestForm(forms.ModelForm):
    class Meta:
        model = CallbackRequest
        fields = ['name', 'phone', 'message', 'preferred_time', 'product']
        widgets = {
            'product': forms.HiddenInput(),
            'message': forms.Textarea(attrs={'rows':3, 'placeholder':'Коротко опишіть питання/побажання'}),
            'phone': forms.TextInput(attrs={'placeholder':'+380XXXXXXXXX'}),
            'name': forms.TextInput(attrs={'placeholder':'Ваше імʼя (необовʼязково)'}),
            'preferred_time': forms.TextInput(attrs={'placeholder':'Наприклад: завтра після 18:00'}),
        }
