from .models import Notification

def notification_count(request):
    if request.user.is_authenticated:
        return {
            'unread_notifications_count': Notification.objects.filter(receiver=request.user, is_read=False).count(),
            'unread_notifications': Notification.objects.filter(receiver=request.user, is_read=False)
        }
    return {}
