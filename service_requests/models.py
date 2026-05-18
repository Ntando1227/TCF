from django.conf import settings
from django.db import models
from django.utils import timezone


class ServiceRequest(models.Model):
    REQUEST_TYPES = [
        ('contract', 'New Contract Request'),
        ('invoice', 'Invoice Request'),
        ('quotation', 'Quotation Request'),
        ('report', 'Report Submission'),
        ('support', 'Support Request'),
        ('review', 'Document Review'),
        ('general', 'General Admin Request'),
    ]

    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]

    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='submitted_requests'
    )

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='assigned_requests',
        blank=True,
        null=True
    )

    linked_folder = models.ForeignKey(
        'clients.ClientFolder',
        on_delete=models.SET_NULL,
        related_name='service_requests',
        blank=True,
        null=True
    )

    linked_file = models.ForeignKey(
        'clients.ClientFile',
        on_delete=models.SET_NULL,
        related_name='service_requests',
        blank=True,
        null=True
    )

    linked_document = models.ForeignKey(
        'documents.GeneratedDocument',
        on_delete=models.SET_NULL,
        related_name='service_requests',
        blank=True,
        null=True
    )

    title = models.CharField(max_length=255)

    request_type = models.CharField(
        max_length=50,
        choices=REQUEST_TYPES,
        default='general'
    )

    description = models.TextField()

    supporting_file = models.FileField(
        upload_to='request_uploads/',
        blank=True,
        null=True
    )

    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='submitted'
    )

    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_LEVELS,
        default='medium'
    )

    due_date = models.DateField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    reviewed_at = models.DateTimeField(blank=True, null=True)

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='reviewed_requests',
        blank=True,
        null=True
    )

    def is_overdue(self):
        if self.due_date and self.status != 'completed':
            return timezone.now().date() > self.due_date
        return False

    def latest_response(self):
        return self.responses.order_by('-responded_at').first()

    def has_response(self):
        return self.responses.exists()

    def __str__(self):
        return self.title


class PublicEnquiry(models.Model):
    STATUS_CHOICES = [
        ('new', 'New'),
        ('reviewed', 'Reviewed'),
        ('converted', 'Converted To Request'),
        ('closed', 'Closed'),
    ]

    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    enquiry_type_choices = ServiceRequest.REQUEST_TYPES

    full_name = models.CharField(max_length=255)

    email = models.EmailField()

    phone_number = models.CharField(
        max_length=100,
        blank=True
    )

    company_name = models.CharField(
        max_length=255,
        blank=True
    )

    enquiry_type = models.CharField(
        max_length=50,
        choices=enquiry_type_choices,
        default='general'
    )

    title = models.CharField(max_length=255)

    description = models.TextField()

    attachment = models.FileField(
        upload_to='public_enquiries/',
        blank=True,
        null=True
    )

    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_LEVELS,
        default='medium'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new'
    )

    converted_request = models.ForeignKey(
        ServiceRequest,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='source_enquiries'
    )

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='reviewed_enquiries'
    )

    reviewed_at = models.DateTimeField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title


class ServiceRequestResponse(models.Model):
    CONFIRMATION_CHOICES = [
        ('pending', 'Pending Confirmation'),
        ('accepted', 'Accepted'),
        ('changes_requested', 'Changes Requested'),
    ]

    service_request = models.ForeignKey(
        ServiceRequest,
        on_delete=models.CASCADE,
        related_name='responses'
    )

    response_message = models.TextField(blank=True)

    response_attachment = models.FileField(
        upload_to='request_responses/',
        blank=True,
        null=True
    )

    response_link = models.URLField(
        max_length=700,
        blank=True
    )

    responded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='request_responses',
        blank=True,
        null=True
    )

    responded_at = models.DateTimeField(default=timezone.now)

    download_count = models.PositiveIntegerField(default=0)

    last_downloaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='downloaded_request_responses',
        blank=True,
        null=True
    )

    last_downloaded_at = models.DateTimeField(
        blank=True,
        null=True
    )

    confirmation_status = models.CharField(
        max_length=50,
        choices=CONFIRMATION_CHOICES,
        default='pending'
    )

    confirmation_note = models.TextField(blank=True)

    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='confirmed_request_responses',
        blank=True,
        null=True
    )

    confirmed_at = models.DateTimeField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(default=timezone.now)

    def has_deliverable(self):
        return bool(
            self.response_message or
            self.response_attachment or
            self.response_link
        )

    def __str__(self):
        return f'Response for {self.service_request.title}'


class ServiceRequestComment(models.Model):
    service_request = models.ForeignKey(
        ServiceRequest,
        on_delete=models.CASCADE,
        related_name='comments'
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='request_comments'
    )

    comment = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'{self.author.username} - {self.service_request.title}'


class ServiceRequestActivity(models.Model):
    ACTION_CHOICES = [
        ('request_submitted', 'Request Submitted'),
        ('status_changed', 'Status Changed'),
        ('folder_linked', 'Folder Linked'),
        ('file_linked', 'File Linked'),
        ('document_linked', 'Document Linked'),
        ('comment_added', 'Comment Added'),
        ('assigned_to_staff', 'Assigned To Staff'),
        ('request_approved', 'Request Approved'),
        ('request_rejected', 'Request Rejected'),
        ('request_completed', 'Request Completed'),
        ('request_fulfilled', 'Request Fulfilled'),
        ('response_uploaded', 'Response Uploaded'),
        ('response_link_added', 'Response Link Added'),
        ('response_downloaded', 'Response Downloaded'),
        ('response_accepted', 'Response Accepted'),
        ('response_changes_requested', 'Response Changes Requested'),
        ('request_updated', 'Request Updated'),
    ]

    service_request = models.ForeignKey(
        ServiceRequest,
        on_delete=models.CASCADE,
        related_name='activities'
    )

    action = models.CharField(
        max_length=100,
        choices=ACTION_CHOICES
    )

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='request_activities'
    )

    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title
