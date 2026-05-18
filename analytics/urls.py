from django.urls import path

from . import views


urlpatterns = [
    path('', views.exports_home, name='exports_home'),

    path('request-analytics/', views.request_analytics_dashboard, name='request_analytics_dashboard'),
    path('ai-summary/', views.ai_summary_centre, name='ai_summary_centre'),
    path('ai-summary/generate/', views.generate_ai_summary, name='generate_ai_summary'),

    path('client-folders/', views.export_client_folders, name='export_client_folders'),
    path('client-files/', views.export_client_files, name='export_client_files'),
    path('documents/', views.export_documents, name='export_documents'),
    path('workflows/', views.export_workflow_logs, name='export_workflow_logs'),
]
