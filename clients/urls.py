from django.urls import path
from . import views

urlpatterns = [
    path('', views.client_portal, name='client_portal'),
    path('folders/', views.client_folder_list, name='client_folder_list'),
    path('profile/<int:folder_id>/', views.client_profile, name='client_profile'),
]
