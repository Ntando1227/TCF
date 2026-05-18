from django.conf import settings
from django.db import models
from django.utils import timezone


class ClientFolder(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='client_folders',
        blank=True,
        null=True
    )

    client_name = models.CharField(max_length=200)
    client_email = models.EmailField(blank=True, null=True)
    folder_path = models.CharField(max_length=500, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.client_name


class ClientFile(models.Model):

    SUBFOLDER_CHOICES = [
        ('contracts', 'Contracts'),
        ('invoices', 'Invoices'),
        ('quotations', 'Quotations'),
        ('proposals', 'Proposals'),
        ('reports', 'Reports'),
        ('certificates', 'Certificates'),
        ('general', 'General'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('changes_requested', 'Needs Changes'),
    ]

    client_folder = models.ForeignKey(
        ClientFolder,
        on_delete=models.CASCADE,
        related_name='files'
    )

    title = models.CharField(max_length=255)

    subfolder = models.CharField(
        max_length=50,
        choices=SUBFOLDER_CHOICES,
        default='general'
    )

    uploaded_file = models.FileField(
        upload_to='client_uploads/'
    )

    status = models.CharField(
        max_length=40,
        choices=STATUS_CHOICES,
        default='pending'
    )

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='approved_files'
    )

    approved_at = models.DateTimeField(
        blank=True,
        null=True
    )

    is_archived = models.BooleanField(default=False)

    archived_at = models.DateTimeField(
        blank=True,
        null=True
    )

    uploaded_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title


class ClientFileComment(models.Model):
    client_file = models.ForeignKey(
        ClientFile,
        on_delete=models.CASCADE,
        related_name='comments'
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='file_comments'
    )

    comment = models.TextField()

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'{self.author.username} - {self.client_file.title}'
