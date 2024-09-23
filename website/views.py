from django.shortcuts import render
from website.models import MyApp
from django.contrib.auth.decorators import login_required
from warehouse.models import Product
from crm.models import Customer
from notifications.models import Notification


@login_required(login_url="/members/login_user")
def index(request):
    
    products = Product.objects.filter(created_by=request.user)
    product_count = products.count()  # Get the total count of products created by the user
    customers = Customer.objects.filter(created_by=request.user)
    customer_count = customers.count()
    notifications = Notification.objects.filter(receiver=request.user)
    notification_count = notifications.count()

    my_apps = MyApp.objects.filter(created_by=request.user)
    context = {
        'my_apps': my_apps,
        'page' : request.path,
        'product_count': product_count,  # Pass product count to template
        'products': products,  # Optional: If you want to list the user's products
        'customer_count': customer_count,
        'customers': customers,
        'notification_count': notification_count,
        'notifications': notifications

    }
    return render(request, 'website/index.html', context)



@login_required(login_url="/members/login_user")
def home(request):
    products = Product.objects.filter(created_by=request.user)
    product_count = products.count()  # Get the total count of products created by the user
    customers = Customer.objects.filter(created_by=request.user)
    customer_count = customers.count()
    notifications = Notification.objects.filter(receiver=request.user)
    notification_count = notifications.count()
    my_apps = MyApp.objects.filter(created_by=request.user)
    context = {
        'my_apps': my_apps,
        'page' : request.path,
        'product_count': product_count,  # Pass product count to template
        'products': products,  # Optional: If you want to list the user's products
        'customer_count': customer_count,
        'customers': customers,
        'notification_count': notification_count,
        'notifications': notifications
    }
    return render(request, 'website/home.html', context)









