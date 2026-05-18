import csv
from collections import defaultdict

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.db.models import Sum
from django.http import Http404
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from accounts.permissions import can_view_exports

from clients.models import ClientFolder
from clients.models import ClientFile
from documents.models import GeneratedDocument
from workflows.models import WorkflowLog
from dashboard.activity import log_activity

from service_requests.models import ServiceRequest
from service_requests.models import ServiceRequestResponse
from service_requests.models import ServiceRequestActivity


def require_export_permission(user):
    if not can_view_exports(user):
        raise Http404('You do not have permission to view analytics or exports.')


def build_request_analytics_summary():
    requests = ServiceRequest.objects.all()
    responses = ServiceRequestResponse.objects.all()

    total_requests = requests.count()
    completed = requests.filter(status='completed').count()
    pending = requests.exclude(status='completed').count()
    under_review = requests.filter(status='under_review').count()
    rejected = requests.filter(status='rejected').count()
    approved = requests.filter(status='approved').count()

    total_responses = responses.count()
    total_downloads = responses.aggregate(total=Sum('download_count'))['total'] or 0

    accepted = responses.filter(confirmation_status='accepted').count()
    changes_requested = responses.filter(confirmation_status='changes_requested').count()
    pending_confirmation = responses.filter(confirmation_status='pending').count()

    completion_rate = 0
    response_rate = 0
    acceptance_rate = 0

    if total_requests > 0:
        completion_rate = round((completed / total_requests) * 100, 1)
        response_rate = round((total_responses / total_requests) * 100, 1)

    if total_responses > 0:
        acceptance_rate = round((accepted / total_responses) * 100, 1)

    top_type = requests.values('request_type').annotate(total=Count('id')).order_by('-total').first()
    top_client = requests.values('submitted_by__username').annotate(total=Count('id')).order_by('-total').first()
    top_staff = responses.values('responded_by__username').annotate(total=Count('id')).order_by('-total').first()

    summary_lines = [
        'AI Operations Summary',
        '',
        f'Total requests recorded: {total_requests}.',
        f'Completed requests: {completed}. Pending requests: {pending}.',
        f'Completion rate: {completion_rate}%. Response rate: {response_rate}%.',
        f'Requests currently under review: {under_review}. Approved: {approved}. Rejected: {rejected}.',
        f'Total staff responses submitted: {total_responses}.',
        f'Total response attachment downloads: {total_downloads}.',
        f'Responses accepted: {accepted}. Changes requested: {changes_requested}. Pending confirmations: {pending_confirmation}.',
        f'Response acceptance rate: {acceptance_rate}%.',
        '',
        'Key insight:',
    ]

    if total_requests == 0:
        summary_lines.append('There is not enough request data yet. Start by submitting and processing requests.')
    elif pending > completed:
        summary_lines.append('The request pipeline needs attention because pending requests are higher than completed requests.')
    elif pending_confirmation > accepted:
        summary_lines.append('Many responses are still waiting for client confirmation. Follow up with clients to close the loop.')
    elif changes_requested > 0:
        summary_lines.append('Some responses resulted in requested changes. Review recurring issues in fulfilment quality.')
    else:
        summary_lines.append('The request and delivery pipeline appears controlled based on current completion and confirmation data.')

    if top_type:
        summary_lines.append(f'Most common request type: {top_type["request_type"]} with {top_type["total"]} request(s).')

    if top_client:
        summary_lines.append(f'Most active client/user: {top_client["submitted_by__username"] or "Unknown"} with {top_client["total"]} request(s).')

    if top_staff:
        summary_lines.append(f'Most active staff responder: {top_staff["responded_by__username"] or "Unknown"} with {top_staff["total"]} response(s).')

    summary_lines.extend([
        '',
        'Recommended next actions:',
        '- Review pending and under-review requests.',
        '- Follow up on responses pending confirmation.',
        '- Review responses where clients requested changes.',
        '- Monitor downloads to confirm clients are receiving deliverables.',
    ])

    return '\n'.join(summary_lines)


def build_documents_summary():
    documents = GeneratedDocument.objects.all()

    total = documents.count()
    total_amount = sum([doc.amount for doc in documents])
    latest = documents.order_by('-created_at').first()

    summary_lines = [
        'AI Document Summary',
        '',
        f'Total generated documents: {total}.',
        f'Total document amount value: R {total_amount}.',
    ]

    if latest:
        summary_lines.append(f'Latest document: {latest.title} for {latest.client_name}.')
    else:
        summary_lines.append('No generated documents exist yet.')

    summary_lines.extend([
        '',
        'Recommended next actions:',
        '- Review generated documents for missing files.',
        '- Link important documents to service requests.',
        '- Export documents if you need reporting evidence.',
    ])

    return '\n'.join(summary_lines)


def build_files_summary():
    files = ClientFile.objects.select_related('client_folder').all()

    total = files.count()
    archived = files.filter(is_archived=True).count()
    active = files.filter(is_archived=False).count()
    approved = files.filter(status='approved').count()
    pending = files.filter(status='pending').count()

    summary_lines = [
        'AI File Summary',
        '',
        f'Total client files: {total}.',
        f'Active files: {active}. Archived files: {archived}.',
        f'Approved files: {approved}. Pending review files: {pending}.',
        '',
        'Key insight:',
    ]

    if pending > approved:
        summary_lines.append('There are more files waiting for review than approved files, so the approval queue needs attention.')
    else:
        summary_lines.append('The file approval flow appears controlled based on current approved versus pending files.')

    summary_lines.extend([
        '',
        'Recommended next actions:',
        '- Open the approvals dashboard.',
        '- Review pending files.',
        '- Archive outdated files.',
        '- Link important files to service requests.',
    ])

    return '\n'.join(summary_lines)


def build_workflows_summary():
    logs = WorkflowLog.objects.select_related('workflow').all().order_by('-created_at')

    total_logs = logs.count()
    latest_log = logs.first()

    workflow_count = logs.values('workflow__name').distinct().count()

    most_active_workflow = logs.values(
        'workflow__name'
    ).annotate(
        total=Count('id')
    ).order_by('-total').first()

    recent_logs = logs[:8]

    possible_failed_logs = logs.filter(message__icontains='fail')
    possible_error_logs = logs.filter(message__icontains='error')
    possible_backup_logs = logs.filter(workflow__name__icontains='backup')

    failed_count = possible_failed_logs.count() + possible_error_logs.count()
    backup_count = possible_backup_logs.count()

    summary_lines = [
        'AI Workflow Operations Summary',
        '',
        f'Total workflow log entries: {total_logs}.',
        f'Unique workflows with recorded activity: {workflow_count}.',
        f'Possible failed/error workflow messages: {failed_count}.',
        f'Backup-related workflow entries: {backup_count}.',
        '',
        'Latest workflow activity:',
    ]

    if latest_log:
        summary_lines.append(
            f'- {latest_log.workflow.name}: {latest_log.message} '
            f'({latest_log.created_at.strftime("%d %b %Y %H:%M")})'
        )
    else:
        summary_lines.append('- No workflow activity has been logged yet.')

    summary_lines.append('')

    if most_active_workflow:
        summary_lines.append(
            f'Most active workflow: {most_active_workflow["workflow__name"]} '
            f'with {most_active_workflow["total"]} log entry/entries.'
        )
    else:
        summary_lines.append('Most active workflow: Not available yet.')

    summary_lines.extend([
        '',
        'Recent workflow activity:',
    ])

    if recent_logs:
        for log in recent_logs:
            summary_lines.append(
                f'- {log.workflow.name}: {log.message} '
                f'({log.created_at.strftime("%d %b %Y %H:%M")})'
            )
    else:
        summary_lines.append('- No recent workflow logs found.')

    summary_lines.extend([
        '',
        'Key insight:',
    ])

    if total_logs == 0:
        summary_lines.append(
            'No workflow logs exist yet. This means your automation system has not recorded activity, '
            'or logging is not being triggered.'
        )
    elif failed_count > 0:
        summary_lines.append(
            'Some workflow logs mention errors or failures. These should be reviewed before relying on automation.'
        )
    elif backup_count == 0:
        summary_lines.append(
            'No backup workflow activity was detected. If backups are part of your system, run or test the backup workflow.'
        )
    else:
        summary_lines.append(
            'Workflow activity exists and no obvious failure messages were detected from the available log messages.'
        )

    summary_lines.extend([
        '',
        'Recommended next actions:',
        '- Open the Workflows page and confirm every important workflow has recent logs.',
        '- Run the daily backup workflow manually and confirm it creates a new log entry.',
        '- Search workflow logs for words like fail, error, missing, denied, or not found.',
        '- Keep workflow logs as operational evidence for audits, reporting, and troubleshooting.',
        '- Add failure logging to PowerShell scripts so broken workflows are easier to diagnose.',
    ])

    return '\n'.join(summary_lines)

@login_required
def ai_summary_centre(request):
    require_export_permission(request.user)

    return render(request, 'analytics/ai_summary_centre.html')


@login_required
def generate_ai_summary(request):
    require_export_permission(request.user)

    summary_type = request.GET.get('type', 'requests')

    if summary_type == 'documents':
        summary = build_documents_summary()
        title = 'Documents AI Summary'
    elif summary_type == 'files':
        summary = build_files_summary()
        title = 'Files AI Summary'
    elif summary_type == 'workflows':
        summary = build_workflows_summary()
        title = 'Workflows AI Summary'
    else:
        summary = build_request_analytics_summary()
        title = 'Request Analytics AI Summary'

    return render(request, 'analytics/ai_summary_result.html', {
        'title': title,
        'summary': summary,
        'summary_type': summary_type,
    })


@login_required
def request_analytics_dashboard(request):
    require_export_permission(request.user)

    today = timezone.now().date()

    requests = ServiceRequest.objects.select_related(
        'submitted_by',
        'assigned_to',
        'reviewed_by',
    ).all()

    responses = ServiceRequestResponse.objects.select_related(
        'service_request',
        'responded_by',
        'last_downloaded_by',
        'confirmed_by',
    ).all()

    total_requests = requests.count()
    completed_requests = requests.filter(status='completed').count()
    pending_requests = requests.exclude(status='completed').count()
    under_review_requests = requests.filter(status='under_review').count()
    approved_requests = requests.filter(status='approved').count()
    rejected_requests = requests.filter(status='rejected').count()

    completion_rate = 0

    if total_requests > 0:
        completion_rate = round((completed_requests / total_requests) * 100, 1)

    total_responses = responses.count()

    total_downloads = responses.aggregate(
        total=Sum('download_count')
    )['total'] or 0

    response_rate = 0

    if total_requests > 0:
        response_rate = round((total_responses / total_requests) * 100, 1)

    accepted_responses = responses.filter(confirmation_status='accepted').count()
    changes_requested_responses = responses.filter(confirmation_status='changes_requested').count()
    pending_confirmations = responses.filter(confirmation_status='pending').count()

    acceptance_rate = 0
    change_request_rate = 0
    confirmation_rate = 0

    if total_responses > 0:
        acceptance_rate = round((accepted_responses / total_responses) * 100, 1)
        change_request_rate = round((changes_requested_responses / total_responses) * 100, 1)
        confirmation_rate = round(((accepted_responses + changes_requested_responses) / total_responses) * 100, 1)

    status_breakdown = [
        {'label': 'Submitted', 'count': requests.filter(status='submitted').count(), 'class_name': 'request-status-submitted'},
        {'label': 'Under Review', 'count': under_review_requests, 'class_name': 'request-status-under_review'},
        {'label': 'Approved', 'count': approved_requests, 'class_name': 'request-status-approved'},
        {'label': 'Rejected', 'count': rejected_requests, 'class_name': 'request-status-rejected'},
        {'label': 'Completed', 'count': completed_requests, 'class_name': 'request-status-completed'},
    ]

    delivery_breakdown = [
        {
            'label': 'Pending Confirmation',
            'count': pending_confirmations,
            'class_name': 'confirmation-pending',
        },
        {
            'label': 'Accepted',
            'count': accepted_responses,
            'class_name': 'confirmation-accepted',
        },
        {
            'label': 'Changes Requested',
            'count': changes_requested_responses,
            'class_name': 'confirmation-changes_requested',
        },
    ]

    type_breakdown = requests.values('request_type').annotate(total=Count('id')).order_by('-total')

    request_type_labels = dict(ServiceRequest.REQUEST_TYPES)

    type_breakdown_display = []

    for item in type_breakdown:
        type_breakdown_display.append({
            'label': request_type_labels.get(item['request_type'], item['request_type']),
            'count': item['total'],
        })

    monthly_data = defaultdict(int)

    for item in requests:
        month_label = item.created_at.strftime('%b %Y')
        monthly_data[month_label] += 1

    monthly_volume = [{'month': key, 'count': value} for key, value in monthly_data.items()]

    top_clients = requests.values('submitted_by__username').annotate(total=Count('id')).order_by('-total')[:5]
    top_staff = responses.values('responded_by__username').annotate(total=Count('id')).order_by('-total')[:5]

    recent_requests = requests.order_by('-created_at')[:8]
    recent_responses = responses.order_by('-responded_at')[:8]

    recent_confirmations = responses.exclude(
        confirmed_at__isnull=True
    ).order_by('-confirmed_at')[:8]

    recent_timeline_events = ServiceRequestActivity.objects.select_related(
        'service_request',
        'actor',
    ).order_by('-created_at')[:10]

    latest_downloads = responses.exclude(
        last_downloaded_at__isnull=True
    ).order_by('-last_downloaded_at')[:8]

    stats = {
        'total_requests': total_requests,
        'completed_requests': completed_requests,
        'pending_requests': pending_requests,
        'under_review_requests': under_review_requests,
        'approved_requests': approved_requests,
        'rejected_requests': rejected_requests,
        'completion_rate': completion_rate,
        'total_responses': total_responses,
        'total_downloads': total_downloads,
        'response_rate': response_rate,
        'accepted_responses': accepted_responses,
        'changes_requested_responses': changes_requested_responses,
        'pending_confirmations': pending_confirmations,
        'acceptance_rate': acceptance_rate,
        'change_request_rate': change_request_rate,
        'confirmation_rate': confirmation_rate,
    }

    return render(request, 'analytics/request_analytics_dashboard.html', {
        'stats': stats,
        'status_breakdown': status_breakdown,
        'delivery_breakdown': delivery_breakdown,
        'type_breakdown': type_breakdown_display,
        'monthly_volume': monthly_volume,
        'top_clients': top_clients,
        'top_staff': top_staff,
        'recent_requests': recent_requests,
        'recent_responses': recent_responses,
        'recent_confirmations': recent_confirmations,
        'recent_timeline_events': recent_timeline_events,
        'latest_downloads': latest_downloads,
        'today': today,
    })


@login_required
def exports_home(request):
    require_export_permission(request.user)

    return render(request, 'analytics/exports_home.html')


@login_required
def export_client_folders(request):
    require_export_permission(request.user)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=\"client_folders.csv\"'

    writer = csv.writer(response)
    writer.writerow(['Client Name', 'Client Email', 'Folder Path', 'Owner', 'Created At'])

    for folder in ClientFolder.objects.all().order_by('-created_at'):
        writer.writerow([
            folder.client_name,
            folder.client_email,
            folder.folder_path,
            folder.owner.username if folder.owner else 'Unassigned',
            folder.created_at,
        ])

    log_activity('export_created', 'Client folders exported', 'CSV export created.')
    return response


@login_required
def export_client_files(request):
    require_export_permission(request.user)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=\"client_files.csv\"'

    writer = csv.writer(response)
    writer.writerow(['Title', 'Client Folder', 'Owner', 'Subfolder', 'Archived', 'Uploaded At'])

    for file in ClientFile.objects.select_related('client_folder').all().order_by('-uploaded_at'):
        writer.writerow([
            file.title,
            file.client_folder.client_name,
            file.client_folder.owner.username if file.client_folder.owner else 'Unassigned',
            file.subfolder,
            file.is_archived,
            file.uploaded_at,
        ])

    log_activity('export_created', 'Client files exported', 'CSV export created.')
    return response


@login_required
def export_documents(request):
    require_export_permission(request.user)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=\"generated_documents.csv\"'

    writer = csv.writer(response)
    writer.writerow(['Title', 'Client', 'Email', 'Type', 'Amount', 'Created At'])

    for document in GeneratedDocument.objects.all().order_by('-created_at'):
        writer.writerow([
            document.title,
            document.client_name,
            document.client_email,
            document.document_type,
            document.amount,
            document.created_at,
        ])

    log_activity('export_created', 'Documents exported', 'CSV export created.')
    return response


@login_required
def export_workflow_logs(request):
    require_export_permission(request.user)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=\"workflow_logs.csv\"'

    writer = csv.writer(response)
    writer.writerow(['Workflow', 'Message', 'Created At'])

    for log in WorkflowLog.objects.select_related('workflow').all().order_by('-created_at'):
        writer.writerow([
            log.workflow.name,
            log.message,
            log.created_at,
        ])

    log_activity('export_created', 'Workflow logs exported', 'CSV export created.')
    return response

