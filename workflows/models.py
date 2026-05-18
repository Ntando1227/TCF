from django.db import models
from django.utils import timezone


class Workflow(models.Model):
    TRIGGER_CHOICES = [
        ('contract_uploaded', 'Contract Uploaded'),
        ('report_uploaded', 'Report Uploaded'),
        ('invoice_generated', 'Invoice Generated'),
        ('client_folder_created', 'Client Folder Created'),
        ('manual_backup', 'Manual Backup'),
    ]

    name = models.CharField(max_length=255)

    trigger = models.CharField(
        max_length=100,
        choices=TRIGGER_CHOICES
    )

    is_active = models.BooleanField(default=True)

    description = models.TextField(blank=True)

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name


class WorkflowLog(models.Model):
    workflow = models.ForeignKey(
        Workflow,
        on_delete=models.CASCADE,
        related_name='logs'
    )

    message = models.TextField()

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'{self.workflow.name} - {self.created_at}'
