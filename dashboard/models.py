from django.db import models
from django.utils import timezone


class ActivityLog(models.Model):
    ACTION_CHOICES = [
        ('folder_created', 'Folder Created'),
        ('folder_deleted', 'Folder Deleted'),
        ('file_uploaded', 'File Uploaded'),
        ('file_moved', 'File Moved'),
        ('file_archived', 'File Archived'),
        ('file_restored', 'File Restored'),
        ('file_deleted', 'File Deleted'),
        ('document_generated', 'Document Generated'),
        ('document_deleted', 'Document Deleted'),
        ('workflow_ran', 'Workflow Ran'),
        ('export_created', 'Export Created'),
    ]

    action = models.CharField(max_length=100, choices=ACTION_CHOICES)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title
