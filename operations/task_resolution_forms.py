from django import forms

from .models import TaskResolution


class ResolveTaskForm(forms.ModelForm):
    class Meta:
        model = TaskResolution
        fields = [
            'resolution_notes',
            'resolution_file',
            'resolution_link',
        ]

        widgets = {
            'resolution_notes': forms.Textarea(attrs={
                'placeholder': 'Explain what was completed, what was attached, and any important handover notes.',
                'rows': 6,
            }),
            'resolution_link': forms.URLInput(attrs={
                'placeholder': 'Optional external link, Google Drive link, SharePoint link, etc.',
            }),
        }
