from django import forms
from .models import GeneratedDocument


class GeneratedDocumentForm(forms.ModelForm):
    class Meta:
        model = GeneratedDocument
        fields = [
            'client_name',
            'client_email',
            'document_type',
            'title',
            'description',
            'amount',
        ]

        widgets = {
            'client_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Example: Mtimkulu Consulting'}),
            'client_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'client@example.com'}),
            'document_type': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Example: Website Development Proposal'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Describe the service, agreement, invoice items, or report summary...'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }
