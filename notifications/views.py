from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render

from .models import Notification


@login_required
def notification_list(request):
    filter_type = request.GET.get('filter', 'all')

    notifications = Notification.objects.filter(user=request.user)

    if filter_type == 'unread':
        notifications = notifications.filter(is_read=False)

    if filter_type == 'critical':
        notifications = notifications.filter(priority='critical')

    if filter_type == 'high':
        notifications = notifications.filter(priority='high')

    notifications = notifications.order_by('-created_at')

    unread_count = Notification.objects.filter(
        user=request.user,
        is_read=False
    ).count()

    return render(request, 'notifications/notification_list.html', {
        'notifications': notifications,
        'unread_count': unread_count,
        'filter_type': filter_type,
    })


@login_required
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(
        Notification,
        id=notification_id,
        user=request.user
    )

    notification.is_read = True
    notification.save()

    if notification.link:
        return redirect(notification.link)

    return redirect('notification_list')


@login_required
def mark_all_notifications_read(request):
    Notification.objects.filter(
        user=request.user,
        is_read=False
    ).update(is_read=True)

    return redirect('notification_list')
