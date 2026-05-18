from pathlib import Path
from django.conf import settings


def clean_folder_name(value):
    return ''.join(
        char for char in value
        if char.isalnum() or char in (' ', '_', '-')
    ).replace(' ', '_')


def create_client_folder_structure(client_name):
    clean_name = clean_folder_name(client_name)

    client_dir = Path(settings.BASE_DIR) / 'client_files' / 'clients' / clean_name

    subfolders = [
        'contracts',
        'invoices',
        'quotations',
        'proposals',
        'reports',
        'certificates',
        'general',
    ]

    client_dir.mkdir(parents=True, exist_ok=True)

    for subfolder in subfolders:
        (client_dir / subfolder).mkdir(parents=True, exist_ok=True)

    return str(client_dir)


def get_folder_files(folder_path):
    base_path = Path(folder_path)

    if not base_path.exists():
        return []

    files = []

    for item in base_path.rglob('*'):
        if item.is_file():
            files.append({
                'name': item.name,
                'subfolder': item.parent.name,
                'path': str(item),
                'size_kb': round(item.stat().st_size / 1024, 2),
            })

    return files
