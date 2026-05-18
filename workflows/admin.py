from django.contrib import admin

from .models import Workflow
from .models import WorkflowLog


@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    list_display = ('name', 'trigger', 'is_active', 'created_at')
    search_fields = ('name', 'trigger')
    list_filter = ('trigger', 'is_active')


@admin.register(WorkflowLog)
class WorkflowLogAdmin(admin.ModelAdmin):
    list_display = ('workflow', 'created_at')
    search_fields = ('workflow__name', 'message')
    list_filter = ('created_at',)
