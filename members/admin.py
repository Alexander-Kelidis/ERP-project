from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

# Register CustomUser with Django's UserAdmin interface
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'user_role', 'is_staff']

admin.site.register(CustomUser, CustomUserAdmin)