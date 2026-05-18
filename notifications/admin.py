from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'user',
        'priority',
        'is_read',
        'created_at',
    )

    search_fields = (
        'title',
        'message',
        'user__username',
        'user__email',
    )

    list_filter = (
        'priority',
        'is_read',
        'created_at',
    )
