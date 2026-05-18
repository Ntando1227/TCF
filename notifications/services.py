from django.contrib.auth import get_user_model

from .models import Notification


def map_notification_priority(notification_type=None, priority=None):
    if priority:
        return priority

    if notification_type in ['critical', 'danger', 'error']:
        return 'critical'

    if notification_type in ['warning', 'high']:
        return 'high'

    return 'medium'


def create_notification(
    recipient=None,
    user=None,
    title='Notification',
    message='',
    notification_type='info',
    priority=None,
    link=''
):
    final_user = user or recipient

    if not final_user:
        return None

    return Notification.objects.create(
        user=final_user,
        title=title,
        message=message,
        priority=map_notification_priority(
            notification_type=notification_type,
            priority=priority
        ),
        link=link
    )


def notify_admins(
    title='Notification',
    message='',
    notification_type='info',
    priority=None,
    link=''
):
    User = get_user_model()
    users = User.objects.filter(is_staff=True)

    created = []

    for user in users:
        notification = create_notification(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            link=link
        )

        if notification:
            created.append(notification)

    return created
