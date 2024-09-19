from django.urls import path
from .views import mark_all_as_read, delete_notification

app_name = 'notifications'

urlpatterns = [
    path('mark_all_as_read/', mark_all_as_read, name='mark_all_as_read'),
    path('delete/<int:notification_id>/', delete_notification, name='delete_notification'),
]
