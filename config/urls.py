from django.contrib import admin
from django.urls import path, include

from dashboard import views as dashboard_views
from clients import views as client_views


urlpatterns = [
    path('', dashboard_views.landing_page, name='landing_page'),
    path('client/', dashboard_views.client_landing_page, name='client_landing_page'),

    path('dashboard/', dashboard_views.home, name='home'),
    path('dashboard/activity-feed/', dashboard_views.activity_feed, name='activity_feed'),
    path('dashboard/health/', dashboard_views.operational_health_dashboard, name='operational_health_dashboard'),
    path('dashboard/assistant/', dashboard_views.ai_operations_assistant, name='ai_operations_assistant'),
    path('dashboard/search/', dashboard_views.global_search, name='global_search'),
    path('dashboard/command-centre/', dashboard_views.command_centre, name='command_centre'),

    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),

    path('clients/', client_views.client_portal, name='client_portal'),
    path('clients/portal/', client_views.client_portal, name='client_portal_alt'),
    path('clients/folders/', client_views.client_folder_list, name='client_folder_list'),
    path('clients/profile/<int:folder_id>/', client_views.client_profile, name='client_profile'),

    path('documents/', include('documents.urls')),
    path('workflows/', include('workflows.urls')),
    path('analytics/', include('analytics.urls')),
    path('exports/', include('exports.urls')),
    path('requests/', include('service_requests.urls')),
    path('operations/', include('operations.urls')),
    path('notifications/', include('notifications.urls')),
]
