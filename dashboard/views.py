from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from clients.models import ClientFolder
from clients.models import ClientFile
from documents.models import GeneratedDocument
from workflows.models import WorkflowLog

from .models import ActivityLog
from service_requests.models import ServiceRequestActivity
from operations.models import InternalTaskComment
from operations.models import OperationsAnnouncement
from workflows.models import WorkflowLog


def landing_page(request):
    return render(request, 'dashboard/landing.html')


@login_required
def home(request):
    stats = {
        'clients_created': ClientFolder.objects.count(),
        'total_files': ClientFile.objects.count(),
        'documents_generated': GeneratedDocument.objects.count(),
        'workflows_run': WorkflowLog.objects.count(),
    }

    recent_folders = ClientFolder.objects.all().order_by('-created_at')[:5]
    recent_activity = ActivityLog.objects.all().order_by('-created_at')[:8]

    return render(request, 'dashboard/admin_dashboard.html', {
        'stats': stats,
        'recent_folders': recent_folders,
        'recent_activity': recent_activity,
    })


from django.contrib.auth.decorators import login_required
from service_requests.models import ServiceRequestActivity
from operations.models import InternalTaskComment
from operations.models import OperationsAnnouncement
from workflows.models import WorkflowLog


@login_required
def activity_feed(request):
    feed_type = request.GET.get('type', 'all').strip()
    search_query = request.GET.get('q', '').strip()

    feed_items = []

    for item in ActivityLog.objects.all().order_by('-created_at')[:80]:
        feed_items.append({
            'type': 'Platform',
            'label': item.get_action_display(),
            'title': item.title,
            'description': item.description,
            'created_at': item.created_at,
            'actor': 'System',
            'url': '',
        })

    for item in ServiceRequestActivity.objects.select_related('service_request', 'actor').all().order_by('-created_at')[:80]:
        feed_items.append({
            'type': 'Request',
            'label': item.get_action_display(),
            'title': item.title,
            'description': item.description,
            'created_at': item.created_at,
            'actor': item.actor.username if item.actor else 'System',
            'url': f'/requests/{item.service_request.id}/',
        })

    for item in InternalTaskComment.objects.select_related('task', 'author').all().order_by('-created_at')[:80]:
        feed_items.append({
            'type': 'Task',
            'label': 'Task Comment',
            'title': item.task.title,
            'description': item.comment,
            'created_at': item.created_at,
            'actor': item.author.username,
            'url': f'/operations/{item.task.id}/',
        })

    for item in WorkflowLog.objects.select_related('workflow').all().order_by('-created_at')[:80]:
        feed_items.append({
            'type': 'Workflow',
            'label': 'Workflow Log',
            'title': item.workflow.name,
            'description': item.message,
            'created_at': item.created_at,
            'actor': 'Workflow Engine',
            'url': '/workflows/',
        })

    for item in OperationsAnnouncement.objects.select_related('created_by').all().order_by('-created_at')[:80]:
        feed_items.append({
            'type': 'Announcement',
            'label': item.get_priority_display(),
            'title': item.title,
            'description': item.message,
            'created_at': item.created_at,
            'actor': item.created_by.username if item.created_by else 'System',
            'url': f'/operations/announcements/{item.id}/',
        })

    if feed_type != 'all':
        feed_items = [
            item for item in feed_items
            if item['type'].lower() == feed_type.lower()
        ]

    if search_query:
        query = search_query.lower()

        feed_items = [
            item for item in feed_items
            if query in item['title'].lower()
            or query in item['description'].lower()
            or query in item['actor'].lower()
            or query in item['label'].lower()
            or query in item['type'].lower()
        ]

    feed_items = sorted(
        feed_items,
        key=lambda item: item['created_at'],
        reverse=True
    )[:120]

    stats = {
        'total': len(feed_items),
        'platform': len([item for item in feed_items if item['type'] == 'Platform']),
        'requests': len([item for item in feed_items if item['type'] == 'Request']),
        'tasks': len([item for item in feed_items if item['type'] == 'Task']),
        'workflows': len([item for item in feed_items if item['type'] == 'Workflow']),
        'announcements': len([item for item in feed_items if item['type'] == 'Announcement']),
    }

    return render(request, 'dashboard/activity_feed.html', {
        'feed_items': feed_items,
        'stats': stats,
        'feed_type': feed_type,
        'search_query': search_query,
    })

@login_required
def operational_health_dashboard(request):
    from service_requests.models import ServiceRequest
    from service_requests.models import ServiceRequestResponse
    from service_requests.models import PublicEnquiry
    from operations.models import InternalTask
    from workflows.models import WorkflowLog
    from django.utils import timezone

    today = timezone.now().date()

    requests = ServiceRequest.objects.all()
    responses = ServiceRequestResponse.objects.all()
    tasks = InternalTask.objects.all()
    enquiries = PublicEnquiry.objects.all()
    workflow_logs = WorkflowLog.objects.all()

    total_requests = requests.count()
    completed_requests = requests.filter(status='completed').count()
    pending_requests = requests.exclude(status='completed').count()
    under_review_requests = requests.filter(status='under_review').count()

    overdue_requests = 0
    for item in requests:
        if hasattr(item, 'is_overdue') and item.is_overdue():
            overdue_requests += 1

    overdue_tasks = 0
    for task in tasks:
        if task.is_overdue():
            overdue_tasks += 1

    blocked_tasks = tasks.filter(status='blocked').count()
    open_enquiries = enquiries.filter(status='new').count()

    total_responses = responses.count()
    pending_confirmations = responses.filter(confirmation_status='pending').count()
    accepted_responses = responses.filter(confirmation_status='accepted').count()
    changes_requested = responses.filter(confirmation_status='changes_requested').count()

    workflow_errors = workflow_logs.filter(message__icontains='error').count() + workflow_logs.filter(message__icontains='fail').count()
    backup_logs = workflow_logs.filter(workflow__name__icontains='backup').count()

    completion_rate = 0
    confirmation_rate = 0

    if total_requests > 0:
        completion_rate = round((completed_requests / total_requests) * 100)

    if total_responses > 0:
        confirmation_rate = round(((accepted_responses + changes_requested) / total_responses) * 100)

    risk_score = 0

    if overdue_tasks > 0:
        risk_score += 25

    if overdue_requests > 0:
        risk_score += 25

    if blocked_tasks > 0:
        risk_score += 15

    if pending_confirmations > accepted_responses:
        risk_score += 15

    if workflow_errors > 0:
        risk_score += 15

    if backup_logs == 0:
        risk_score += 5

    if risk_score <= 20:
        health_status = 'Good'
        health_message = 'Operations look stable. No major warning signs detected.'
        health_class = 'health-good'
    elif risk_score <= 50:
        health_status = 'Needs Attention'
        health_message = 'Some areas need follow-up. Review overdue work, confirmations, and workflow activity.'
        health_class = 'health-warning'
    else:
        health_status = 'At Risk'
        health_message = 'Operational risk is high. Prioritise overdue work, blocked tasks, and workflow issues.'
        health_class = 'health-danger'

    recommended_actions = []

    if overdue_tasks > 0:
        recommended_actions.append('Review overdue internal tasks and reassign work where needed.')

    if overdue_requests > 0:
        recommended_actions.append('Review overdue client requests and update due dates or owners.')

    if blocked_tasks > 0:
        recommended_actions.append('Open blocked tasks and resolve blockers before they delay delivery.')

    if pending_confirmations > 0:
        recommended_actions.append('Follow up on client responses still pending confirmation.')

    if open_enquiries > 0:
        recommended_actions.append('Review new public enquiries and convert valid ones into requests.')

    if workflow_errors > 0:
        recommended_actions.append('Review workflow logs for error or failed automation messages.')

    if backup_logs == 0:
        recommended_actions.append('Run and confirm the backup workflow so the system has backup evidence.')

    if not recommended_actions:
        recommended_actions.append('Maintain current rhythm and continue monitoring weekly.')

    return render(request, 'dashboard/operational_health.html', {
        'health_status': health_status,
        'health_message': health_message,
        'health_class': health_class,
        'risk_score': risk_score,
        'completion_rate': completion_rate,
        'confirmation_rate': confirmation_rate,
        'stats': {
            'total_requests': total_requests,
            'completed_requests': completed_requests,
            'pending_requests': pending_requests,
            'under_review_requests': under_review_requests,
            'overdue_requests': overdue_requests,
            'total_tasks': tasks.count(),
            'overdue_tasks': overdue_tasks,
            'blocked_tasks': blocked_tasks,
            'open_enquiries': open_enquiries,
            'total_responses': total_responses,
            'pending_confirmations': pending_confirmations,
            'accepted_responses': accepted_responses,
            'changes_requested': changes_requested,
            'workflow_errors': workflow_errors,
            'backup_logs': backup_logs,
        },
        'recommended_actions': recommended_actions,
    })

@login_required
def operational_health_dashboard(request):
    from service_requests.models import ServiceRequest
    from service_requests.models import ServiceRequestResponse
    from service_requests.models import PublicEnquiry
    from operations.models import InternalTask
    from workflows.models import WorkflowLog
    from django.utils import timezone

    today = timezone.now().date()

    requests = ServiceRequest.objects.all()
    responses = ServiceRequestResponse.objects.all()
    tasks = InternalTask.objects.all()
    enquiries = PublicEnquiry.objects.all()
    workflow_logs = WorkflowLog.objects.all()

    total_requests = requests.count()
    completed_requests = requests.filter(status='completed').count()
    pending_requests = requests.exclude(status='completed').count()
    under_review_requests = requests.filter(status='under_review').count()

    overdue_requests = 0
    for item in requests:
        if hasattr(item, 'is_overdue') and item.is_overdue():
            overdue_requests += 1

    overdue_tasks = 0
    for task in tasks:
        if task.is_overdue():
            overdue_tasks += 1

    blocked_tasks = tasks.filter(status='blocked').count()
    open_enquiries = enquiries.filter(status='new').count()

    total_responses = responses.count()
    pending_confirmations = responses.filter(confirmation_status='pending').count()
    accepted_responses = responses.filter(confirmation_status='accepted').count()
    changes_requested = responses.filter(confirmation_status='changes_requested').count()

    workflow_errors = workflow_logs.filter(message__icontains='error').count() + workflow_logs.filter(message__icontains='fail').count()
    backup_logs = workflow_logs.filter(workflow__name__icontains='backup').count()

    completion_rate = 0
    confirmation_rate = 0

    if total_requests > 0:
        completion_rate = round((completed_requests / total_requests) * 100)

    if total_responses > 0:
        confirmation_rate = round(((accepted_responses + changes_requested) / total_responses) * 100)

    risk_score = 0

    if overdue_tasks > 0:
        risk_score += 25

    if overdue_requests > 0:
        risk_score += 25

    if blocked_tasks > 0:
        risk_score += 15

    if pending_confirmations > accepted_responses:
        risk_score += 15

    if workflow_errors > 0:
        risk_score += 15

    if backup_logs == 0:
        risk_score += 5

    if risk_score <= 20:
        health_status = 'Good'
        health_message = 'Operations look stable. No major warning signs detected.'
        health_class = 'health-good'
    elif risk_score <= 50:
        health_status = 'Needs Attention'
        health_message = 'Some areas need follow-up. Review overdue work, confirmations, and workflow activity.'
        health_class = 'health-warning'
    else:
        health_status = 'At Risk'
        health_message = 'Operational risk is high. Prioritise overdue work, blocked tasks, and workflow issues.'
        health_class = 'health-danger'

    recommended_actions = []

    if overdue_tasks > 0:
        recommended_actions.append('Review overdue internal tasks and reassign work where needed.')

    if overdue_requests > 0:
        recommended_actions.append('Review overdue client requests and update due dates or owners.')

    if blocked_tasks > 0:
        recommended_actions.append('Open blocked tasks and resolve blockers before they delay delivery.')

    if pending_confirmations > 0:
        recommended_actions.append('Follow up on client responses still pending confirmation.')

    if open_enquiries > 0:
        recommended_actions.append('Review new public enquiries and convert valid ones into requests.')

    if workflow_errors > 0:
        recommended_actions.append('Review workflow logs for error or failed automation messages.')

    if backup_logs == 0:
        recommended_actions.append('Run and confirm the backup workflow so the system has backup evidence.')

    if not recommended_actions:
        recommended_actions.append('Maintain current rhythm and continue monitoring weekly.')

    return render(request, 'dashboard/operational_health.html', {
        'health_status': health_status,
        'health_message': health_message,
        'health_class': health_class,
        'risk_score': risk_score,
        'completion_rate': completion_rate,
        'confirmation_rate': confirmation_rate,
        'stats': {
            'total_requests': total_requests,
            'completed_requests': completed_requests,
            'pending_requests': pending_requests,
            'under_review_requests': under_review_requests,
            'overdue_requests': overdue_requests,
            'total_tasks': tasks.count(),
            'overdue_tasks': overdue_tasks,
            'blocked_tasks': blocked_tasks,
            'open_enquiries': open_enquiries,
            'total_responses': total_responses,
            'pending_confirmations': pending_confirmations,
            'accepted_responses': accepted_responses,
            'changes_requested': changes_requested,
            'workflow_errors': workflow_errors,
            'backup_logs': backup_logs,
        },
        'recommended_actions': recommended_actions,
    })

def client_landing_page(request):
    return render(request, 'dashboard/client_landing.html')

@login_required
def ai_operations_assistant(request):
    from service_requests.models import ServiceRequest
    from service_requests.models import ServiceRequestResponse
    from service_requests.models import PublicEnquiry
    from operations.models import InternalTask
    from workflows.models import WorkflowLog

    question = request.GET.get('q', '').strip()

    requests = ServiceRequest.objects.all()
    responses = ServiceRequestResponse.objects.all()
    tasks = InternalTask.objects.all()
    enquiries = PublicEnquiry.objects.all()
    workflow_logs = WorkflowLog.objects.all()

    overdue_tasks = [task for task in tasks if task.is_overdue()]
    overdue_requests = [item for item in requests if hasattr(item, 'is_overdue') and item.is_overdue()]

    blocked_tasks = tasks.filter(status='blocked')
    under_review_requests = requests.filter(status='under_review')
    pending_confirmations = responses.filter(confirmation_status='pending')
    new_enquiries = enquiries.filter(status='new')
    workflow_errors = workflow_logs.filter(message__icontains='error') | workflow_logs.filter(message__icontains='fail')

    answer_title = 'Ask a question about operations'
    answer_lines = [
        'Try asking: What needs attention today?',
        'You can also ask about overdue tasks, blocked tasks, pending confirmations, public enquiries, workflow errors, or under-review requests.',
    ]

    action_cards = [
        {
            'title': 'Open Health Dashboard',
            'description': 'View overall operational risk and health signals.',
            'url': '/dashboard/health/',
        },
        {
            'title': 'Open Operations Board',
            'description': 'Review active, blocked, overdue, and completed tasks.',
            'url': '/operations/board/',
        },
    ]

    lowered = question.lower()

    if question:
        if 'attention' in lowered or 'today' in lowered or 'urgent' in lowered:
            answer_title = 'What needs attention today'

            answer_lines = [
                f'{len(overdue_tasks)} overdue task(s).',
                f'{len(overdue_requests)} overdue request(s).',
                f'{blocked_tasks.count()} blocked task(s).',
                f'{pending_confirmations.count()} response(s) pending client confirmation.',
                f'{new_enquiries.count()} new public enquiry/enquiries.',
                f'{workflow_errors.count()} workflow error/failure log(s).',
            ]

            action_cards = [
                {'title': 'Open Operations Board', 'description': 'Review overdue and blocked tasks.', 'url': '/operations/board/'},
                {'title': 'Open Requests', 'description': 'Review overdue and under-review requests.', 'url': '/requests/'},
                {'title': 'Open Public Enquiries', 'description': 'Review new external enquiries.', 'url': '/requests/public-enquiries/'},
                {'title': 'Open Workflows', 'description': 'Review workflow logs and automation issues.', 'url': '/workflows/'},
            ]

        elif 'overdue' in lowered or 'late' in lowered:
            answer_title = 'Overdue work summary'

            answer_lines = [
                f'There are {len(overdue_tasks)} overdue internal task(s).',
                f'There are {len(overdue_requests)} overdue service request(s).',
            ]

            for task in overdue_tasks[:5]:
                answer_lines.append(f'- Task: {task.title}')

            for item in overdue_requests[:5]:
                answer_lines.append(f'- Request: {item.title}')

            action_cards = [
                {'title': 'Open Operations Board', 'description': 'Review overdue tasks.', 'url': '/operations/board/'},
                {'title': 'Open Requests', 'description': 'Review overdue requests.', 'url': '/requests/'},
            ]

        elif 'blocked' in lowered:
            answer_title = 'Blocked task summary'

            answer_lines = [
                f'There are {blocked_tasks.count()} blocked task(s).',
            ]

            for task in blocked_tasks[:8]:
                answer_lines.append(f'- {task.title}')

            action_cards = [
                {'title': 'Open Operations Board', 'description': 'Review blocked tasks.', 'url': '/operations/board/'},
                {'title': 'Open Task Dashboard', 'description': 'Filter and manage internal tasks.', 'url': '/operations/'},
            ]

        elif 'confirmation' in lowered or 'confirm' in lowered or 'pending response' in lowered:
            answer_title = 'Pending confirmation summary'

            answer_lines = [
                f'There are {pending_confirmations.count()} response(s) pending client confirmation.',
            ]

            for response in pending_confirmations[:8]:
                answer_lines.append(f'- {response.service_request.title}')

            action_cards = [
                {'title': 'Open Request Analytics', 'description': 'Review confirmation metrics.', 'url': '/analytics/request-analytics/'},
                {'title': 'Open Requests', 'description': 'Follow up on client confirmations.', 'url': '/requests/'},
            ]

        elif 'workflow' in lowered or 'error' in lowered or 'fail' in lowered:
            answer_title = 'Workflow reliability summary'

            answer_lines = [
                f'There are {workflow_errors.count()} workflow log(s) mentioning error or failure.',
                f'Total workflow logs recorded: {workflow_logs.count()}.',
            ]

            for log in workflow_errors[:8]:
                answer_lines.append(f'- {log.workflow.name}: {log.message}')

            action_cards = [
                {'title': 'Open Workflows', 'description': 'Review workflow activity.', 'url': '/workflows/'},
                {'title': 'Open Activity Feed', 'description': 'View workflow events inside the unified feed.', 'url': '/dashboard/activity-feed/'},
            ]

        elif 'enquiry' in lowered or 'enquiries' in lowered or 'public' in lowered:
            answer_title = 'Public enquiry summary'

            answer_lines = [
                f'There are {new_enquiries.count()} new public enquiry/enquiries.',
            ]

            for enquiry in new_enquiries[:8]:
                answer_lines.append(f'- {enquiry.title} from {enquiry.full_name}')

            action_cards = [
                {'title': 'Open Public Enquiries', 'description': 'Review and convert enquiries.', 'url': '/requests/public-enquiries/'},
                {'title': 'Submit Public Enquiry', 'description': 'Open the public enquiry form.', 'url': '/requests/public-enquiry/'},
            ]

        elif 'under review' in lowered or 'review' in lowered:
            answer_title = 'Requests under review'

            answer_lines = [
                f'There are {under_review_requests.count()} request(s) under review.',
            ]

            for item in under_review_requests[:8]:
                answer_lines.append(f'- {item.title}')

            action_cards = [
                {'title': 'Open Requests', 'description': 'Review request queue.', 'url': '/requests/?status=under_review'},
                {'title': 'Open Analytics', 'description': 'Check request performance.', 'url': '/analytics/request-analytics/'},
            ]

        elif 'client' in lowered or 'clients' in lowered:
            answer_title = 'Client activity guidance'

            answer_lines = [
                'Client activity is best reviewed through client profiles, request history, and the activity feed.',
                'Open Client Folders to inspect client-specific documents, requests, files, and notes.',
            ]

            action_cards = [
                {'title': 'Open Client Folders', 'description': 'Review client profiles and files.', 'url': '/clients/'},
                {'title': 'Open Activity Feed', 'description': 'Review recent activity across the platform.', 'url': '/dashboard/activity-feed/'},
            ]

        else:
            answer_title = 'Operations assistant response'

            answer_lines = [
                'I can help with operational questions such as:',
                '- What needs attention today?',
                '- What tasks are overdue?',
                '- Show blocked tasks.',
                '- Which responses need client confirmation?',
                '- Are there workflow errors?',
                '- Show public enquiries.',
                '- What requests are under review?',
            ]

    suggested_questions = [
        'What needs attention today?',
        'What tasks are overdue?',
        'Show blocked tasks.',
        'Which responses need confirmation?',
        'Are there workflow errors?',
        'Show public enquiries.',
        'What requests are under review?',
        'Show client activity.',
    ]

    return render(request, 'dashboard/ai_operations_assistant.html', {
        'question': question,
        'answer_title': answer_title,
        'answer_lines': answer_lines,
        'action_cards': action_cards,
        'suggested_questions': suggested_questions,
    })

@login_required
def global_search(request):
    from django.db.models import Q
    from django.utils.dateparse import parse_date

    from clients.models import ClientFolder
    from clients.models import ClientFile
    from documents.models import GeneratedDocument
    from service_requests.models import ServiceRequest
    from service_requests.models import PublicEnquiry
    from operations.models import InternalTask
    from operations.models import OperationsAnnouncement
    from workflows.models import WorkflowLog

    query = request.GET.get('q', '').strip()

    selected_categories = request.GET.getlist('categories')

    if not selected_categories:
        selected_categories = ['all']

    if 'all' in selected_categories:
        selected_categories = ['all']

    status = request.GET.get('status', 'all').strip()
    priority = request.GET.get('priority', 'all').strip()
    document_type = request.GET.get('document_type', '').strip()
    client_name = request.GET.get('client_name', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    sort = request.GET.get('sort', 'newest').strip()

    parsed_from = parse_date(date_from) if date_from else None
    parsed_to = parse_date(date_to) if date_to else None

    results = []

    def category_allowed(name):
        return 'all' in selected_categories or name in selected_categories

    def date_allowed(date_value):
        if not date_value:
            return True

        date_only = date_value.date() if hasattr(date_value, 'date') else date_value

        if parsed_from and date_only < parsed_from:
            return False

        if parsed_to and date_only > parsed_to:
            return False

        return True

    def add_result(category_name, title, description, url, date_value, status_value='', priority_value=''):
        if not date_allowed(date_value):
            return

        if status != 'all' and status_value and status_value != status:
            return

        if priority != 'all' and priority_value and priority_value != priority:
            return

        results.append({
            'category': category_name,
            'title': title,
            'description': description,
            'url': url,
            'date': date_value,
            'status': status_value,
            'priority': priority_value,
        })

    has_query = bool(query)
    q_value = query if query else ''

    if category_allowed('clients'):
        items = ClientFolder.objects.all()

        if has_query:
            items = items.filter(
                Q(client_name__icontains=q_value) |
                Q(client_email__icontains=q_value) |
                Q(notes__icontains=q_value)
            )

        if client_name:
            items = items.filter(client_name__icontains=client_name)

        items = items.order_by('-created_at')[:40]

        for item in items:
            add_result(
                'Client',
                item.client_name,
                item.client_email or 'Client folder',
                f'/clients/{item.id}/profile/',
                item.created_at
            )

    if category_allowed('files'):
        items = ClientFile.objects.select_related('client_folder').all()

        if has_query:
            items = items.filter(
                Q(title__icontains=q_value) |
                Q(client_folder__client_name__icontains=q_value) |
                Q(client_folder__client_email__icontains=q_value) |
                Q(status__icontains=q_value) |
                Q(subfolder__icontains=q_value)
            )

        if client_name:
            items = items.filter(client_folder__client_name__icontains=client_name)

        items = items.order_by('-uploaded_at')[:40]

        for item in items:
            add_result(
                'File',
                item.title,
                f'{item.client_folder.client_name} · {item.get_status_display()}',
                f'/clients/files/{item.id}/preview/',
                item.uploaded_at,
                item.status
            )

    if category_allowed('documents'):
        items = GeneratedDocument.objects.all()

        if has_query:
            items = items.filter(
                Q(title__icontains=q_value) |
                Q(client_name__icontains=q_value) |
                Q(client_email__icontains=q_value) |
                Q(document_type__icontains=q_value)
            )

        if client_name:
            items = items.filter(client_name__icontains=client_name)

        if document_type:
            items = items.filter(document_type__icontains=document_type)

        items = items.order_by('-created_at')[:40]

        for item in items:
            add_result(
                'Document',
                item.title,
                f'{item.client_name} · {item.client_email} · {item.document_type}',
                f'/documents/{item.id}/download/',
                item.created_at
            )

    if category_allowed('requests'):
        items = ServiceRequest.objects.select_related(
            'submitted_by',
            'assigned_to',
            'linked_folder',
        ).all()

        if has_query:
            items = items.filter(
                Q(title__icontains=q_value) |
                Q(description__icontains=q_value) |
                Q(submitted_by__username__icontains=q_value) |
                Q(assigned_to__username__icontains=q_value) |
                Q(linked_folder__client_name__icontains=q_value) |
                Q(status__icontains=q_value) |
                Q(priority__icontains=q_value)
            )

        if client_name:
            items = items.filter(linked_folder__client_name__icontains=client_name)

        items = items.order_by('-created_at')[:40]

        for item in items:
            client_label = item.linked_folder.client_name if item.linked_folder else 'No linked client'

            add_result(
                'Request',
                item.title,
                f'{item.get_status_display()} · {item.get_request_type_display()} · {client_label}',
                f'/requests/{item.id}/',
                item.created_at,
                item.status,
                item.priority
            )

    if category_allowed('tasks'):
        items = InternalTask.objects.select_related(
            'assigned_to',
            'created_by',
            'linked_request',
            'linked_client',
            'template',
        ).all()

        if has_query:
            items = items.filter(
                Q(title__icontains=q_value) |
                Q(description__icontains=q_value) |
                Q(status__icontains=q_value) |
                Q(priority__icontains=q_value) |
                Q(assigned_to__username__icontains=q_value) |
                Q(created_by__username__icontains=q_value) |
                Q(linked_request__title__icontains=q_value) |
                Q(linked_client__client_name__icontains=q_value) |
                Q(template__name__icontains=q_value)
            )

        if client_name:
            items = items.filter(linked_client__client_name__icontains=client_name)

        items = items.order_by('-created_at')[:40]

        for item in items:
            assigned = item.assigned_to.username if item.assigned_to else 'Unassigned'

            add_result(
                'Task',
                item.title,
                f'{item.get_status_display()} · {item.get_priority_display()} · {assigned}',
                f'/operations/{item.id}/',
                item.created_at,
                item.status,
                item.priority
            )

    if category_allowed('enquiries'):
        items = PublicEnquiry.objects.all()

        if has_query:
            items = items.filter(
                Q(title__icontains=q_value) |
                Q(description__icontains=q_value) |
                Q(full_name__icontains=q_value) |
                Q(email__icontains=q_value) |
                Q(phone_number__icontains=q_value) |
                Q(company_name__icontains=q_value) |
                Q(status__icontains=q_value)
            )

        if client_name:
            items = items.filter(
                Q(full_name__icontains=client_name) |
                Q(company_name__icontains=client_name)
            )

        items = items.order_by('-created_at')[:40]

        for item in items:
            add_result(
                'Public Enquiry',
                item.title,
                f'{item.full_name} · {item.email} · {item.company_name or "No company"} · {item.get_status_display()}',
                f'/requests/public-enquiries/{item.id}/',
                item.created_at,
                item.status
            )

    if category_allowed('announcements'):
        items = OperationsAnnouncement.objects.select_related('created_by').all()

        if has_query:
            items = items.filter(
                Q(title__icontains=q_value) |
                Q(message__icontains=q_value) |
                Q(priority__icontains=q_value) |
                Q(created_by__username__icontains=q_value)
            )

        items = items.order_by('-created_at')[:40]

        for item in items:
            add_result(
                'Announcement',
                item.title,
                f'{item.get_priority_display()} · {item.message[:140]}',
                f'/operations/announcements/{item.id}/',
                item.created_at,
                '',
                item.priority
            )

    if category_allowed('workflows'):
        items = WorkflowLog.objects.select_related('workflow').all()

        if has_query:
            items = items.filter(
                Q(message__icontains=q_value) |
                Q(workflow__name__icontains=q_value)
            )

        items = items.order_by('-created_at')[:40]

        for item in items:
            add_result(
                'Workflow Log',
                item.workflow.name,
                item.message,
                '/workflows/',
                item.created_at
            )

    if sort == 'oldest':
        results = sorted(results, key=lambda item: item['date'])
    elif sort == 'title':
        results = sorted(results, key=lambda item: item['title'].lower())
    elif sort == 'category':
        results = sorted(results, key=lambda item: item['category'].lower())
    else:
        results = sorted(results, key=lambda item: item['date'], reverse=True)

    stats = {
        'total': len(results),
        'clients': len([item for item in results if item['category'] == 'Client']),
        'files': len([item for item in results if item['category'] == 'File']),
        'documents': len([item for item in results if item['category'] == 'Document']),
        'requests': len([item for item in results if item['category'] == 'Request']),
        'tasks': len([item for item in results if item['category'] == 'Task']),
        'enquiries': len([item for item in results if item['category'] == 'Public Enquiry']),
        'announcements': len([item for item in results if item['category'] == 'Announcement']),
        'workflows': len([item for item in results if item['category'] == 'Workflow Log']),
    }

    recent_suggestions = [
        'overdue',
        'contract',
        'invoice',
        'client',
        'backup',
        'pending',
        'blocked',
        'approved',
    ]

    search_categories = [
        {'value': 'all', 'label': 'Everything'},
        {'value': 'clients', 'label': 'Clients'},
        {'value': 'files', 'label': 'Files'},
        {'value': 'documents', 'label': 'Documents'},
        {'value': 'requests', 'label': 'Requests'},
        {'value': 'tasks', 'label': 'Tasks'},
        {'value': 'enquiries', 'label': 'Public Enquiries'},
        {'value': 'announcements', 'label': 'Announcements'},
        {'value': 'workflows', 'label': 'Workflow Logs'},
    ]

    return render(request, 'dashboard/global_search.html', {
        'query': query,
        'selected_categories': selected_categories,
        'search_categories': search_categories,
        'status': status,
        'priority': priority,
        'document_type': document_type,
        'client_name': client_name,
        'date_from': date_from,
        'date_to': date_to,
        'sort': sort,
        'results': results,
        'stats': stats,
        'recent_suggestions': recent_suggestions,
    })

@login_required
def command_centre(request):
    from service_requests.models import ServiceRequest
    from service_requests.models import ServiceRequestResponse
    from service_requests.models import PublicEnquiry
    from operations.models import InternalTask
    from clients.models import ClientFolder
    from clients.models import ClientFile
    from workflows.models import WorkflowLog
    from django.utils import timezone

    today = timezone.now().date()

    requests = ServiceRequest.objects.all()
    responses = ServiceRequestResponse.objects.all()
    tasks = InternalTask.objects.all()
    enquiries = PublicEnquiry.objects.all()
    clients = ClientFolder.objects.all()
    files = ClientFile.objects.all()
    workflow_logs = WorkflowLog.objects.all()

    total_requests = requests.count()
    completed_requests = requests.filter(status='completed').count()
    open_requests = requests.exclude(status='completed').count()
    under_review = requests.filter(status='under_review').count()

    total_tasks = tasks.count()
    in_progress_tasks = tasks.filter(status='in_progress').count()
    blocked_tasks = tasks.filter(status='blocked').count()
    completed_tasks = tasks.filter(status='completed').count()

    overdue_tasks = 0
    overdue_requests = 0

    for task in tasks:
        if task.is_overdue():
            overdue_tasks += 1

    for item in requests:
        if hasattr(item, 'is_overdue') and item.is_overdue():
            overdue_requests += 1

    total_responses = responses.count()
    pending_confirmations = responses.filter(confirmation_status='pending').count()
    accepted_responses = responses.filter(confirmation_status='accepted').count()
    changes_requested = responses.filter(confirmation_status='changes_requested').count()

    workflow_errors = workflow_logs.filter(message__icontains='error').count() + workflow_logs.filter(message__icontains='fail').count()
    backup_logs = workflow_logs.filter(workflow__name__icontains='backup').count()

    completion_rate = 0
    task_completion_rate = 0
    confirmation_rate = 0

    if total_requests > 0:
        completion_rate = round((completed_requests / total_requests) * 100)

    if total_tasks > 0:
        task_completion_rate = round((completed_tasks / total_tasks) * 100)

    if total_responses > 0:
        confirmation_rate = round(((accepted_responses + changes_requested) / total_responses) * 100)

    risk_score = 0

    if overdue_tasks > 0:
        risk_score += 25

    if overdue_requests > 0:
        risk_score += 25

    if blocked_tasks > 0:
        risk_score += 20

    if pending_confirmations > accepted_responses:
        risk_score += 15

    if workflow_errors > 0:
        risk_score += 15

    if risk_score <= 20:
        pulse_status = 'Stable'
        pulse_class = 'pulse-stable'
        pulse_message = 'Operations are moving with low risk signals.'
    elif risk_score <= 50:
        pulse_status = 'Watch'
        pulse_class = 'pulse-watch'
        pulse_message = 'Some operational areas need attention today.'
    else:
        pulse_status = 'Critical'
        pulse_class = 'pulse-critical'
        pulse_message = 'High-risk signals detected. Prioritise action immediately.'

    latest_requests = requests.select_related('submitted_by', 'assigned_to').order_by('-created_at')[:5]
    latest_tasks = tasks.select_related('assigned_to', 'linked_client').order_by('-created_at')[:5]
    latest_responses = responses.select_related('service_request', 'responded_by').order_by('-responded_at')[:5]
    latest_workflows = workflow_logs.select_related('workflow').order_by('-created_at')[:5]

    return render(request, 'dashboard/command_centre.html', {
        'today': today,
        'pulse_status': pulse_status,
        'pulse_class': pulse_class,
        'pulse_message': pulse_message,
        'risk_score': risk_score,
        'stats': {
            'total_requests': total_requests,
            'completed_requests': completed_requests,
            'open_requests': open_requests,
            'under_review': under_review,
            'completion_rate': completion_rate,
            'total_tasks': total_tasks,
            'in_progress_tasks': in_progress_tasks,
            'blocked_tasks': blocked_tasks,
            'completed_tasks': completed_tasks,
            'task_completion_rate': task_completion_rate,
            'overdue_tasks': overdue_tasks,
            'overdue_requests': overdue_requests,
            'total_responses': total_responses,
            'pending_confirmations': pending_confirmations,
            'accepted_responses': accepted_responses,
            'changes_requested': changes_requested,
            'confirmation_rate': confirmation_rate,
            'clients': clients.count(),
            'files': files.count(),
            'enquiries': enquiries.filter(status='new').count(),
            'workflow_logs': workflow_logs.count(),
            'workflow_errors': workflow_errors,
            'backup_logs': backup_logs,
        },
        'latest_requests': latest_requests,
        'latest_tasks': latest_tasks,
        'latest_responses': latest_responses,
        'latest_workflows': latest_workflows,
    })




