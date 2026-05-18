from django.contrib import admin

from .models import ServiceRequest
from .models import PublicEnquiry
from .models import ServiceRequestResponse
from .models import ServiceRequestComment
from .models import ServiceRequestActivity


@admin.register(ServiceRequest)
class ServiceRequestAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'request_type',
        'priority',
        'status',
        'submitted_by',
        'assigned_to',
        'due_date',
        'created_at',
    )

    search_fields = (
        'title',
        'description',
    )

    list_filter = (
        'request_type',
        'priority',
        'status',
        'created_at',
    )


@admin.register(PublicEnquiry)
class PublicEnquiryAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'full_name',
        'company_name',
        'priority',
        'status',
        'created_at',
    )

    search_fields = (
        'title',
        'full_name',
        'email',
        'company_name',
        'description',
    )

    list_filter = (
        'priority',
        'status',
        'enquiry_type',
        'created_at',
    )


@admin.register(ServiceRequestResponse)
class ServiceRequestResponseAdmin(admin.ModelAdmin):
    list_display = (
        'service_request',
        'responded_by',
        'confirmation_status',
        'download_count',
        'responded_at',
    )


@admin.register(ServiceRequestComment)
class ServiceRequestCommentAdmin(admin.ModelAdmin):
    list_display = (
        'service_request',
        'author',
        'created_at',
    )


@admin.register(ServiceRequestActivity)
class ServiceRequestActivityAdmin(admin.ModelAdmin):
    list_display = (
        'service_request',
        'action',
        'actor',
        'created_at',
    )
