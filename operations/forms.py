from django import forms
from django.contrib.auth import get_user_model

from clients.models import ClientFolder
from service_requests.models import ServiceRequest

from .models import InternalTask
from .models import InternalTaskComment
from .models import OperationsAnnouncement
from .models import TaskTemplate
from .models import TaskTemplateChecklistItem
from .models import InternalTaskChecklistItem


class TaskTemplateForm(forms.ModelForm):
    class Meta:
        model = TaskTemplate

        fields = [
            'name',
            'description',
            'default_priority',
            'default_due_days',
            'is_active',
        ]

        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
            'default_priority': forms.Select(attrs={'class': 'form-control'}),
            'default_due_days': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
        }


class TaskTemplateChecklistItemForm(forms.ModelForm):
    class Meta:
        model = TaskTemplateChecklistItem

        fields = [
            'title',
            'order',
        ]

        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Example: Review client document',
            }),

            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
            }),
        }


class InternalTaskForm(forms.ModelForm):
    assigned_to = forms.ModelChoiceField(
        queryset=get_user_model().objects.all().order_by('username'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    linked_request = forms.ModelChoiceField(
        queryset=ServiceRequest.objects.all().order_by('-created_at'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    linked_client = forms.ModelChoiceField(
        queryset=ClientFolder.objects.all().order_by('-created_at'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    template = forms.ModelChoiceField(
        queryset=TaskTemplate.objects.filter(is_active=True).order_by('name'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = InternalTask

        fields = [
            'title',
            'description',
            'template',
            'assigned_to',
            'linked_request',
            'linked_client',
            'status',
            'priority',
            'due_date',
        ]

        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 5}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }


class InternalTaskChecklistItemForm(forms.ModelForm):
    class Meta:
        model = InternalTaskChecklistItem

        fields = [
            'title',
            'order',
        ]

        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Example: Confirm client details',
            }),

            'order': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
            }),
        }


class InternalTaskCommentForm(forms.ModelForm):
    class Meta:
        model = InternalTaskComment

        fields = ['comment']

        widgets = {
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Write a task update or comment...',
            }),
        }


class OperationsAnnouncementForm(forms.ModelForm):
    class Meta:
        model = OperationsAnnouncement

        fields = [
            'title',
            'message',
            'priority',
            'is_pinned',
            'is_active',
        ]

        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'is_pinned': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'checkbox-input'}),
        }
