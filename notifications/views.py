from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import redirect, render
from django.core.paginator import Paginator

from .models import Notification


@login_required
def notification_list(request):
    """Full page showing all notifications with pagination."""
    qs = request.user.notifications.all()
    paginator = Paginator(qs, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'notifications/notification_list.html', {
        'page_obj': page_obj,
        'unread_notification_count': qs.filter(is_read=False).count(),
    })


@login_required
def mark_notification_read(request, pk):
    """Mark a single notification as read and redirect to its link."""
    if request.method != 'POST':
        return redirect('notification_list')

    notification = request.user.notifications.filter(pk=pk).first()
    if notification:
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        if notification.link:
            return redirect(notification.link)

    return redirect('notification_list')


@login_required
def mark_all_read(request):
    """Mark all of the user's notifications as read."""
    if request.method != 'POST':
        return redirect('notification_list')

    request.user.notifications.filter(is_read=False).update(is_read=True)
    messages.success(request, 'All notifications marked as read.')
    return redirect('notification_list')
