from django import forms
from django.contrib.auth import get_user_model

from clients.models import ClientFolder
from clients.models import ClientFile
from documents.models import GeneratedDocument

from .models import ServiceRequest
from .models import ServiceRequestResponse
from .models import ServiceRequestComment
from .models import PublicEnquiry


class ServiceRequestForm(forms.ModelForm):
    class Meta:
        model = ServiceRequest

        fields = [
            'title',
            'request_type',
            'priority',
            'due_date',
            'description',
            'supporting_file',
        ]

        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
            }),

            'request_type': forms.Select(attrs={
                'class': 'form-control',
            }),

            'priority': forms.Select(attrs={
                'class': 'form-control',
            }),

            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),

            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
            }),

            'supporting_file': forms.ClearableFileInput(attrs={
                'class': 'form-control',
            }),
        }


class PublicEnquiryForm(forms.ModelForm):
    class Meta:
        model = PublicEnquiry

        fields = [
            'full_name',
            'email',
            'phone_number',
            'company_name',
            'enquiry_type',
            'priority',
            'title',
            'description',
            'attachment',
        ]

        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'form-control',
            }),

            'email': forms.EmailInput(attrs={
                'class': 'form-control',
            }),

            'phone_number': forms.TextInput(attrs={
                'class': 'form-control',
            }),

            'company_name': forms.TextInput(attrs={
                'class': 'form-control',
            }),

            'enquiry_type': forms.Select(attrs={
                'class': 'form-control',
            }),

            'priority': forms.Select(attrs={
                'class': 'form-control',
            }),

            'title': forms.TextInput(attrs={
                'class': 'form-control',
            }),

            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 6,
            }),

            'attachment': forms.ClearableFileInput(attrs={
                'class': 'form-control',
            }),
        }


class StaffServiceRequestForm(forms.ModelForm):
    assigned_to = forms.ModelChoiceField(
        queryset=get_user_model().objects.all().order_by('username'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    linked_folder = forms.ModelChoiceField(
        queryset=ClientFolder.objects.all().order_by('-created_at'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    linked_file = forms.ModelChoiceField(
        queryset=ClientFile.objects.all().order_by('-uploaded_at'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    linked_document = forms.ModelChoiceField(
        queryset=GeneratedDocument.objects.all().order_by('-created_at'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = ServiceRequest

        fields = [
            'assigned_to',
            'status',
            'priority',
            'due_date',
            'linked_folder',
            'linked_file',
            'linked_document',
        ]

        widgets = {
            'status': forms.Select(attrs={
                'class': 'form-control',
            }),

            'priority': forms.Select(attrs={
                'class': 'form-control',
            }),

            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
        }


class ServiceRequestResponseForm(forms.ModelForm):
    mark_completed = forms.BooleanField(
        required=False,
        initial=True,
        label='Mark request as completed',
        widget=forms.CheckboxInput(attrs={
            'class': 'checkbox-input',
        })
    )

    class Meta:
        model = ServiceRequestResponse

        fields = [
            'response_message',
            'response_attachment',
            'response_link',
        ]

        widgets = {
            'response_message': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
            }),

            'response_attachment': forms.ClearableFileInput(attrs={
                'class': 'form-control',
            }),

            'response_link': forms.URLInput(attrs={
                'class': 'form-control',
            }),
        }


class ServiceRequestConfirmationForm(forms.ModelForm):
    class Meta:
        model = ServiceRequestResponse

        fields = [
            'confirmation_status',
            'confirmation_note',
        ]

        widgets = {
            'confirmation_status': forms.Select(attrs={
                'class': 'form-control',
            }),

            'confirmation_note': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
            }),
        }


class ServiceRequestCommentForm(forms.ModelForm):
    class Meta:
        model = ServiceRequestComment

        fields = [
            'comment',
        ]

        widgets = {
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
            }),
        }
