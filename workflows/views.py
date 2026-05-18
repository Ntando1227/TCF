from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import render
from django.shortcuts import redirect

from accounts.permissions import can_run_workflows
from accounts.permissions import can_view_workflows

from .models import Workflow
from .models import WorkflowLog
from .automation_engine import run_daily_backup_workflow


@login_required
def workflow_list(request):
    if not can_view_workflows(request.user):
        raise Http404('You do not have permission to view workflows.')

    workflows = Workflow.objects.all().order_by('-created_at')

    return render(request, 'workflows/workflow_list.html', {
        'workflows': workflows,
        'can_run_workflow': can_run_workflows(request.user),
    })


@login_required
def workflow_logs(request):
    if not can_view_workflows(request.user):
        raise Http404('You do not have permission to view workflow logs.')

    logs = WorkflowLog.objects.all().order_by('-created_at')

    return render(request, 'workflows/workflow_logs.html', {
        'logs': logs,
        'can_run_workflow': can_run_workflows(request.user),
    })


@login_required
def run_backup_now(request):
    if not can_run_workflows(request.user):
        raise Http404('You do not have permission to run workflows.')

    success, output = run_daily_backup_workflow()

    if success:
        messages.success(request, 'Backup workflow completed successfully.')
    else:
        messages.error(request, f'Backup workflow failed: {output}')

    return redirect('workflow_logs')
