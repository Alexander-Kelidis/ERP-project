# Create your models here.
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Notification(models.Model):
    sender = models.ForeignKey(User, related_name='sent_notifications', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_notifications', on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    

    def __str__(self):
        return f"Notification from {self.sender} to {self.receiver}: {self.message}"
