from django.urls import path

from . import views


urlpatterns = [
    path('resolve-task/<int:task_id>/', views.resolve_task, name='resolve_task'),
    path('', views.task_dashboard, name='task_dashboard'),
    path('board/', views.task_board, name='task_board'),
    path('my-work/', views.my_work_dashboard, name='my_work_dashboard'),

    path('templates/', views.task_template_list, name='task_template_list'),
    path('templates/create/', views.create_task_template, name='create_task_template'),
    path('templates/<int:template_id>/', views.task_template_detail, name='task_template_detail'),
    path('templates/<int:template_id>/edit/', views.edit_task_template, name='edit_task_template'),
    path('templates/<int:template_id>/create-task/', views.create_task_from_template, name='create_task_from_template'),
    path('templates/<int:template_id>/checklist/add/', views.add_template_checklist_item, name='add_template_checklist_item'),
    path('templates/checklist/<int:item_id>/delete/', views.delete_template_checklist_item, name='delete_template_checklist_item'),

    path('announcements/', views.announcement_list, name='announcement_list'),
    path('announcements/create/', views.create_announcement, name='create_announcement'),
    path('announcements/<int:announcement_id>/', views.announcement_detail, name='announcement_detail'),
    path('announcements/<int:announcement_id>/edit/', views.edit_announcement, name='edit_announcement'),
    path('announcements/<int:announcement_id>/toggle-active/', views.toggle_announcement_active, name='toggle_announcement_active'),

    path('create/', views.create_task, name='create_task'),
    path('create-from-request/<int:request_id>/', views.create_task_from_request, name='create_task_from_request'),

    path('<int:task_id>/', views.task_detail, name='task_detail'),
    path('<int:task_id>/edit/', views.edit_task, name='edit_task'),
    path('<int:task_id>/complete/', views.complete_task, name='complete_task'),
    path('<int:task_id>/reopen/', views.reopen_task, name='reopen_task'),

    path('<int:task_id>/move/<str:new_status>/', views.move_task_status, name='move_task_status'),
    path('<int:task_id>/move/<str:new_status>/', views.move_task_status, name='move_task_status'),
    path('<int:task_id>/checklist/add/', views.add_task_checklist_item, name='add_task_checklist_item'),
    path('checklist/<int:item_id>/toggle/', views.toggle_task_checklist_item, name='toggle_task_checklist_item'),
    path('checklist/<int:item_id>/delete/', views.delete_task_checklist_item, name='delete_task_checklist_item'),
]

