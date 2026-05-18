def get_user_role(user):
    if not user.is_authenticated:
        return 'anonymous'

    if user.is_superuser:
        return 'admin'

    return getattr(user, 'role', 'viewer')


def is_admin(user):
    return user.is_authenticated and (
        user.is_superuser or
        user.is_staff or
        get_user_role(user) == 'admin'
    )


def is_operations(user):
    return user.is_authenticated and get_user_role(user) == 'operations'


def is_finance(user):
    return user.is_authenticated and get_user_role(user) == 'finance'


def is_client(user):
    return user.is_authenticated and get_user_role(user) == 'client'


def is_viewer(user):
    return user.is_authenticated and get_user_role(user) == 'viewer'


def can_manage_all_folders(user):
    return is_admin(user) or is_operations(user) or is_finance(user)


def can_create_folders(user):
    return is_admin(user) or is_operations(user) or is_client(user)


def can_reassign_folders(user):
    return is_admin(user) or is_operations(user)


def can_delete_folders(user):
    return is_admin(user)


def can_upload_files(user):
    return is_admin(user) or is_operations(user) or is_finance(user) or is_client(user)


def can_move_files(user):
    return is_admin(user) or is_operations(user)


def can_archive_files(user):
    return is_admin(user) or is_operations(user)


def can_restore_files(user):
    return is_admin(user) or is_operations(user)


def can_delete_files(user):
    return is_admin(user)


def can_download_files(user):
    return user.is_authenticated


def can_generate_documents(user):
    return is_admin(user) or is_operations(user) or is_finance(user)


def can_delete_documents(user):
    return is_admin(user)


def can_view_exports(user):
    return is_admin(user) or is_operations(user) or is_finance(user)


def can_run_workflows(user):
    return is_admin(user) or is_operations(user)


def can_view_workflows(user):
    return is_admin(user) or is_operations(user) or is_finance(user)


def can_approve_files(user):
    return is_admin(user) or is_operations(user)
