from .models import ActivityLog


def log_activity(action, title, description=''):
    ActivityLog.objects.create(
        action=action,
        title=title,
        description=description
    )
