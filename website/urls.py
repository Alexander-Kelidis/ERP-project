from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='website_index'),
    path('home/', views.home, name='home'),
    
    
]