from django.contrib import admin

from .models import InternalTask
from .models import InternalTaskChecklistItem
from .models import InternalTaskComment
from .models import OperationsAnnouncement
from .models import TaskTemplate
from .models import TaskTemplateChecklistItem


class TaskTemplateChecklistInline(admin.TabularInline):
    model = TaskTemplateChecklistItem
    extra = 1


@admin.register(TaskTemplate)
class TaskTemplateAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'default_priority',
        'default_due_days',
        'is_active',
        'created_at',
    )

    search_fields = (
        'name',
        'description',
    )

    list_filter = (
        'default_priority',
        'is_active',
        'created_at',
    )

    inlines = [
        TaskTemplateChecklistInline,
    ]


class InternalTaskChecklistInline(admin.TabularInline):
    model = InternalTaskChecklistItem
    extra = 1


@admin.register(InternalTask)
class InternalTaskAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'template',
        'assigned_to',
        'status',
        'priority',
        'due_date',
        'created_at',
    )

    search_fields = (
        'title',
        'description',
        'assigned_to__username',
        'created_by__username',
        'linked_request__title',
        'linked_client__client_name',
        'template__name',
    )

    list_filter = (
        'template',
        'status',
        'priority',
        'due_date',
        'created_at',
    )

    inlines = [
        InternalTaskChecklistInline,
    ]


@admin.register(TaskTemplateChecklistItem)
class TaskTemplateChecklistItemAdmin(admin.ModelAdmin):
    list_display = (
        'template',
        'title',
        'order',
        'created_at',
    )

    search_fields = (
        'template__name',
        'title',
    )


@admin.register(InternalTaskChecklistItem)
class InternalTaskChecklistItemAdmin(admin.ModelAdmin):
    list_display = (
        'task',
        'title',
        'is_completed',
        'completed_by',
        'completed_at',
        'order',
    )

    search_fields = (
        'task__title',
        'title',
    )

    list_filter = (
        'is_completed',
        'completed_at',
    )


@admin.register(InternalTaskComment)
class InternalTaskCommentAdmin(admin.ModelAdmin):
    list_display = (
        'task',
        'author',
        'created_at',
    )


@admin.register(OperationsAnnouncement)
class OperationsAnnouncementAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'priority',
        'is_pinned',
        'is_active',
        'created_by',
        'created_at',
    )
