from pathlib import Path
import shutil

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse
from django.http import Http404
from django.shortcuts import render
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404
from django.utils import timezone

from accounts.permissions import can_manage_all_folders
from accounts.permissions import can_create_folders
from accounts.permissions import can_reassign_folders
from accounts.permissions import can_delete_folders
from accounts.permissions import can_upload_files
from accounts.permissions import can_move_files
from accounts.permissions import can_archive_files
from accounts.permissions import can_restore_files
from accounts.permissions import can_delete_files
from accounts.permissions import can_download_files

from notifications.services import create_notification
from notifications.services import notify_admins

from .models import ClientFolder
from .models import ClientFile

from .forms import ClientFolderForm
from .forms import StaffClientFolderForm
from .forms import ClientFileForm
from .forms import MoveClientFileForm
from .forms import ReassignClientFolderForm
from .forms import ClientFileCommentForm

from .folder_tools import create_client_folder_structure

from workflows.automation_engine import run_client_folder_created_workflow
from workflows.automation_engine import run_contract_uploaded_workflow
from workflows.automation_engine import run_report_uploaded_workflow
from dashboard.activity import log_activity


def get_visible_folders(user):
    if can_manage_all_folders(user):
        return ClientFolder.objects.all()

    return ClientFolder.objects.filter(owner=user)


def get_accessible_folder_or_404(user, folder_id):
    if can_manage_all_folders(user):
        return get_object_or_404(ClientFolder, id=folder_id)

    return get_object_or_404(ClientFolder, id=folder_id, owner=user)


def get_accessible_file_or_404(user, file_id):
    if can_manage_all_folders(user):
        return get_object_or_404(ClientFile, id=file_id)

    return get_object_or_404(
        ClientFile,
        id=file_id,
        client_folder__owner=user
    )


def get_file_preview_type(file_path):
    extension = Path(file_path).suffix.lower()

    if extension == '.pdf':
        return 'pdf'

    if extension in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
        return 'image'

    if extension in ['.txt', '.csv', '.log', '.md']:
        return 'text'

    return 'unsupported'


@login_required
def client_folder_list(request):
    search_query = request.GET.get('q', '').strip()

    folders = get_visible_folders(request.user).order_by('-created_at')

    if search_query:
        folders = folders.filter(client_name__icontains=search_query)

    return render(request, 'clients/client_folder_list.html', {
        'folders': folders,
        'search_query': search_query,
        'can_manage_all': can_manage_all_folders(request.user),
        'can_create_folder': can_create_folders(request.user),
        'can_reassign_folder': can_reassign_folders(request.user),
        'can_delete_folder': can_delete_folders(request.user),
    })


@login_required
def create_client_folder_view(request):
    if not can_create_folders(request.user):
        raise Http404('You do not have permission to create folders.')

    is_staff_user = can_manage_all_folders(request.user)

    if request.method == 'POST':
        if is_staff_user:
            form = StaffClientFolderForm(request.POST)
        else:
            form = ClientFolderForm(request.POST)

        if form.is_valid():
            folder = form.save(commit=False)

            if not is_staff_user:
                folder.owner = request.user

            folder.folder_path = create_client_folder_structure(folder.client_name)
            folder.save()

            run_client_folder_created_workflow(folder)

            owner_name = folder.owner.username if folder.owner else 'Unassigned'

            log_activity(
                'folder_created',
                f'Client folder created: {folder.client_name}',
                f'Owner: {owner_name}. Created by {request.user.username}.'
            )

            if folder.owner:
                create_notification(
                    recipient=folder.owner,
                    title='Client folder created',
                    message=f'{folder.client_name} has been assigned to you.',
                    notification_type='success',
                    link=f'/clients/{folder.id}/'
                )

            notify_admins(
                title='New client folder created',
                message=f'{folder.client_name} was created by {request.user.username}.',
                notification_type='info',
                link=f'/clients/{folder.id}/'
            )

            messages.success(request, 'Client folder created successfully.')

            return redirect('client_folder_detail', folder_id=folder.id)

    else:
        if is_staff_user:
            form = StaffClientFolderForm()
        else:
            form = ClientFolderForm()

    return render(request, 'clients/client_folder_form.html', {
        'form': form,
        'can_manage_all': is_staff_user,
    })


@login_required
def reassign_client_folder(request, folder_id):
    if not can_reassign_folders(request.user):
        raise Http404('You do not have permission to reassign folders.')

    folder = get_object_or_404(ClientFolder, id=folder_id)

    old_owner = folder.owner.username if folder.owner else 'Unassigned'

    if request.method == 'POST':
        form = ReassignClientFolderForm(request.POST, instance=folder)

        if form.is_valid():
            folder = form.save()
            new_owner = folder.owner.username if folder.owner else 'Unassigned'

            log_activity(
                'folder_created',
                f'Client folder reassigned: {folder.client_name}',
                f'Reassigned from {old_owner} to {new_owner} by {request.user.username}.'
            )

            if folder.owner:
                create_notification(
                    recipient=folder.owner,
                    title='Client folder assigned to you',
                    message=f'{folder.client_name} is now assigned to your account.',
                    notification_type='info',
                    link=f'/clients/{folder.id}/'
                )

            messages.success(request, 'Client folder reassigned successfully.')

            return redirect('client_folder_detail', folder_id=folder.id)

    else:
        form = ReassignClientFolderForm(instance=folder)

    return render(request, 'clients/reassign_client_folder.html', {
        'form': form,
        'folder': folder,
    })


@login_required
def client_folder_detail(request, folder_id):
    folder = get_accessible_folder_or_404(request.user, folder_id)

    search_query = request.GET.get('q', '').strip()
    folder_filter = request.GET.get('folder', '').strip()
    status_filter = request.GET.get('status', 'active').strip()

    all_files = folder.files.all().order_by('-uploaded_at')

    if search_query:
        all_files = all_files.filter(title__icontains=search_query)

    if folder_filter:
        all_files = all_files.filter(subfolder=folder_filter)

    if status_filter == 'archived':
        files = ClientFile.objects.none()
        archived_files = all_files.filter(is_archived=True)
    elif status_filter == 'all':
        files = all_files.filter(is_archived=False)
        archived_files = all_files.filter(is_archived=True)
    else:
        files = all_files.filter(is_archived=False)
        archived_files = ClientFile.objects.none()

    return render(request, 'clients/client_folder_detail.html', {
        'folder': folder,
        'files': files,
        'archived_files': archived_files,
        'search_query': search_query,
        'folder_filter': folder_filter,
        'status_filter': status_filter,
        'subfolder_choices': ClientFile.SUBFOLDER_CHOICES,
        'can_manage_all': can_manage_all_folders(request.user),
        'can_upload_file': can_upload_files(request.user),
        'can_move_file': can_move_files(request.user),
        'can_archive_file': can_archive_files(request.user),
        'can_restore_file': can_restore_files(request.user),
        'can_delete_file': can_delete_files(request.user),
        'can_download_file': can_download_files(request.user),
        'can_reassign_folder': can_reassign_folders(request.user),
    })


@login_required
def upload_client_file(request, folder_id):
    if not can_upload_files(request.user):
        raise Http404('You do not have permission to upload files.')

    folder = get_accessible_folder_or_404(request.user, folder_id)

    if request.method == 'POST':
        form = ClientFileForm(request.POST, request.FILES)

        if form.is_valid():
            client_file = form.save(commit=False)
            client_file.client_folder = folder
            client_file.save()

            base_folder = Path(folder.folder_path)
            subfolder_path = base_folder / client_file.subfolder
            subfolder_path.mkdir(parents=True, exist_ok=True)

            source_path = Path(client_file.uploaded_file.path)
            destination_path = subfolder_path / source_path.name

            shutil.copy2(source_path, destination_path)

            if client_file.subfolder == 'contracts':
                run_contract_uploaded_workflow(client_file, folder)

            if client_file.subfolder == 'reports':
                run_report_uploaded_workflow(client_file, folder)

            log_activity(
                'file_uploaded',
                f'File uploaded: {client_file.title}',
                f'Uploaded by {request.user.username} to {folder.client_name}.'
            )

            if folder.owner:
                create_notification(
                    recipient=folder.owner,
                    title='New file uploaded',
                    message=f'{client_file.title} was uploaded to {folder.client_name}.',
                    notification_type='success',
                    link=f'/clients/{folder.id}/'
                )

            notify_admins(
                title='File uploaded',
                message=f'{request.user.username} uploaded {client_file.title} to {folder.client_name}.',
                notification_type='info',
                link=f'/clients/{folder.id}/'
            )

            messages.success(request, 'File uploaded successfully.')

            return redirect('client_folder_detail', folder_id=folder.id)

    else:
        form = ClientFileForm()

    return render(request, 'clients/upload_client_file.html', {
        'folder': folder,
        'form': form,
    })


@login_required
def preview_client_file(request, file_id):
    if not can_download_files(request.user):
        raise Http404('You do not have permission to preview files.')

    client_file = get_accessible_file_or_404(request.user, file_id)

    file_path = Path(client_file.uploaded_file.path)

    if not file_path.exists():
        raise Http404('File not found.')

    if request.method == 'POST':
        comment_form = ClientFileCommentForm(request.POST)

        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.client_file = client_file
            comment.author = request.user
            comment.save()

            folder = client_file.client_folder

            log_activity(
                'file_uploaded',
                f'Comment added: {client_file.title}',
                f'{request.user.username} commented on {client_file.title}.'
            )

            if folder.owner and folder.owner != request.user:
                create_notification(
                    recipient=folder.owner,
                    title='New file comment',
                    message=f'{request.user.username} commented on {client_file.title}.',
                    notification_type='info',
                    link=f'/clients/preview/{client_file.id}/'
                )

            notify_admins(
                title='New file comment',
                message=f'{request.user.username} commented on {client_file.title}.',
                notification_type='info',
                link=f'/clients/preview/{client_file.id}/'
            )

            messages.success(request, 'Comment added successfully.')

            return redirect('preview_client_file', file_id=client_file.id)

    else:
        comment_form = ClientFileCommentForm()

    preview_type = get_file_preview_type(file_path)

    text_content = ''

    if preview_type == 'text':
        try:
            text_content = file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            text_content = file_path.read_text(encoding='latin-1')

    comments = client_file.comments.select_related('author').all().order_by('-created_at')

    return render(request, 'clients/preview_client_file.html', {
        'client_file': client_file,
        'folder': client_file.client_folder,
        'preview_type': preview_type,
        'text_content': text_content,
        'comments': comments,
        'comment_form': comment_form,
    })


@login_required
def stream_client_file(request, file_id):
    if not can_download_files(request.user):
        raise Http404('You do not have permission to view files.')

    client_file = get_accessible_file_or_404(request.user, file_id)

    file_path = Path(client_file.uploaded_file.path)

    if not file_path.exists():
        raise Http404('File not found.')

    return FileResponse(
        open(file_path, 'rb'),
        as_attachment=False
    )


@login_required
def move_client_file(request, file_id):
    if not can_move_files(request.user):
        raise Http404('You do not have permission to move files.')

    client_file = get_accessible_file_or_404(request.user, file_id)

    folder = client_file.client_folder
    old_subfolder = client_file.subfolder

    if request.method == 'POST':
        form = MoveClientFileForm(request.POST, instance=client_file)

        if form.is_valid():
            new_subfolder = form.cleaned_data['subfolder']

            base_folder = Path(folder.folder_path)

            old_file_path = base_folder / old_subfolder / Path(client_file.uploaded_file.path).name
            new_folder_path = base_folder / new_subfolder
            new_folder_path.mkdir(parents=True, exist_ok=True)
            new_file_path = new_folder_path / Path(client_file.uploaded_file.path).name

            if old_file_path.exists():
                shutil.move(str(old_file_path), str(new_file_path))

            client_file.subfolder = new_subfolder
            client_file.save()

            if new_subfolder == 'contracts':
                run_contract_uploaded_workflow(client_file, folder)

            if new_subfolder == 'reports':
                run_report_uploaded_workflow(client_file, folder)

            log_activity(
                'file_moved',
                f'File moved: {client_file.title}',
                f'Moved by {request.user.username} from {old_subfolder} to {new_subfolder}.'
            )

            if folder.owner:
                create_notification(
                    recipient=folder.owner,
                    title='File moved',
                    message=f'{client_file.title} was moved to {new_subfolder}.',
                    notification_type='info',
                    link=f'/clients/{folder.id}/'
                )

            messages.success(request, 'File moved successfully.')

            return redirect('client_folder_detail', folder_id=folder.id)

    else:
        form = MoveClientFileForm(instance=client_file)

    return render(request, 'clients/move_client_file.html', {
        'folder': folder,
        'client_file': client_file,
        'form': form,
    })


@login_required
def confirm_archive_client_file(request, file_id):
    if not can_archive_files(request.user):
        raise Http404('You do not have permission to archive files.')

    client_file = get_accessible_file_or_404(request.user, file_id)

    return render(request, 'confirmations/confirm_action.html', {
        'title': 'Archive File',
        'message': f'Are you sure you want to archive {client_file.title}?',
        'cancel_url': 'client_folder_detail',
        'cancel_id': client_file.client_folder.id,
        'action_url': 'archive_client_file',
        'object_id': client_file.id,
        'button_text': 'Archive File',
        'danger': True,
    })


@login_required
def archive_client_file(request, file_id):
    if not can_archive_files(request.user):
        raise Http404('You do not have permission to archive files.')

    client_file = get_accessible_file_or_404(request.user, file_id)
    folder = client_file.client_folder

    client_file.is_archived = True
    client_file.archived_at = timezone.now()
    client_file.save()

    base_folder = Path(folder.folder_path)
    current_file_path = base_folder / client_file.subfolder / Path(client_file.uploaded_file.path).name

    archive_folder = base_folder / 'archived'
    archive_folder.mkdir(parents=True, exist_ok=True)

    archive_file_path = archive_folder / Path(client_file.uploaded_file.path).name

    if current_file_path.exists():
        shutil.move(str(current_file_path), str(archive_file_path))

    log_activity(
        'file_archived',
        f'File archived: {client_file.title}',
        f'Archived by {request.user.username}.'
    )

    if folder.owner:
        create_notification(
            recipient=folder.owner,
            title='File archived',
            message=f'{client_file.title} was archived.',
            notification_type='warning',
            link=f'/clients/{folder.id}/'
        )

    messages.success(request, 'File archived successfully.')

    return redirect('client_folder_detail', folder_id=folder.id)


@login_required
def confirm_restore_client_file(request, file_id):
    if not can_restore_files(request.user):
        raise Http404('You do not have permission to restore files.')

    client_file = get_accessible_file_or_404(request.user, file_id)

    return render(request, 'confirmations/confirm_action.html', {
        'title': 'Restore File',
        'message': f'Are you sure you want to restore {client_file.title}?',
        'cancel_url': 'client_folder_detail',
        'cancel_id': client_file.client_folder.id,
        'action_url': 'restore_client_file',
        'object_id': client_file.id,
        'button_text': 'Restore File',
        'danger': False,
    })


@login_required
def restore_client_file(request, file_id):
    if not can_restore_files(request.user):
        raise Http404('You do not have permission to restore files.')

    client_file = get_accessible_file_or_404(request.user, file_id)
    folder = client_file.client_folder

    base_folder = Path(folder.folder_path)

    archive_file_path = base_folder / 'archived' / Path(client_file.uploaded_file.path).name

    restored_folder = base_folder / client_file.subfolder
    restored_folder.mkdir(parents=True, exist_ok=True)

    restored_file_path = restored_folder / Path(client_file.uploaded_file.path).name

    if archive_file_path.exists():
        shutil.move(str(archive_file_path), str(restored_file_path))

    client_file.is_archived = False
    client_file.archived_at = None
    client_file.save()

    log_activity(
        'file_restored',
        f'File restored: {client_file.title}',
        f'Restored by {request.user.username}.'
    )

    if folder.owner:
        create_notification(
            recipient=folder.owner,
            title='File restored',
            message=f'{client_file.title} was restored.',
            notification_type='success',
            link=f'/clients/{folder.id}/'
        )

    messages.success(request, 'File restored successfully.')

    return redirect('client_folder_detail', folder_id=folder.id)


@login_required
def confirm_delete_client_file(request, file_id):
    if not can_delete_files(request.user):
        raise Http404('You do not have permission to delete files.')

    client_file = get_accessible_file_or_404(request.user, file_id)

    return render(request, 'confirmations/confirm_action.html', {
        'title': 'Delete File',
        'message': f'Are you sure you want to permanently delete {client_file.title}?',
        'cancel_url': 'client_folder_detail',
        'cancel_id': client_file.client_folder.id,
        'action_url': 'delete_client_file',
        'object_id': client_file.id,
        'button_text': 'Delete File',
        'danger': True,
    })


@login_required
def delete_client_file(request, file_id):
    if not can_delete_files(request.user):
        raise Http404('You do not have permission to delete files.')

    client_file = get_accessible_file_or_404(request.user, file_id)
    folder = client_file.client_folder

    title = client_file.title

    if client_file.uploaded_file:
        uploaded_file_path = Path(client_file.uploaded_file.path)

        if uploaded_file_path.exists():
            uploaded_file_path.unlink()

    client_file.delete()

    log_activity(
        'file_deleted',
        f'File deleted: {title}',
        f'Deleted by {request.user.username} from {folder.client_name}.'
    )

    messages.success(request, 'File deleted successfully.')

    return redirect('client_folder_detail', folder_id=folder.id)


@login_required
def confirm_delete_client_folder(request, folder_id):
    if not can_delete_folders(request.user):
        raise Http404('You do not have permission to delete folders.')

    folder = get_accessible_folder_or_404(request.user, folder_id)

    return render(request, 'confirmations/confirm_action.html', {
        'title': 'Delete Client Folder',
        'message': f'Are you sure you want to permanently delete {folder.client_name} and its files?',
        'cancel_url': 'client_folder_list',
        'action_url': 'delete_client_folder',
        'object_id': folder.id,
        'button_text': 'Delete Folder',
        'danger': True,
    })


@login_required
def delete_client_folder(request, folder_id):
    if not can_delete_folders(request.user):
        raise Http404('You do not have permission to delete folders.')

    folder = get_accessible_folder_or_404(request.user, folder_id)

    folder_name = folder.client_name
    folder_path = Path(folder.folder_path)

    if folder_path.exists():
        shutil.rmtree(folder_path, ignore_errors=True)

    folder.delete()

    log_activity(
        'folder_deleted',
        f'Client folder deleted: {folder_name}',
        f'Deleted by {request.user.username}.'
    )

    messages.success(request, 'Client folder deleted successfully.')

    return redirect('client_folder_list')


@login_required
def download_client_file(request, file_id):
    if not can_download_files(request.user):
        raise Http404('You do not have permission to download files.')

    client_file = get_accessible_file_or_404(request.user, file_id)
    file_path = client_file.uploaded_file.path

    if not Path(file_path).exists():
        raise Http404('File not found.')

    return FileResponse(open(file_path, 'rb'), as_attachment=True)

@login_required
def approve_client_file(request, file_id):

    from accounts.permissions import can_approve_files

    if not can_approve_files(request.user):
        raise Http404('You do not have permission to approve files.')

    client_file = get_accessible_file_or_404(request.user, file_id)

    client_file.status = 'approved'
    client_file.approved_by = request.user
    client_file.approved_at = timezone.now()
    client_file.save()

    log_activity(
        'file_uploaded',
        f'File approved: {client_file.title}',
        f'Approved by {request.user.username}.'
    )

    folder = client_file.client_folder

    if folder.owner:
        create_notification(
            recipient=folder.owner,
            title='File Approved',
            message=f'{client_file.title} was approved.',
            notification_type='success',
            link=f'/clients/preview/{client_file.id}/'
        )

    messages.success(request, 'File approved successfully.')

    return redirect('preview_client_file', file_id=client_file.id)


@login_required
def reject_client_file(request, file_id):

    from accounts.permissions import can_approve_files

    if not can_approve_files(request.user):
        raise Http404('You do not have permission to reject files.')

    client_file = get_accessible_file_or_404(request.user, file_id)

    client_file.status = 'rejected'
    client_file.approved_by = request.user
    client_file.approved_at = timezone.now()
    client_file.save()

    log_activity(
        'file_uploaded',
        f'File rejected: {client_file.title}',
        f'Rejected by {request.user.username}.'
    )

    folder = client_file.client_folder

    if folder.owner:
        create_notification(
            recipient=folder.owner,
            title='File Rejected',
            message=f'{client_file.title} was rejected.',
            notification_type='warning',
            link=f'/clients/preview/{client_file.id}/'
        )

    messages.success(request, 'File rejected.')

    return redirect('preview_client_file', file_id=client_file.id)


@login_required
def request_changes_client_file(request, file_id):

    from accounts.permissions import can_approve_files

    if not can_approve_files(request.user):
        raise Http404('You do not have permission to request changes.')

    client_file = get_accessible_file_or_404(request.user, file_id)

    client_file.status = 'changes_requested'
    client_file.approved_by = request.user
    client_file.approved_at = timezone.now()
    client_file.save()

    log_activity(
        'file_uploaded',
        f'Changes requested: {client_file.title}',
        f'Changes requested by {request.user.username}.'
    )

    folder = client_file.client_folder

    if folder.owner:
        create_notification(
            recipient=folder.owner,
            title='Changes Requested',
            message=f'Changes were requested for {client_file.title}.',
            notification_type='info',
            link=f'/clients/preview/{client_file.id}/'
        )

    messages.success(request, 'Changes requested.')

    return redirect('preview_client_file', file_id=client_file.id)


@login_required
def approval_dashboard(request):
    from accounts.permissions import can_approve_files

    if not can_approve_files(request.user):
        raise Http404('You do not have permission to view approvals.')

    status_filter = request.GET.get('status', 'pending').strip()
    search_query = request.GET.get('q', '').strip()

    files = ClientFile.objects.select_related(
        'client_folder',
        'approved_by'
    ).all().order_by('-uploaded_at')

    if status_filter != 'all':
        files = files.filter(status=status_filter)

    if search_query:
        files = files.filter(title__icontains=search_query)

    stats = {
        'pending': ClientFile.objects.filter(status='pending').count(),
        'approved': ClientFile.objects.filter(status='approved').count(),
        'rejected': ClientFile.objects.filter(status='rejected').count(),
        'changes_requested': ClientFile.objects.filter(status='changes_requested').count(),
    }

    return render(request, 'clients/approval_dashboard.html', {
        'files': files,
        'stats': stats,
        'status_filter': status_filter,
        'search_query': search_query,
        'status_choices': ClientFile.STATUS_CHOICES,
    })

@login_required
def client_profile(request, folder_id):
    folder = get_accessible_folder_or_404(request.user, folder_id)

    files = folder.files.all().order_by('-uploaded_at')

    active_files = files.filter(is_archived=False)
    archived_files = files.filter(is_archived=True)

    service_requests = folder.service_requests.select_related(
        'submitted_by',
        'assigned_to',
        'reviewed_by',
    ).prefetch_related(
        'responses'
    ).all().order_by('-created_at')

    linked_documents = []

    for item in service_requests:
        if item.linked_document:
            linked_documents.append(item.linked_document)

    recent_comments = []

    for file in files:
        for comment in file.comments.select_related('author').all().order_by('-created_at')[:3]:
            recent_comments.append(comment)

    recent_comments = sorted(
        recent_comments,
        key=lambda item: item.created_at,
        reverse=True
    )[:8]

    stats = {
        'total_files': files.count(),
        'active_files': active_files.count(),
        'archived_files': archived_files.count(),
        'approved_files': files.filter(status='approved').count(),
        'pending_files': files.filter(status='pending').count(),
        'requests': service_requests.count(),
        'completed_requests': service_requests.filter(status='completed').count(),
        'pending_requests': service_requests.exclude(status='completed').count(),
        'documents': len(linked_documents),
    }

    return render(request, 'clients/client_profile.html', {
        'folder': folder,
        'files': files[:10],
        'active_files': active_files[:10],
        'archived_files': archived_files[:10],
        'service_requests': service_requests[:10],
        'linked_documents': linked_documents[:10],
        'recent_comments': recent_comments,
        'stats': stats,
        'can_manage_all': can_manage_all_folders(request.user),
        'can_upload_file': can_upload_files(request.user),
        'can_reassign_folder': can_reassign_folders(request.user),
    })

@login_required
def client_portal(request):
    from service_requests.models import ServiceRequest
    from service_requests.models import ServiceRequestResponse

    folders = ClientFolder.objects.filter(owner=request.user).order_by('-created_at')

    requests = ServiceRequest.objects.filter(
        submitted_by=request.user
    ).prefetch_related(
        'responses'
    ).order_by('-created_at')

    responses = ServiceRequestResponse.objects.filter(
        service_request__submitted_by=request.user
    ).select_related(
        'service_request',
        'responded_by',
        'last_downloaded_by',
        'confirmed_by',
    ).order_by('-responded_at')

    files = ClientFile.objects.filter(
        client_folder__owner=request.user
    ).select_related(
        'client_folder'
    ).order_by('-uploaded_at')

    stats = {
        'folders': folders.count(),
        'requests': requests.count(),
        'completed_requests': requests.filter(status='completed').count(),
        'open_requests': requests.exclude(status='completed').count(),
        'responses': responses.count(),
        'pending_confirmations': responses.filter(confirmation_status='pending').count(),
        'accepted_responses': responses.filter(confirmation_status='accepted').count(),
        'files': files.count(),
    }

    return render(request, 'clients/client_portal.html', {
        'folders': folders[:6],
        'requests': requests[:8],
        'responses': responses[:8],
        'files': files[:8],
        'stats': stats,
    })
