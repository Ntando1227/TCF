from django.contrib import admin

from .models import ActivityLog


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('title', 'action', 'created_at')
    search_fields = ('title', 'description')
    list_filter = ('action', 'created_at')
