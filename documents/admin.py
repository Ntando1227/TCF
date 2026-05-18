from django.contrib import admin

from .models import GeneratedDocument


@admin.register(GeneratedDocument)
class GeneratedDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'client_name', 'document_type', 'amount', 'created_at')
    search_fields = ('title', 'client_name', 'client_email')
    list_filter = ('document_type', 'created_at')
