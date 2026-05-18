from pathlib import Path
import subprocess

from django.conf import settings

from workflows.models import Workflow
from workflows.models import WorkflowLog


def get_workflow_script(script_name):
    return Path(settings.BASE_DIR) / 'powershell' / 'workflows' / script_name


def run_powershell_script(script_name, arguments):
    script_path = get_workflow_script(script_name)

    if not script_path.exists():
        return False, f'PowerShell script not found: {script_path}'

    command = [
        'powershell',
        '-ExecutionPolicy',
        'Bypass',
        '-File',
        str(script_path),
    ]

    for key, value in arguments.items():
        command.append(f'-{key}')
        command.append(str(value))

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        cwd=str(settings.BASE_DIR)
    )

    if result.returncode == 0:
        return True, result.stdout.strip() or 'PowerShell workflow completed successfully.'

    return False, result.stderr.strip() or 'PowerShell workflow failed.'


def get_or_create_workflow(name, trigger, description):
    workflow, created = Workflow.objects.get_or_create(
        name=name,
        defaults={
            'trigger': trigger,
            'description': description,
            'is_active': True,
        }
    )

    return workflow


def log_workflow(workflow, message):
    WorkflowLog.objects.create(
        workflow=workflow,
        message=message,
    )


def run_client_folder_created_workflow(folder):
    workflow = get_or_create_workflow(
        name='Client Folder Onboarding Automation',
        trigger='client_folder_created',
        description='Creates onboarding files and logs folder setup when a client folder is created.'
    )

    if not workflow.is_active:
        log_workflow(workflow, 'Skipped because workflow is inactive.')
        return

    success, output = run_powershell_script(
        'client_folder_created_workflow.ps1',
        {
            'ClientName': folder.client_name,
            'ClientFolderPath': folder.folder_path,
        }
    )

    if success:
        log_workflow(workflow, f'SUCCESS: {folder.client_name} | {output}')
    else:
        log_workflow(workflow, f'FAILED: {folder.client_name} | {output}')


def run_contract_uploaded_workflow(client_file, folder):
    workflow = get_or_create_workflow(
        name='Contract Intake Automation',
        trigger='contract_uploaded',
        description='Archives contract uploads and records workflow activity.'
    )

    if not workflow.is_active:
        log_workflow(workflow, 'Skipped because workflow is inactive.')
        return

    success, output = run_powershell_script(
        'contract_upload_workflow.ps1',
        {
            'ClientName': folder.client_name,
            'UploadedFilePath': client_file.uploaded_file.path,
        }
    )

    if success:
        log_workflow(workflow, f'SUCCESS: {folder.client_name} | {output}')
    else:
        log_workflow(workflow, f'FAILED: {folder.client_name} | {output}')


def run_report_uploaded_workflow(client_file, folder):
    workflow = get_or_create_workflow(
        name='Report Upload Automation',
        trigger='report_uploaded',
        description='Archives uploaded reports and creates a report summary file.'
    )

    if not workflow.is_active:
        log_workflow(workflow, 'Skipped because workflow is inactive.')
        return

    success, output = run_powershell_script(
        'report_uploaded_workflow.ps1',
        {
            'ClientName': folder.client_name,
            'ReportFilePath': client_file.uploaded_file.path,
        }
    )

    if success:
        log_workflow(workflow, f'SUCCESS: {folder.client_name} | {output}')
    else:
        log_workflow(workflow, f'FAILED: {folder.client_name} | {output}')


def run_invoice_generated_workflow(document):
    workflow = get_or_create_workflow(
        name='Invoice Generation Automation',
        trigger='invoice_generated',
        description='Updates invoice export ledger and archives invoice PDFs.'
    )

    if not workflow.is_active:
        log_workflow(workflow, 'Skipped because workflow is inactive.')
        return

    success, output = run_powershell_script(
        'invoice_generated_workflow.ps1',
        {
            'ClientName': document.client_name,
            'InvoiceTitle': document.title,
            'Amount': document.amount,
            'PdfPath': document.file_path,
        }
    )

    if success:
        log_workflow(workflow, f'SUCCESS: {document.client_name} | {output}')
    else:
        log_workflow(workflow, f'FAILED: {document.client_name} | {output}')


def run_daily_backup_workflow():
    workflow = get_or_create_workflow(
        name='Daily Backup Automation',
        trigger='manual_backup',
        description='Creates a timestamped backup of client files, generated documents, and exports.'
    )

    if not workflow.is_active:
        log_workflow(workflow, 'Skipped because workflow is inactive.')
        return False, 'Workflow inactive.'

    success, output = run_powershell_script(
        'daily_backup_workflow.ps1',
        {}
    )

    if success:
        log_workflow(workflow, f'SUCCESS: {output}')
    else:
        log_workflow(workflow, f'FAILED: {output}')

    return success, output
