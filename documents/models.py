from django.db import models
from django.utils import timezone


class GeneratedDocument(models.Model):
    DOCUMENT_TYPES = [
        ('invoice', 'Invoice'),
        ('quotation', 'Quotation'),
        ('contract', 'Contract'),
        ('proposal', 'Proposal'),
        ('certificate', 'Certificate'),
        ('report', 'Report'),
    ]

    client_name = models.CharField(max_length=200)
    client_email = models.EmailField(blank=True, null=True)
    document_type = models.CharField(max_length=50, choices=DOCUMENT_TYPES)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    file_path = models.CharField(max_length=500, blank=True)
    file_name = models.CharField(max_length=255, blank=True)

    client_folder_path = models.CharField(max_length=500, blank=True)

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'{self.title} - {self.client_name}'
