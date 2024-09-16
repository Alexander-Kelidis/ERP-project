from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser
#from django.contrib.auth.models import User

class RegisterForm(UserCreationForm):

    class Meta(UserCreationForm):
        model = CustomUser
        fields = ["username", "password1", "password2", "user_role"]