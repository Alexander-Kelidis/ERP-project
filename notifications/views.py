from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Notification
from django.http import JsonResponse

@login_required
def mark_all_as_read(request):
    if request.method == 'POST':
        # Mark all unread notifications for the user as read
        unread_notifications = Notification.objects.filter(receiver=request.user, is_read=False)
        unread_notifications.update(is_read=True)  # Mark them as read

        return JsonResponse({'status': 'success'})
    return JsonResponse({'status': 'failed'})

@login_required
def delete_notification(request, notification_id):
    if request.method == 'POST':
        try:
            # Delete the notification
            notification = Notification.objects.get(id=notification_id, receiver=request.user)
            notification.delete()
            return JsonResponse({'status': 'success'})
        except Notification.DoesNotExist:
            return JsonResponse({'status': 'not_found'})
    return JsonResponse({'status': 'failed'})
