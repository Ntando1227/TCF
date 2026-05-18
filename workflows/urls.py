from django.urls import path

from . import views


urlpatterns = [
    path(
        '',
        views.workflow_list,
        name='workflow_list'
    ),

    path(
        'logs/',
        views.workflow_logs,
        name='workflow_logs'
    ),

    path(
        'run-backup/',
        views.run_backup_now,
        name='run_backup_now'
    ),
]
