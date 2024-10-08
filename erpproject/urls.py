from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('website.urls')),
    path('members/', include('django.contrib.auth.urls')),
    path('members/', include('members.urls')),
    path('products/', include('warehouse.urls')),
    path('customers/', include('crm.urls')),
    path('supplychain/', include('supplychain.urls')),
    path('notifications/', include('notifications.urls')),
    
    
] 

