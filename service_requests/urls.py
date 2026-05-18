from django.urls import path

from . import views


urlpatterns = [
    path('', views.request_list, name='request_list'),

    path('public-enquiry/', views.public_enquiry_form, name='public_enquiry_form'),

    path('public-enquiry-success/', views.public_enquiry_success, name='public_enquiry_success'),

    path('public-enquiries/', views.public_enquiry_list, name='public_enquiry_list'),

    path('public-enquiries/<int:enquiry_id>/', views.public_enquiry_detail, name='public_enquiry_detail'),

    path('public-enquiries/<int:enquiry_id>/reviewed/', views.mark_public_enquiry_reviewed, name='mark_public_enquiry_reviewed'),

    path('public-enquiries/<int:enquiry_id>/closed/', views.mark_public_enquiry_closed, name='mark_public_enquiry_closed'),

    path('public-enquiries/<int:enquiry_id>/convert/', views.convert_public_enquiry_to_request, name='convert_public_enquiry_to_request'),

    path('public-enquiries/', views.public_enquiry_list, name='public_enquiry_list'),

    path('public-enquiries/<int:enquiry_id>/', views.public_enquiry_detail, name='public_enquiry_detail'),

    path('public-enquiries/<int:enquiry_id>/reviewed/', views.mark_public_enquiry_reviewed, name='mark_public_enquiry_reviewed'),

    path('public-enquiries/<int:enquiry_id>/closed/', views.mark_public_enquiry_closed, name='mark_public_enquiry_closed'),

    path('public-enquiries/<int:enquiry_id>/convert/', views.convert_public_enquiry_to_request, name='convert_public_enquiry_to_request'),

    path('public-enquiries/', views.public_enquiry_list, name='public_enquiry_list'),

    path('public-enquiries/<int:enquiry_id>/', views.public_enquiry_detail, name='public_enquiry_detail'),

    path('public-enquiries/<int:enquiry_id>/reviewed/', views.mark_public_enquiry_reviewed, name='mark_public_enquiry_reviewed'),

    path('public-enquiries/<int:enquiry_id>/closed/', views.mark_public_enquiry_closed, name='mark_public_enquiry_closed'),

    path('public-enquiries/<int:enquiry_id>/convert/', views.convert_public_enquiry_to_request, name='convert_public_enquiry_to_request'),

    path('create/', views.create_request, name='create_request'),

    path('<int:request_id>/', views.request_detail, name='request_detail'),

    path('<int:request_id>/update/', views.update_request_status, name='update_request_status'),

    path('<int:request_id>/respond/', views.create_request_response, name='create_request_response'),

    path('<int:request_id>/download/', views.download_request_file, name='download_request_file'),

    path('response/<int:response_id>/confirm/', views.confirm_response_delivery, name='confirm_response_delivery'),

    path('response/<int:response_id>/preview/', views.preview_response_attachment, name='preview_response_attachment'),

    path('response/<int:response_id>/stream/', views.stream_response_attachment, name='stream_response_attachment'),

    path('response/<int:response_id>/download/', views.download_response_attachment, name='download_response_attachment'),
]
