from django.db import models
from django.conf import settings

# Create your models here

class MyApp(models.Model):
    name = models.CharField(max_length=64, unique=True)
    description = models.TextField(default='', blank=True)
    image = models.ImageField(upload_to='my_apps')
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='my_apps') 




def __str__(self):

    return (f'MyApp{self.id} {self.name}')


class Meta:
    verbose_name_plural = 'my apps'
    ordering = ['name']
