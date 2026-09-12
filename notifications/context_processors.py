def notifications_context(request):
    """Context processor that makes recent notifications and unread count available in every template."""
    if request.user.is_authenticated:
        qs = request.user.notifications.all()
        return {
            'nav_notifications': qs[:5],
            'unread_notification_count': qs.filter(is_read=False).count(),
        }
    return {}
