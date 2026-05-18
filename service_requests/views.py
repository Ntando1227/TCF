from pathlib import Path

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse
from django.http import Http404
from django.shortcuts import render
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from django.utils import timezone

from accounts.permissions import can_manage_all_folders

from dashboard.activity import log_activity

from notifications.services import create_notification
from notifications.services import notify_admins

from .models import PublicEnquiry, ServiceRequest
from .models import PublicEnquiry, ServiceRequestResponse
from .models import PublicEnquiry, ServiceRequestActivity
from .forms import ServiceRequestForm
from .forms import PublicEnquiryForm
from .forms import StaffServiceRequestForm
from .forms import ServiceRequestResponseForm
from .forms import ServiceRequestConfirmationForm
from .forms import ServiceRequestCommentForm


def can_manage_requests(user):
    return can_manage_all_folders(user)


def get_visible_requests(user):
    if can_manage_requests(user):
        return ServiceRequest.objects.all()

    return ServiceRequest.objects.filter(submitted_by=user)


def get_accessible_request_or_404(user, request_id):
    if can_manage_requests(user):
        return get_object_or_404(ServiceRequest, id=request_id)

    return get_object_or_404(
        ServiceRequest,
        id=request_id,
        submitted_by=user
    )


def get_accessible_response_or_404(user, response_id):
    if can_manage_requests(user):
        return get_object_or_404(ServiceRequestResponse, id=response_id)

    return get_object_or_404(
        ServiceRequestResponse,
        id=response_id,
        service_request__submitted_by=user
    )


def get_preview_type(file_path):
    extension = Path(file_path).suffix.lower()

    if extension == '.pdf':
        return 'pdf'

    if extension in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
        return 'image'

    if extension in ['.txt', '.csv', '.log', '.md']:
        return 'text'

    return 'unsupported'


def create_request_activity(service_request, action, title, description, actor):
    ServiceRequestActivity.objects.create(
        service_request=service_request,
        action=action,
        title=title,
        description=description,
        actor=actor
    )


def get_status_activity_action(status):
    if status == 'approved':
        return 'request_approved'

    if status == 'rejected':
        return 'request_rejected'

    if status == 'completed':
        return 'request_completed'

    return 'status_changed'


@login_required
def request_list(request):
    search_query = request.GET.get('q', '').strip()
    status_filter = request.GET.get('status', 'all').strip()
    type_filter = request.GET.get('type', 'all').strip()

    service_requests = get_visible_requests(request.user).select_related(
        'submitted_by',
        'assigned_to',
        'reviewed_by',
        'linked_folder',
        'linked_file',
        'linked_document',
    ).prefetch_related(
        'responses'
    ).order_by('-created_at')

    if search_query:
        service_requests = service_requests.filter(title__icontains=search_query)

    if status_filter != 'all':
        service_requests = service_requests.filter(status=status_filter)

    if type_filter != 'all':
        service_requests = service_requests.filter(request_type=type_filter)

    stats_source = get_visible_requests(request.user)

    stats = {
        'submitted': stats_source.filter(status='submitted').count(),
        'under_review': stats_source.filter(status='under_review').count(),
        'approved': stats_source.filter(status='approved').count(),
        'rejected': stats_source.filter(status='rejected').count(),
        'completed': stats_source.filter(status='completed').count(),
        'responses': ServiceRequestResponse.objects.filter(
            service_request__in=stats_source
        ).count(),
        'downloads': sum(
            ServiceRequestResponse.objects.filter(
                service_request__in=stats_source
            ).values_list('download_count', flat=True)
        ),
    }

    return render(request, 'service_requests/request_list.html', {
        'service_requests': service_requests,
        'search_query': search_query,
        'status_filter': status_filter,
        'type_filter': type_filter,
        'status_choices': ServiceRequest.STATUS_CHOICES,
        'request_types': ServiceRequest.REQUEST_TYPES,
        'stats': stats,
        'can_manage_requests': can_manage_requests(request.user),
    })


@login_required
def create_request(request):
    if request.method == 'POST':
        form = ServiceRequestForm(request.POST, request.FILES)

        if form.is_valid():
            service_request = form.save(commit=False)
            service_request.submitted_by = request.user
            service_request.save()

            create_request_activity(
                service_request,
                'request_submitted',
                'Request submitted',
                f'{request.user.username} submitted this request.',
                request.user
            )

            log_activity(
                'workflow_ran',
                f'Request submitted: {service_request.title}',
                f'{request.user.username} submitted a {service_request.get_request_type_display()}.'
            )

            notify_admins(
                title='New service request submitted',
                message=f'{request.user.username} submitted: {service_request.title}',
                notification_type='info',
                link=f'/requests/{service_request.id}/'
            )

            messages.success(request, 'Request submitted successfully.')

            return redirect('request_detail', request_id=service_request.id)

    else:
        form = ServiceRequestForm()

    return render(request, 'service_requests/request_form.html', {
        'form': form,
    })


@login_required
def request_detail(request, request_id):
    service_request = get_accessible_request_or_404(request.user, request_id)

    if request.method == 'POST':
        comment_form = ServiceRequestCommentForm(request.POST)

        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.service_request = service_request
            comment.author = request.user
            comment.save()

            create_request_activity(
                service_request,
                'comment_added',
                'Comment added',
                f'{request.user.username} added a comment.',
                request.user
            )

            log_activity(
                'workflow_ran',
                f'Request comment added: {service_request.title}',
                f'{request.user.username} commented on request.'
            )

            if service_request.submitted_by != request.user:
                create_notification(
                    recipient=service_request.submitted_by,
                    title='New comment on your request',
                    message=f'{request.user.username} commented on {service_request.title}.',
                    notification_type='info',
                    link=f'/requests/{service_request.id}/'
                )

            if service_request.assigned_to and service_request.assigned_to != request.user:
                create_notification(
                    recipient=service_request.assigned_to,
                    title='New comment on assigned request',
                    message=f'{request.user.username} commented on {service_request.title}.',
                    notification_type='info',
                    link=f'/requests/{service_request.id}/'
                )

            messages.success(request, 'Comment posted successfully.')

            return redirect('request_detail', request_id=service_request.id)

    else:
        comment_form = ServiceRequestCommentForm()

    staff_form = None
    response_form = None

    if can_manage_requests(request.user):
        staff_form = StaffServiceRequestForm(instance=service_request)
        response_form = ServiceRequestResponseForm()

    comments = service_request.comments.select_related('author').all().order_by('-created_at')
    activities = service_request.activities.select_related('actor').all().order_by('-created_at')
    responses = service_request.responses.select_related(
        'responded_by',
        'last_downloaded_by',
        'confirmed_by',
    ).all().order_by('-responded_at')

    latest_response = responses.first()

    confirmation_forms = {}

    for response in responses:
        confirmation_forms[response.id] = ServiceRequestConfirmationForm(instance=response)

    completion_metrics = {
        'responses': responses.count(),
        'total_downloads': sum(responses.values_list('download_count', flat=True)),
        'has_attachment': responses.filter(response_attachment__isnull=False).exclude(response_attachment='').exists(),
        'has_link': responses.exclude(response_link='').exists(),
        'accepted': responses.filter(confirmation_status='accepted').count(),
        'changes_requested': responses.filter(confirmation_status='changes_requested').count(),
        'pending_confirmation': responses.filter(confirmation_status='pending').count(),
        'latest_response': latest_response,
    }

    return render(request, 'service_requests/request_detail.html', {
        'service_request': service_request,
        'comments': comments,
        'activities': activities,
        'responses': responses,
        'latest_response': latest_response,
        'completion_metrics': completion_metrics,
        'comment_form': comment_form,
        'staff_form': staff_form,
        'response_form': response_form,
        'confirmation_forms': confirmation_forms,
        'can_manage_requests': can_manage_requests(request.user),
    })


@login_required
def update_request_status(request, request_id):
    if not can_manage_requests(request.user):
        raise Http404('You do not have permission to update requests.')

    service_request = get_object_or_404(ServiceRequest, id=request_id)

    if request.method == 'POST':
        old_status = service_request.status
        old_assigned_to = service_request.assigned_to
        old_folder = service_request.linked_folder
        old_file = service_request.linked_file
        old_document = service_request.linked_document

        form = StaffServiceRequestForm(request.POST, instance=service_request)

        if form.is_valid():
            updated_request = form.save(commit=False)
            updated_request.reviewed_by = request.user
            updated_request.reviewed_at = timezone.now()
            updated_request.save()

            changes = []

            if old_status != updated_request.status:
                status_text = updated_request.get_status_display()

                create_request_activity(
                    updated_request,
                    get_status_activity_action(updated_request.status),
                    f'Status changed to {status_text}',
                    f'{request.user.username} changed the request status to {status_text}.',
                    request.user
                )

                changes.append(f'Status changed to {status_text}')

            if old_assigned_to != updated_request.assigned_to and updated_request.assigned_to:
                create_request_activity(
                    updated_request,
                    'assigned_to_staff',
                    'Assigned to staff',
                    f'{updated_request.assigned_to.username} was assigned to this request.',
                    request.user
                )

                changes.append(f'Assigned to {updated_request.assigned_to.username}')

            if old_folder != updated_request.linked_folder and updated_request.linked_folder:
                create_request_activity(
                    updated_request,
                    'folder_linked',
                    'Folder linked',
                    f'{updated_request.linked_folder.client_name} was linked to this request.',
                    request.user
                )

                changes.append(f'Linked folder: {updated_request.linked_folder.client_name}')

            if old_file != updated_request.linked_file and updated_request.linked_file:
                create_request_activity(
                    updated_request,
                    'file_linked',
                    'File linked',
                    f'{updated_request.linked_file.title} was linked to this request.',
                    request.user
                )

                changes.append(f'Linked file: {updated_request.linked_file.title}')

            if old_document != updated_request.linked_document and updated_request.linked_document:
                create_request_activity(
                    updated_request,
                    'document_linked',
                    'Document linked',
                    f'{updated_request.linked_document.title} was linked to this request.',
                    request.user
                )

                changes.append(f'Linked document: {updated_request.linked_document.title}')

            if not changes:
                create_request_activity(
                    updated_request,
                    'request_updated',
                    'Request updated',
                    f'{request.user.username} updated the request.',
                    request.user
                )

            change_text = '; '.join(changes) if changes else 'Request updated'

            log_activity(
                'workflow_ran',
                f'Request updated: {updated_request.title}',
                f'{change_text} by {request.user.username}.'
            )

            create_notification(
                recipient=updated_request.submitted_by,
                title='Request updated',
                message=f'{updated_request.title}: {change_text}.',
                notification_type='info',
                link=f'/requests/{updated_request.id}/'
            )

            if updated_request.assigned_to and updated_request.assigned_to != request.user:
                create_notification(
                    recipient=updated_request.assigned_to,
                    title='Request assigned or updated',
                    message=f'{updated_request.title}: {change_text}.',
                    notification_type='info',
                    link=f'/requests/{updated_request.id}/'
                )

            messages.success(request, 'Request updated successfully.')

    return redirect('request_detail', request_id=service_request.id)


@login_required
def create_request_response(request, request_id):
    if not can_manage_requests(request.user):
        raise Http404('You do not have permission to respond to requests.')

    service_request = get_object_or_404(ServiceRequest, id=request_id)

    if request.method == 'POST':
        form = ServiceRequestResponseForm(request.POST, request.FILES)

        if form.is_valid():
            response = form.save(commit=False)
            response.service_request = service_request
            response.responded_by = request.user
            response.responded_at = timezone.now()
            response.save()

            if form.cleaned_data.get('mark_completed'):
                service_request.status = 'completed'
                service_request.reviewed_by = request.user
                service_request.reviewed_at = timezone.now()
                service_request.save()

            if response.response_attachment:
                create_request_activity(
                    service_request,
                    'response_uploaded',
                    'Response attachment uploaded',
                    f'{request.user.username} uploaded a response attachment.',
                    request.user
                )

            if response.response_link:
                create_request_activity(
                    service_request,
                    'response_link_added',
                    'Response link added',
                    f'{request.user.username} added an external response link.',
                    request.user
                )

            create_request_activity(
                service_request,
                'request_fulfilled',
                'Request response added',
                f'{request.user.username} responded to this request.',
                request.user
            )

            if service_request.status == 'completed':
                create_request_activity(
                    service_request,
                    'request_completed',
                    'Request completed',
                    f'{request.user.username} marked this request as completed.',
                    request.user
                )

            log_activity(
                'workflow_ran',
                f'Request response added: {service_request.title}',
                f'{request.user.username} added a request response.'
            )

            create_notification(
                recipient=service_request.submitted_by,
                title='Request response available',
                message=f'{service_request.title} has a new response.',
                notification_type='success',
                link=f'/requests/{service_request.id}/'
            )

            messages.success(request, 'Request response added successfully.')

    return redirect('request_detail', request_id=service_request.id)


@login_required
def confirm_response_delivery(request, response_id):
    response = get_accessible_response_or_404(request.user, response_id)

    if request.method == 'POST':
        form = ServiceRequestConfirmationForm(request.POST, instance=response)

        if form.is_valid():
            updated_response = form.save(commit=False)
            updated_response.confirmed_by = request.user
            updated_response.confirmed_at = timezone.now()
            updated_response.save()

            service_request = updated_response.service_request

            if updated_response.confirmation_status == 'accepted':
                create_request_activity(
                    service_request,
                    'response_accepted',
                    'Response accepted',
                    f'{request.user.username} accepted the response.',
                    request.user
                )

                notify_admins(
                    title='Response accepted',
                    message=f'{request.user.username} accepted the response for {service_request.title}.',
                    notification_type='success',
                    link=f'/requests/{service_request.id}/'
                )

                messages.success(request, 'Response accepted successfully.')

            elif updated_response.confirmation_status == 'changes_requested':
                service_request.status = 'under_review'
                service_request.save()

                create_request_activity(
                    service_request,
                    'response_changes_requested',
                    'Changes requested',
                    f'{request.user.username} requested changes on the response.',
                    request.user
                )

                notify_admins(
                    title='Client requested changes',
                    message=f'{request.user.username} requested changes for {service_request.title}.',
                    notification_type='warning',
                    link=f'/requests/{service_request.id}/'
                )

                messages.success(request, 'Changes requested successfully.')

            else:
                messages.success(request, 'Confirmation updated successfully.')

    return redirect('request_detail', request_id=response.service_request.id)


@login_required
def preview_response_attachment(request, response_id):
    response = get_accessible_response_or_404(request.user, response_id)

    if not response.response_attachment:
        raise Http404('No response attachment available.')

    file_path = Path(response.response_attachment.path)

    if not file_path.exists():
        raise Http404('Response attachment not found.')

    preview_type = get_preview_type(file_path)

    text_content = ''

    if preview_type == 'text':
        try:
            text_content = file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            text_content = file_path.read_text(encoding='latin-1')

    return render(request, 'service_requests/response_preview.html', {
        'response': response,
        'service_request': response.service_request,
        'preview_type': preview_type,
        'text_content': text_content,
    })


@login_required
def stream_response_attachment(request, response_id):
    response = get_accessible_response_or_404(request.user, response_id)

    if not response.response_attachment:
        raise Http404('No response attachment available.')

    file_path = Path(response.response_attachment.path)

    if not file_path.exists():
        raise Http404('Response attachment not found.')

    return FileResponse(
        open(file_path, 'rb'),
        as_attachment=False
    )


@login_required
def download_request_file(request, request_id):
    service_request = get_accessible_request_or_404(request.user, request_id)

    if not service_request.supporting_file:
        raise Http404('No supporting file attached.')

    file_path = Path(service_request.supporting_file.path)

    if not file_path.exists():
        raise Http404('File not found.')

    return FileResponse(
        open(file_path, 'rb'),
        as_attachment=True
    )


@login_required
def download_response_attachment(request, response_id):
    response = get_accessible_response_or_404(request.user, response_id)

    if not response.response_attachment:
        raise Http404('No response attachment available.')

    file_path = Path(response.response_attachment.path)

    if not file_path.exists():
        raise Http404('Response attachment not found.')

    response.download_count = response.download_count + 1
    response.last_downloaded_by = request.user
    response.last_downloaded_at = timezone.now()
    response.save()

    create_request_activity(
        response.service_request,
        'response_downloaded',
        'Response downloaded',
        f'{request.user.username} downloaded a response attachment.',
        request.user
    )

    return FileResponse(
        open(file_path, 'rb'),
        as_attachment=True
    )

@login_required
def public_enquiry_success(request):
    return render(request, 'service_requests/public_enquiry_success.html')


def public_enquiry_form(request):
    if request.method == 'POST':
        form = PublicEnquiryForm(request.POST, request.FILES)

        if form.is_valid():
            enquiry = form.save()

            log_activity(
                'workflow_ran',
                f'Public enquiry submitted: {enquiry.title}',
                f'{enquiry.full_name} submitted a public enquiry.'
            )

            notify_admins(
                title='New Public Enquiry',
                message=f'{enquiry.full_name} submitted: {enquiry.title}',
                notification_type='info',
                link='/admin/service_requests/publicenquiry/'
            )

            return redirect('public_enquiry_success')

    else:
        form = PublicEnquiryForm()

    return render(request, 'service_requests/public_enquiry_form.html', {
        'form': form,
    })

@login_required
def public_enquiry_success(request):
    return render(request, 'service_requests/public_enquiry_success.html')


def public_enquiry_form(request):
    if request.method == 'POST':
        form = PublicEnquiryForm(request.POST, request.FILES)

        if form.is_valid():
            enquiry = form.save()

            log_activity(
                'workflow_ran',
                f'Public enquiry submitted: {enquiry.title}',
                f'{enquiry.full_name} submitted a public enquiry.'
            )

            notify_admins(
                title='New Public Enquiry',
                message=f'{enquiry.full_name} submitted: {enquiry.title}',
                notification_type='info',
                link='/admin/service_requests/publicenquiry/'
            )

            return redirect('public_enquiry_success')

    else:
        form = PublicEnquiryForm()

    return render(request, 'service_requests/public_enquiry_form.html', {
        'form': form,
    })

@login_required
def public_enquiry_list(request):
    if not can_manage_requests(request.user):
        raise Http404('You do not have permission to view public enquiries.')

    status_filter = request.GET.get('status', 'all').strip()
    search_query = request.GET.get('q', '').strip()

    enquiries = PublicEnquiry.objects.all().order_by('-created_at')

    if status_filter != 'all':
        enquiries = enquiries.filter(status=status_filter)

    if search_query:
        enquiries = enquiries.filter(title__icontains=search_query)

    stats = {
        'new': PublicEnquiry.objects.filter(status='new').count(),
        'reviewed': PublicEnquiry.objects.filter(status='reviewed').count(),
        'converted': PublicEnquiry.objects.filter(status='converted').count(),
        'closed': PublicEnquiry.objects.filter(status='closed').count(),
    }

    return render(request, 'service_requests/public_enquiry_list.html', {
        'enquiries': enquiries,
        'stats': stats,
        'status_filter': status_filter,
        'search_query': search_query,
        'status_choices': PublicEnquiry.STATUS_CHOICES,
    })


@login_required
def public_enquiry_detail(request, enquiry_id):
    if not can_manage_requests(request.user):
        raise Http404('You do not have permission to view public enquiries.')

    enquiry = get_object_or_404(PublicEnquiry, id=enquiry_id)

    return render(request, 'service_requests/public_enquiry_detail.html', {
        'enquiry': enquiry,
    })


@login_required
def mark_public_enquiry_reviewed(request, enquiry_id):
    if not can_manage_requests(request.user):
        raise Http404('You do not have permission to update public enquiries.')

    enquiry = get_object_or_404(PublicEnquiry, id=enquiry_id)
    enquiry.status = 'reviewed'
    enquiry.reviewed_by = request.user
    enquiry.reviewed_at = timezone.now()
    enquiry.save()

    messages.success(request, 'Public enquiry marked as reviewed.')

    return redirect('public_enquiry_detail', enquiry_id=enquiry.id)


@login_required
def mark_public_enquiry_closed(request, enquiry_id):
    if not can_manage_requests(request.user):
        raise Http404('You do not have permission to update public enquiries.')

    enquiry = get_object_or_404(PublicEnquiry, id=enquiry_id)
    enquiry.status = 'closed'
    enquiry.reviewed_by = request.user
    enquiry.reviewed_at = timezone.now()
    enquiry.save()

    messages.success(request, 'Public enquiry closed.')

    return redirect('public_enquiry_detail', enquiry_id=enquiry.id)



@login_required
def convert_public_enquiry_to_request(request, enquiry_id):
    if not can_manage_requests(request.user):
        raise Http404('You do not have permission to convert public enquiries.')

    enquiry = get_object_or_404(PublicEnquiry, id=enquiry_id)

    description = (
        f'Converted from public enquiry by {enquiry.full_name}. '
        f'Email: {enquiry.email}. '
        f'Phone: {enquiry.phone_number}. '
        f'Company: {enquiry.company_name}.'
        f'\n\n{enquiry.description}'
    )

    service_request = ServiceRequest.objects.create(
        submitted_by=request.user,
        title=enquiry.title,
        request_type=enquiry.enquiry_type,
        priority=enquiry.priority,
        description=description,
        supporting_file=enquiry.attachment,
        status='submitted',
    )

    enquiry.status = 'converted'
    enquiry.converted_request = service_request
    enquiry.reviewed_by = request.user
    enquiry.reviewed_at = timezone.now()
    enquiry.save()

    create_request_activity(
        service_request,
        'request_submitted',
        'Request created from public enquiry',
        f'{request.user.username} converted a public enquiry into a service request.',
        request.user
    )

    messages.success(request, 'Public enquiry converted into a service request.')

    return redirect('request_detail', request_id=service_request.id)

