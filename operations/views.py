from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils import timezone

from accounts.permissions import can_manage_all_folders

from dashboard.activity import log_activity
from notifications.services import create_notification
from notifications.services import notify_admins
from service_requests.models import ServiceRequest

from .models import InternalTask
from .models import InternalTaskComment
from .models import InternalTaskChecklistItem
from .models import TaskTemplateChecklistItem
from .models import OperationsAnnouncement
from .models import TaskTemplate
from .forms import InternalTaskForm
from .forms import InternalTaskCommentForm
from .forms import InternalTaskChecklistItemForm
from .forms import TaskTemplateChecklistItemForm
from .forms import OperationsAnnouncementForm
from .forms import TaskTemplateForm


def can_manage_tasks(user):
    return can_manage_all_folders(user)


def get_visible_tasks(user):
    if can_manage_tasks(user):
        return InternalTask.objects.all()

    return InternalTask.objects.filter(assigned_to=user)


def get_accessible_task_or_404(user, task_id):
    if can_manage_tasks(user):
        return get_object_or_404(InternalTask, id=task_id)

    return get_object_or_404(
        InternalTask,
        id=task_id,
        assigned_to=user
    )


@login_required
def task_dashboard(request):
    status_filter = request.GET.get('status', 'all').strip()
    priority_filter = request.GET.get('priority', 'all').strip()
    search_query = request.GET.get('q', '').strip()

    tasks = get_visible_tasks(request.user).select_related(
        'assigned_to',
        'created_by',
        'linked_request',
        'linked_client',
    ).order_by('-created_at')

    if status_filter != 'all':
        tasks = tasks.filter(status=status_filter)

    if priority_filter != 'all':
        tasks = tasks.filter(priority=priority_filter)

    if search_query:
        tasks = tasks.filter(title__icontains=search_query)

    source = get_visible_tasks(request.user)

    overdue_count = 0

    for task in source:
        if task.is_overdue():
            overdue_count += 1

    stats = {
        'total': source.count(),
        'todo': source.filter(status='todo').count(),
        'in_progress': source.filter(status='in_progress').count(),
        'blocked': source.filter(status='blocked').count(),
        'completed': source.filter(status='completed').count(),
        'overdue': overdue_count,
    }

    pinned_announcements = OperationsAnnouncement.objects.filter(
        is_active=True,
        is_pinned=True
    ).order_by('-created_at')[:3]

    return render(request, 'operations/task_dashboard.html', {
        'tasks': tasks,
        'stats': stats,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'search_query': search_query,
        'status_choices': InternalTask.STATUS_CHOICES,
        'priority_choices': InternalTask.PRIORITY_CHOICES,
        'can_manage_tasks': can_manage_tasks(request.user),
        'pinned_announcements': pinned_announcements,
    })


@login_required
def task_board(request):
    tasks = get_visible_tasks(request.user).select_related(
        'assigned_to',
        'created_by',
        'linked_request',
        'linked_client',
    ).order_by('-created_at')

    board = {
        'todo': tasks.filter(status='todo'),
        'in_progress': tasks.filter(status='in_progress'),
        'blocked': tasks.filter(status='blocked'),
        'completed': tasks.filter(status='completed'),
    }

    stats = {
        'todo': board['todo'].count(),
        'in_progress': board['in_progress'].count(),
        'blocked': board['blocked'].count(),
        'completed': board['completed'].count(),
    }

    pinned_announcements = OperationsAnnouncement.objects.filter(
        is_active=True,
        is_pinned=True
    ).order_by('-created_at')[:3]

    return render(request, 'operations/task_board.html', {
        'board': board,
        'stats': stats,
        'can_manage_tasks': can_manage_tasks(request.user),
        'pinned_announcements': pinned_announcements,
    })


@login_required
def my_work_dashboard(request):
    my_tasks = InternalTask.objects.select_related(
        'assigned_to',
        'created_by',
        'linked_request',
        'linked_client',
    ).filter(
        assigned_to=request.user
    ).order_by('-created_at')

    overdue_tasks = []

    for task in my_tasks:
        if task.is_overdue():
            overdue_tasks.append(task)

    my_requests = request.user.assigned_requests.select_related(
        'submitted_by',
        'assigned_to',
        'linked_folder',
    ).all().order_by('-created_at')

    recent_comments = InternalTaskComment.objects.select_related(
        'task',
        'author',
    ).filter(
        task__assigned_to=request.user
    ).order_by('-created_at')[:8]

    pinned_announcements = OperationsAnnouncement.objects.filter(
        is_active=True,
        is_pinned=True
    ).order_by('-created_at')[:3]

    latest_announcements = OperationsAnnouncement.objects.filter(
        is_active=True
    ).order_by('-created_at')[:5]

    stats = {
        'total_tasks': my_tasks.count(),
        'todo': my_tasks.filter(status='todo').count(),
        'in_progress': my_tasks.filter(status='in_progress').count(),
        'blocked': my_tasks.filter(status='blocked').count(),
        'completed': my_tasks.filter(status='completed').count(),
        'overdue': len(overdue_tasks),
        'assigned_requests': my_requests.count(),
    }

    return render(request, 'operations/my_work_dashboard.html', {
        'my_tasks': my_tasks[:12],
        'overdue_tasks': overdue_tasks[:8],
        'my_requests': my_requests[:10],
        'recent_comments': recent_comments,
        'pinned_announcements': pinned_announcements,
        'latest_announcements': latest_announcements,
        'stats': stats,
    })


@login_required
def create_task(request):
    if not can_manage_tasks(request.user):
        raise Http404('You do not have permission to create tasks.')

    if request.method == 'POST':
        form = InternalTaskForm(request.POST)

        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.save()
            create_checklist_items_from_template(task)

            log_activity(
                'workflow_ran',
                f'Task created: {task.title}',
                f'{request.user.username} created an internal task.'
            )

            if task.assigned_to and task.assigned_to != request.user:
                create_notification(
                    recipient=task.assigned_to,
                    title='New task assigned',
                    message=f'You have been assigned: {task.title}',
                    notification_type='info',
                    link=f'/operations/{task.id}/'
                )

            messages.success(request, 'Task created successfully.')

            return redirect('task_detail', task_id=task.id)

    else:
        form = InternalTaskForm()

    return render(request, 'operations/task_form.html', {
        'form': form,
        'title': 'Create Task',
        'button_text': 'Create Task',
    })


@login_required
def edit_task(request, task_id):
    task = get_accessible_task_or_404(request.user, task_id)

    if request.method == 'POST':
        old_assigned_to = task.assigned_to
        old_status = task.status

        form = InternalTaskForm(request.POST, instance=task)

        if form.is_valid():
            updated_task = form.save(commit=False)

            if updated_task.status == 'completed' and old_status != 'completed':
                updated_task.completed_at = timezone.now()

            if updated_task.status != 'completed':
                updated_task.completed_at = None

            updated_task.save()

            log_activity(
                'workflow_ran',
                f'Task updated: {updated_task.title}',
                f'{request.user.username} updated an internal task.'
            )

            if updated_task.assigned_to and updated_task.assigned_to != old_assigned_to:
                create_notification(
                    recipient=updated_task.assigned_to,
                    title='Task assigned',
                    message=f'You have been assigned: {updated_task.title}',
                    notification_type='info',
                    link=f'/operations/{updated_task.id}/'
                )

            messages.success(request, 'Task updated successfully.')

            return redirect('task_detail', task_id=updated_task.id)

    else:
        form = InternalTaskForm(instance=task)

    return render(request, 'operations/task_form.html', {
        'form': form,
        'title': 'Edit Task',
        'button_text': 'Save Task',
    })


@login_required
def task_detail(request, task_id):
    task = get_accessible_task_or_404(request.user, task_id)

    if request.method == 'POST':
        comment_form = InternalTaskCommentForm(request.POST)

        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.task = task
            comment.author = request.user
            comment.save()

            log_activity(
                'workflow_ran',
                f'Task comment added: {task.title}',
                f'{request.user.username} commented on a task.'
            )

            if task.assigned_to and task.assigned_to != request.user:
                create_notification(
                    recipient=task.assigned_to,
                    title='New task comment',
                    message=f'{request.user.username} commented on {task.title}.',
                    notification_type='info',
                    link=f'/operations/{task.id}/'
                )

            messages.success(request, 'Comment added successfully.')

            return redirect('task_detail', task_id=task.id)

    else:
        comment_form = InternalTaskCommentForm()

    comments = task.comments.select_related('author').all().order_by('-created_at')
    checklist_items = task.checklist_items.select_related('completed_by').all().order_by('order', 'created_at')
    checklist_form = InternalTaskChecklistItemForm(initial={'order': checklist_items.count() + 1})

    return render(request, 'operations/task_detail.html', {
        'task': task,
        'comments': comments,
        'comment_form': comment_form,
        'checklist_items': checklist_items,
        'checklist_form': checklist_form,
        'can_manage_tasks': can_manage_tasks(request.user),
    })


@login_required
def complete_task(request, task_id):
    task = get_accessible_task_or_404(request.user, task_id)

    task.status = 'completed'
    task.completed_at = timezone.now()
    task.save()

    log_activity(
        'workflow_ran',
        f'Task completed: {task.title}',
        f'{request.user.username} completed an internal task.'
    )

    messages.success(request, 'Task marked as completed.')

    return redirect('task_detail', task_id=task.id)


@login_required
def reopen_task(request, task_id):
    task = get_accessible_task_or_404(request.user, task_id)

    task.status = 'todo'
    task.completed_at = None
    task.save()

    log_activity(
        'workflow_ran',
        f'Task reopened: {task.title}',
        f'{request.user.username} reopened an internal task.'
    )

    messages.success(request, 'Task reopened.')

    return redirect('task_detail', task_id=task.id)


@login_required
def move_task_status(request, task_id, new_status):
    task = get_accessible_task_or_404(request.user, task_id)

    valid_statuses = [
        'todo',
        'in_progress',
        'blocked',
        'completed',
        'cancelled',
    ]

    if new_status not in valid_statuses:
        raise Http404('Invalid task status.')

    task.status = new_status

    if new_status == 'completed':
        task.completed_at = timezone.now()
    else:
        task.completed_at = None

    task.save()

    log_activity(
        'workflow_ran',
        f'Task moved: {task.title}',
        f'{request.user.username} moved task to {task.get_status_display()}.'
    )

    messages.success(request, f'Task moved to {task.get_status_display()}.')

    return redirect('task_board')


@login_required
def announcement_list(request):
    announcements = OperationsAnnouncement.objects.select_related(
        'created_by'
    ).all().order_by('-is_pinned', '-created_at')

    if not can_manage_tasks(request.user):
        announcements = announcements.filter(is_active=True)

    stats = {
        'total': announcements.count(),
        'pinned': announcements.filter(is_pinned=True).count(),
        'urgent': announcements.filter(priority='urgent').count(),
        'critical': announcements.filter(priority='critical').count(),
    }

    return render(request, 'operations/announcement_list.html', {
        'announcements': announcements,
        'stats': stats,
        'can_manage_tasks': can_manage_tasks(request.user),
    })


@login_required
def announcement_detail(request, announcement_id):
    if can_manage_tasks(request.user):
        announcement = get_object_or_404(OperationsAnnouncement, id=announcement_id)
    else:
        announcement = get_object_or_404(
            OperationsAnnouncement,
            id=announcement_id,
            is_active=True
        )

    return render(request, 'operations/announcement_detail.html', {
        'announcement': announcement,
        'can_manage_tasks': can_manage_tasks(request.user),
    })


@login_required
def create_announcement(request):
    if not can_manage_tasks(request.user):
        raise Http404('You do not have permission to create announcements.')

    if request.method == 'POST':
        form = OperationsAnnouncementForm(request.POST)

        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.created_by = request.user
            announcement.save()

            log_activity(
                'workflow_ran',
                f'Announcement posted: {announcement.title}',
                f'{request.user.username} posted an operations announcement.'
            )

            notify_admins(
                title='New operations announcement',
                message=announcement.title,
                notification_type='info',
                link=f'/operations/announcements/{announcement.id}/'
            )

            messages.success(request, 'Announcement posted successfully.')

            return redirect('announcement_detail', announcement_id=announcement.id)

    else:
        form = OperationsAnnouncementForm()

    return render(request, 'operations/announcement_form.html', {
        'form': form,
        'title': 'Create Announcement',
        'button_text': 'Post Announcement',
    })


@login_required
def edit_announcement(request, announcement_id):
    if not can_manage_tasks(request.user):
        raise Http404('You do not have permission to edit announcements.')

    announcement = get_object_or_404(OperationsAnnouncement, id=announcement_id)

    if request.method == 'POST':
        form = OperationsAnnouncementForm(request.POST, instance=announcement)

        if form.is_valid():
            announcement = form.save()

            log_activity(
                'workflow_ran',
                f'Announcement updated: {announcement.title}',
                f'{request.user.username} updated an operations announcement.'
            )

            messages.success(request, 'Announcement updated successfully.')

            return redirect('announcement_detail', announcement_id=announcement.id)

    else:
        form = OperationsAnnouncementForm(instance=announcement)

    return render(request, 'operations/announcement_form.html', {
        'form': form,
        'title': 'Edit Announcement',
        'button_text': 'Save Announcement',
    })


@login_required
def toggle_announcement_active(request, announcement_id):
    if not can_manage_tasks(request.user):
        raise Http404('You do not have permission to update announcements.')

    announcement = get_object_or_404(OperationsAnnouncement, id=announcement_id)
    announcement.is_active = not announcement.is_active
    announcement.save()

    messages.success(request, 'Announcement visibility updated.')

    return redirect('announcement_detail', announcement_id=announcement.id)

@login_required
def create_task_from_request(request, request_id):
    if not can_manage_tasks(request.user):
        raise Http404('You do not have permission to create tasks.')

    service_request = get_object_or_404(
        ServiceRequest.objects.select_related(
            'assigned_to',
            'linked_folder',
            'submitted_by',
        ),
        id=request_id
    )

    initial_data = {
        'title': f'Handle Request: {service_request.title}',
        'description': f'''
Service Request: {service_request.title}

Request Description:
{service_request.description}

Client:
{service_request.linked_folder.client_name if service_request.linked_folder else "No linked client"}

Submitted By:
{service_request.submitted_by.username if service_request.submitted_by else "Unknown"}

Priority:
{service_request.get_priority_display()}

Status:
{service_request.get_status_display()}
''',

        'assigned_to': service_request.assigned_to,
        'linked_request': service_request,
        'linked_client': service_request.linked_folder,
        'priority': service_request.priority,
        'due_date': service_request.due_date,
    }

    if request.method == 'POST':
        form = InternalTaskForm(request.POST)

        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.linked_request = service_request

            if not task.linked_client and service_request.linked_folder:
                task.linked_client = service_request.linked_folder

            task.save()
            create_checklist_items_from_template(task)

            log_activity(
                'workflow_ran',
                f'Task created from request: {service_request.title}',
                f'{request.user.username} generated an internal task from a service request.'
            )

            if task.assigned_to:
                create_notification(
                    recipient=task.assigned_to,
                    title='New request task assigned',
                    message=f'A task was created from request: {service_request.title}',
                    notification_type='info',
                    link=f'/operations/{task.id}/'
                )

            messages.success(
                request,
                'Task successfully created from service request.'
            )

            return redirect('task_detail', task_id=task.id)

    else:
        form = InternalTaskForm(initial=initial_data)

    return render(request, 'operations/task_form.html', {
        'form': form,
        'title': 'Create Task From Request',
        'button_text': 'Create Request Task',
    })



@login_required
def task_template_list(request):
    if not can_manage_tasks(request.user):
        raise Http404('You do not have permission to view task templates.')

    templates = TaskTemplate.objects.all().order_by('-is_active', 'name')

    stats = {
        'total': templates.count(),
        'active': templates.filter(is_active=True).count(),
        'inactive': templates.filter(is_active=False).count(),
        'critical': templates.filter(default_priority='critical').count(),
    }

    return render(request, 'operations/task_template_list.html', {
        'templates': templates,
        'stats': stats,
    })


@login_required
def task_template_detail(request, template_id):
    if not can_manage_tasks(request.user):
        raise Http404('You do not have permission to view task templates.')

    template = get_object_or_404(TaskTemplate, id=template_id)
    tasks = template.tasks.select_related('assigned_to', 'linked_request', 'linked_client').all().order_by('-created_at')[:10]

    return render(request, 'operations/task_template_detail.html', {
        'template': template,
        'tasks': tasks,
    })


@login_required
def create_task_template(request):
    if not can_manage_tasks(request.user):
        raise Http404('You do not have permission to create task templates.')

    if request.method == 'POST':
        form = TaskTemplateForm(request.POST)

        if form.is_valid():
            template = form.save()

            log_activity(
                'workflow_ran',
                f'Task template created: {template.name}',
                f'{request.user.username} created a task template.'
            )

            messages.success(request, 'Task template created successfully.')

            return redirect('task_template_detail', template_id=template.id)

    else:
        form = TaskTemplateForm()

    return render(request, 'operations/task_template_form.html', {
        'form': form,
        'title': 'Create Task Template',
        'button_text': 'Create Template',
    })


@login_required
def edit_task_template(request, template_id):
    if not can_manage_tasks(request.user):
        raise Http404('You do not have permission to edit task templates.')

    template = get_object_or_404(TaskTemplate, id=template_id)

    if request.method == 'POST':
        form = TaskTemplateForm(request.POST, instance=template)

        if form.is_valid():
            template = form.save()

            log_activity(
                'workflow_ran',
                f'Task template updated: {template.name}',
                f'{request.user.username} updated a task template.'
            )

            messages.success(request, 'Task template updated successfully.')

            return redirect('task_template_detail', template_id=template.id)

    else:
        form = TaskTemplateForm(instance=template)

    return render(request, 'operations/task_template_form.html', {
        'form': form,
        'title': 'Edit Task Template',
        'button_text': 'Save Template',
    })


@login_required
def create_task_from_template(request, template_id):
    if not can_manage_tasks(request.user):
        raise Http404('You do not have permission to create tasks from templates.')

    template = get_object_or_404(TaskTemplate, id=template_id, is_active=True)

    due_date = timezone.now().date() + timezone.timedelta(days=template.default_due_days)

    initial_data = {
        'title': template.name,
        'description': template.description,
        'template': template,
        'priority': template.default_priority,
        'due_date': due_date,
        'status': 'todo',
    }

    if request.method == 'POST':
        form = InternalTaskForm(request.POST)

        if form.is_valid():
            task = form.save(commit=False)
            task.created_by = request.user
            task.template = template
            task.save()
            create_checklist_items_from_template(task)

            log_activity(
                'workflow_ran',
                f'Task created from template: {template.name}',
                f'{request.user.username} created a task from a template.'
            )

            if task.assigned_to:
                create_notification(
                    recipient=task.assigned_to,
                    title='New template task assigned',
                    message=f'You have been assigned: {task.title}',
                    notification_type='info',
                    link=f'/operations/{task.id}/'
                )

            messages.success(request, 'Task created from template successfully.')

            return redirect('task_detail', task_id=task.id)

    else:
        form = InternalTaskForm(initial=initial_data)

    return render(request, 'operations/task_form.html', {
        'form': form,
        'title': f'Create Task From Template: {template.name}',
        'button_text': 'Create Task',
    })



def create_checklist_items_from_template(task):
    if not task.template:
        return

    template_items = task.template.checklist_items.all().order_by('order', 'created_at')

    for item in template_items:
        InternalTaskChecklistItem.objects.create(
            task=task,
            title=item.title,
            order=item.order
        )


@login_required
def add_template_checklist_item(request, template_id):
    if not can_manage_tasks(request.user):
        raise Http404('You do not have permission to update task templates.')

    template = get_object_or_404(TaskTemplate, id=template_id)

    if request.method == 'POST':
        form = TaskTemplateChecklistItemForm(request.POST)

        if form.is_valid():
            item = form.save(commit=False)
            item.template = template
            item.save()

            messages.success(request, 'Template checklist item added.')

    return redirect('task_template_detail', template_id=template.id)


@login_required
def delete_template_checklist_item(request, item_id):
    if not can_manage_tasks(request.user):
        raise Http404('You do not have permission to update task templates.')

    item = get_object_or_404(TaskTemplateChecklistItem, id=item_id)
    template_id = item.template.id
    item.delete()

    messages.success(request, 'Template checklist item deleted.')

    return redirect('task_template_detail', template_id=template_id)


@login_required
def add_task_checklist_item(request, task_id):
    task = get_accessible_task_or_404(request.user, task_id)

    if request.method == 'POST':
        form = InternalTaskChecklistItemForm(request.POST)

        if form.is_valid():
            item = form.save(commit=False)
            item.task = task
            item.save()

            log_activity(
                'workflow_ran',
                f'Checklist item added: {task.title}',
                f'{request.user.username} added a checklist item.'
            )

            messages.success(request, 'Checklist item added.')

    return redirect('task_detail', task_id=task.id)


@login_required
def toggle_task_checklist_item(request, item_id):
    item = get_object_or_404(InternalTaskChecklistItem, id=item_id)
    task = get_accessible_task_or_404(request.user, item.task.id)

    item.is_completed = not item.is_completed

    if item.is_completed:
        item.completed_by = request.user
        item.completed_at = timezone.now()
    else:
        item.completed_by = None
        item.completed_at = None

    item.save()

    log_activity(
        'workflow_ran',
        f'Checklist updated: {task.title}',
        f'{request.user.username} updated a checklist item.'
    )

    messages.success(request, 'Checklist updated.')

    return redirect('task_detail', task_id=task.id)


@login_required
def delete_task_checklist_item(request, item_id):
    item = get_object_or_404(InternalTaskChecklistItem, id=item_id)
    task = get_accessible_task_or_404(request.user, item.task.id)

    item.delete()

    messages.success(request, 'Checklist item deleted.')

    return redirect('task_detail', task_id=task.id)



@login_required
def resolve_task(request, task_id):
    from django.contrib import messages
    from django.shortcuts import get_object_or_404
    from django.shortcuts import redirect
    from django.shortcuts import render
    from django.utils import timezone

    from .models import InternalTask
    from .task_resolution_forms import ResolveTaskForm

    task = get_object_or_404(InternalTask, id=task_id)

    if request.method == 'POST':
        form = ResolveTaskForm(request.POST, request.FILES)

        if form.is_valid():
            resolution = form.save(commit=False)
            resolution.task = task
            resolution.resolved_by = request.user
            resolution.save()

            task.status = 'completed'

            if hasattr(task, 'completed_at'):
                task.completed_at = timezone.now()

            task.save()

            messages.success(request, 'Task resolved successfully.')

            if getattr(task, 'linked_request', None):
                return redirect('request_detail', task.linked_request.id)

            return redirect('task_detail', task.id)

    else:
        form = ResolveTaskForm()

    return render(request, 'operations/resolve_task.html', {
        'task': task,
        'form': form,
    })
