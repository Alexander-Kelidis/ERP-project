from django.urls import path
from . import views


urlpatterns = [
     path('add_customer/', views.add_customer, name="add_customer"),
     path('display_customer/', views.display_customer, name="display_customer"),
     path('edit_customer/<int:id>', views.edit_customer, name="edit_customer"),
     path('delete_customer/<int:id>/', views.delete_customer, name="delete_customer"),
]  