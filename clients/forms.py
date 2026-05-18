from django import forms
from django.contrib.auth import get_user_model

from .models import ClientFolder
from .models import ClientFile
from .models import ClientFileComment


class ClientFolderForm(forms.ModelForm):
    class Meta:
        model = ClientFolder

        fields = [
            'client_name',
            'client_email',
            'notes',
        ]

        widgets = {
            'client_name': forms.TextInput(attrs={'class': 'form-control'}),
            'client_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }


class StaffClientFolderForm(forms.ModelForm):
    owner = forms.ModelChoiceField(
        queryset=get_user_model().objects.all().order_by('username'),
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = ClientFolder

        fields = [
            'owner',
            'client_name',
            'client_email',
            'notes',
        ]

        widgets = {
            'client_name': forms.TextInput(attrs={'class': 'form-control'}),
            'client_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
        }


class ClientFileForm(forms.ModelForm):
    class Meta:
        model = ClientFile

        fields = [
            'title',
            'subfolder',
            'uploaded_file',
        ]

        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'subfolder': forms.Select(attrs={'class': 'form-control'}),
            'uploaded_file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }


class MoveClientFileForm(forms.ModelForm):
    class Meta:
        model = ClientFile

        fields = [
            'subfolder',
        ]

        widgets = {
            'subfolder': forms.Select(attrs={'class': 'form-control'}),
        }


class ReassignClientFolderForm(forms.ModelForm):
    owner = forms.ModelChoiceField(
        queryset=get_user_model().objects.all().order_by('username'),
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = ClientFolder

        fields = [
            'owner',
        ]


class ClientFileCommentForm(forms.ModelForm):
    class Meta:
        model = ClientFileComment

        fields = [
            'comment',
        ]

        widgets = {
            'comment': forms.Textarea(
                attrs={
                    'class': 'form-control',
                    'rows': 4,
                    'placeholder': 'Write a comment about this file...',
                }
            ),
        }
