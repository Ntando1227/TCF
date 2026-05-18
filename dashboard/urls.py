from django.urls import path
from . import views

urlpatterns = [
    path('activity-feed/', views.activity_feed, name='activity_feed'),
    path('activity-feed/', views.activity_feed, name='activity_feed'),
    path('', views.home, name='home'),
]
