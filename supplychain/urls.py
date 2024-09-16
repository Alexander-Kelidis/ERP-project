# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('initiate-delivery/', views.initiate_delivery_view, name='initiate_delivery'),
    path('confirm-delivery/', views.confirm_delivery_view, name='confirm_delivery'),
    path('update-delivery-status/', views.update_delivery_status_view, name='update_delivery_status'),
    path('get-delivery-details/', views.get_delivery_details_view, name='get_delivery_details'),
    path('place-order/', views.place_order_view, name='place_order'),
    path('process-order/', views.process_order_view, name='process_order'),
    path('check-inventory/', views.check_inventory_view, name='check_inventory'),
    path('create-product/', views.create_product_view, name='create_product'),

    
    
]