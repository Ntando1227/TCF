from django.contrib import admin

from .models import ClientFolder
from .models import ClientFile
from .models import ClientFileComment


@admin.register(ClientFolder)
class ClientFolderAdmin(admin.ModelAdmin):
    list_display = (
        'client_name',
        'client_email',
        'owner',
        'created_at',
    )

    search_fields = (
        'client_name',
        'client_email',
        'owner__username',
    )

    list_filter = (
        'created_at',
        'owner',
    )


@admin.register(ClientFile)
class ClientFileAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'client_folder',
        'subfolder',
        'is_archived',
        'uploaded_at',
    )

    search_fields = (
        'title',
        'client_folder__client_name',
        'client_folder__owner__username',
    )

    list_filter = (
        'subfolder',
        'is_archived',
        'uploaded_at',
    )


@admin.register(ClientFileComment)
class ClientFileCommentAdmin(admin.ModelAdmin):
    list_display = (
        'client_file',
        'author',
        'created_at',
    )

    search_fields = (
        'client_file__title',
        'author__username',
        'comment',
    )

    list_filter = (
        'created_at',
    )
