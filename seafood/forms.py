"""
Forms for the Seafood app.
"""

from django import forms
from .models import CallbackRequest


class CallbackRequestForm(forms.ModelForm):
    """
    Form for creating a callback request.
    """
    class Meta:
        model = CallbackRequest
        fields = ['name', 'phone', 'product', 'preferred_time', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ваше ім\'я',
                'required': True,
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+38 (0XX) XXX-XX-XX',
                'type': 'tel',
                'required': True,
            }),
            'product': forms.Select(attrs={
                'class': 'form-control',
            }),
            'preferred_time': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Час звернення (наприклад: 14:00)',
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Ваше повідомлення',
                'rows': 4,
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make product optional
        self.fields['product'].required = False
        self.fields['preferred_time'].required = False
        self.fields['message'].required = False
