from pathlib import Path
import shutil
from django.conf import settings


def clean_folder_name(value):
    return ''.join(char for char in value if char.isalnum() or char in (' ', '_', '-')).replace(' ', '_')


def create_client_folder_and_copy_document(document):
    client_folder_name = clean_folder_name(document.client_name)

    base_client_dir = Path(settings.BASE_DIR) / 'client_files' / 'clients'
    client_dir = base_client_dir / client_folder_name

    document_type_dir = client_dir / document.document_type
    document_type_dir.mkdir(parents=True, exist_ok=True)

    original_file = Path(document.file_path)

    if original_file.exists():
        copied_file = document_type_dir / original_file.name
        shutil.copy2(original_file, copied_file)
        return str(client_dir), str(copied_file)

    return str(client_dir), ''
