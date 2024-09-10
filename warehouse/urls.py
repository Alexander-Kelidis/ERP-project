from django.urls import path
from . import views


urlpatterns = [
     path('add_product/', views.add_product, name="add_product"),
     path('display_product/', views.display_product, name="display_product"),
     path('edit_product/<int:id>', views.edit_product, name="edit_product"),
     path('delete_product/<int:id>/', views.delete_product, name="delete_product"),
     
     

    
]  