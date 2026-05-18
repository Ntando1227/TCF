from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = (
        'username',
        'email',
        'role',
        'company_name',
        'is_staff',
        'is_superuser',
    )

    list_filter = (
        'role',
        'is_staff',
        'is_superuser',
        'is_active',
    )

    search_fields = (
        'username',
        'email',
        'company_name',
    )

    fieldsets = UserAdmin.fieldsets + (
        (
            'That Corporate Flow Profile',
            {
                'fields': (
                    'role',
                    'company_name',
                    'phone_number',
                    'must_change_password',
                )
            }
        ),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            'That Corporate Flow Profile',
            {
                'fields': (
                    'role',
                    'company_name',
                    'phone_number',
                    'must_change_password',
                )
            }
        ),
    )
