from pathlib import Path

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import FileResponse
from django.http import Http404
from django.shortcuts import render
from django.shortcuts import redirect
from django.shortcuts import get_object_or_404

from accounts.permissions import can_generate_documents
from accounts.permissions import can_delete_documents

from .models import GeneratedDocument
from .forms import GeneratedDocumentForm
from .pdf_generator import generate_business_pdf
from .folder_automation import create_client_folder_and_copy_document

from workflows.automation_engine import run_invoice_generated_workflow
from dashboard.activity import log_activity


@login_required
def document_list(request):
    search_query = request.GET.get('q', '').strip()
    document_type = request.GET.get('type', '').strip()
    sort_by = request.GET.get('sort', 'newest').strip()

    documents = GeneratedDocument.objects.all()

    if search_query:
        documents = documents.filter(
            Q(title__icontains=search_query) |
            Q(client_name__icontains=search_query) |
            Q(client_email__icontains=search_query)
        )

    if document_type:
        documents = documents.filter(document_type=document_type)

    if sort_by == 'oldest':
        documents = documents.order_by('created_at')
    elif sort_by == 'amount_high':
        documents = documents.order_by('-amount')
    elif sort_by == 'amount_low':
        documents = documents.order_by('amount')
    else:
        documents = documents.order_by('-created_at')

    return render(request, 'documents/document_list.html', {
        'documents': documents,
        'search_query': search_query,
        'document_type': document_type,
        'sort_by': sort_by,
        'document_types': GeneratedDocument.DOCUMENT_TYPES,
        'can_generate_document': can_generate_documents(request.user),
        'can_delete_document': can_delete_documents(request.user),
    })


@login_required
def generate_document(request):
    if not can_generate_documents(request.user):
        raise Http404('You do not have permission to generate documents.')

    if request.method == 'POST':
        form = GeneratedDocumentForm(request.POST)

        if form.is_valid():
            document = form.save()

            pdf_path, filename = generate_business_pdf(document)

            document.file_path = pdf_path
            document.file_name = filename

            client_folder_path, copied_file_path = create_client_folder_and_copy_document(document)
            document.client_folder_path = client_folder_path
            document.save()

            if document.document_type == 'invoice':
                run_invoice_generated_workflow(document)

            log_activity(
                'document_generated',
                f'Document generated: {document.title}',
                f'{document.get_document_type_display()} for {document.client_name}'
            )

            messages.success(request, 'Document generated successfully.')
            return redirect('document_list')

    else:
        form = GeneratedDocumentForm()

    return render(request, 'documents/document_form.html', {
        'form': form,
    })


@login_required
def download_document(request, document_id):
    document = get_object_or_404(GeneratedDocument, id=document_id)

    if not document.file_path:
        raise Http404('No file attached to this document.')

    file_path = Path(document.file_path)

    if not file_path.exists():
        raise Http404('The generated file could not be found.')

    return FileResponse(
        open(file_path, 'rb'),
        as_attachment=False,
        filename=document.file_name or file_path.name
    )


@login_required
def confirm_delete_document(request, document_id):
    if not can_delete_documents(request.user):
        raise Http404('You do not have permission to delete documents.')

    document = get_object_or_404(GeneratedDocument, id=document_id)

    return render(request, 'confirmations/confirm_action.html', {
        'title': 'Delete Document',
        'message': f'Are you sure you want to delete {document.title}?',
        'cancel_url': 'document_list',
        'action_url': 'delete_document',
        'object_id': document.id,
        'button_text': 'Delete Document',
        'danger': True,
    })


@login_required
def delete_document(request, document_id):
    if not can_delete_documents(request.user):
        raise Http404('You do not have permission to delete documents.')

    document = get_object_or_404(GeneratedDocument, id=document_id)

    title = document.title
    client_name = document.client_name

    if document.file_path:
        file_path = Path(document.file_path)

        if file_path.exists():
            file_path.unlink()

    document.delete()

    log_activity(
        'document_deleted',
        f'Document deleted: {title}',
        f'Deleted document for {client_name}'
    )

    messages.success(request, 'Document deleted successfully.')
    return redirect('document_list')
