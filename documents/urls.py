from django.urls import path

from . import views


urlpatterns = [
    path('', views.document_list, name='document_list'),
    path('generate/', views.generate_document, name='generate_document'),
    path('download/<int:document_id>/', views.download_document, name='download_document'),
    path('delete/<int:document_id>/confirm/', views.confirm_delete_document, name='confirm_delete_document'),
    path('delete/<int:document_id>/', views.delete_document, name='delete_document'),
]
