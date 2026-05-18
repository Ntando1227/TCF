from django.conf import settings
from django.db import models
from django.utils import timezone


class TaskTemplate(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
        ('critical', 'Critical'),
    ]

    name = models.CharField(max_length=255)
    description = models.TextField()
    default_priority = models.CharField(max_length=50, choices=PRIORITY_CHOICES, default='medium')
    default_due_days = models.PositiveIntegerField(default=3)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name


class TaskTemplateChecklistItem(models.Model):
    template = models.ForeignKey(
        TaskTemplate,
        on_delete=models.CASCADE,
        related_name='checklist_items'
    )

    title = models.CharField(max_length=255)

    order = models.PositiveIntegerField(default=1)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return f'{self.template.name} - {self.title}'


class InternalTask(models.Model):
    STATUS_CHOICES = [
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('blocked', 'Blocked'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    PRIORITY_CHOICES = TaskTemplate.PRIORITY_CHOICES

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    template = models.ForeignKey(
        TaskTemplate,
        on_delete=models.SET_NULL,
        related_name='tasks',
        blank=True,
        null=True
    )

    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='assigned_internal_tasks',
        blank=True,
        null=True
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_internal_tasks',
        blank=True,
        null=True
    )

    linked_request = models.ForeignKey(
        'service_requests.ServiceRequest',
        on_delete=models.SET_NULL,
        related_name='internal_tasks',
        blank=True,
        null=True
    )

    linked_client = models.ForeignKey(
        'clients.ClientFolder',
        on_delete=models.SET_NULL,
        related_name='internal_tasks',
        blank=True,
        null=True
    )

    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='todo')
    priority = models.CharField(max_length=50, choices=PRIORITY_CHOICES, default='medium')

    due_date = models.DateField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def is_overdue(self):
        if self.due_date and self.status != 'completed':
            return timezone.now().date() > self.due_date
        return False

    def checklist_total(self):
        return self.checklist_items.count()

    def checklist_completed(self):
        return self.checklist_items.filter(is_completed=True).count()

    def checklist_progress_percent(self):
        total = self.checklist_total()

        if total == 0:
            return 0

        return round((self.checklist_completed() / total) * 100)

    def __str__(self):
        return self.title


class InternalTaskChecklistItem(models.Model):
    task = models.ForeignKey(
        InternalTask,
        on_delete=models.CASCADE,
        related_name='checklist_items'
    )

    title = models.CharField(max_length=255)

    is_completed = models.BooleanField(default=False)

    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='completed_task_checklist_items',
        blank=True,
        null=True
    )

    completed_at = models.DateTimeField(blank=True, null=True)

    order = models.PositiveIntegerField(default=1)

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return f'{self.task.title} - {self.title}'


class InternalTaskComment(models.Model):
    task = models.ForeignKey(
        InternalTask,
        on_delete=models.CASCADE,
        related_name='comments'
    )

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='internal_task_comments'
    )

    comment = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'{self.author.username} - {self.task.title}'


class OperationsAnnouncement(models.Model):
    PRIORITY_CHOICES = [
        ('normal', 'Normal'),
        ('important', 'Important'),
        ('urgent', 'Urgent'),
        ('critical', 'Critical'),
    ]

    title = models.CharField(max_length=255)
    message = models.TextField()

    priority = models.CharField(
        max_length=50,
        choices=PRIORITY_CHOICES,
        default='normal'
    )

    is_pinned = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='created_announcements',
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    
class TaskResolution(models.Model):
    task = models.ForeignKey(
        'InternalTask',
        on_delete=models.CASCADE,
        related_name='resolutions'
    )

    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    resolution_notes = models.TextField(blank=True)

    resolution_file = models.FileField(
        upload_to='task_resolutions/',
        blank=True,
        null=True
    )

    resolution_link = models.URLField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Resolution for {self.task.title}"
