from django.shortcuts import render,redirect
from .models import Customer
from django.contrib import messages
from django.core.paginator import Paginator


# Create your views here.


def add_customer(request): 
    context = {
       'values': request.POST
    }
    if request.method == 'GET':
            
      return render(request, 'customers/add_customers.html', context)

    if request.method == 'POST':
       customername = request.POST['customername']

       if not customername:
          messages.error(request, 'Name is required')
          return render(request, 'customers/add_customers.html', context)
    
       email = request.POST['email']

       if not email:
          messages.error(request, 'Email is required')
          return render(request, 'customers/add_customers.html', context)   
       
       date = request.POST['date']

       if not date:
          messages.error(request, 'Date is required')
          return render(request, 'customers/add_customers.html', context)
       

       phone = request.POST['phone']
    
       if not phone:
          messages.error(request, 'Phone is required')
          return render(request, 'customers/add_customers.html', context)
       
       address = request.POST['address']

       if not address:
           messages.error(request, 'Address is required')
           return render(request, 'customers/add_customers.html', context)
       

       city = request.POST['city']
       country = request.POST['country']
       postalcode = request.POST['postalcode']
       customertitle = request.POST['customertitle']
       companyname = request.POST['companyname']
       


       Customer.objects.create(customername=customername,email=email,phone=phone,address=address,date=date,city=city,country=country,postalcode=postalcode,customertitle=customertitle,companyname=companyname) 
       messages.success(request, 'Customer saves successfully')    

       return redirect('display_customer') 
    
def display_customer(request):
    customers = Customer.objects.all()
    paginator=Paginator(customers, 3)
    page_number=request.GET.get('page')
    page_obj=Paginator.get_page(paginator,page_number)

    context = {
       'customers': customers,
       'page_obj': page_obj
    }
    return render(request, 'customers/display_customers.html', context) 



def edit_customer(request, id):
   customer = Customer.objects.get(pk=id)
   customers = Customer.objects.all()
   context = {
      'customer': customer,
      'values': customer,
      'customers': customers
      
   }
   if request.method == 'GET':
       
      return render(request, 'customers/edit_customers.html', context)
   if request.method == 'POST':
       customername = request.POST['customername']

       if not customername:
          messages.error(request, 'Name is required')
          return render(request, 'customers/edit_customers.html', context)
    
       email = request.POST['email']

       if not email:
          messages.error(request, 'Email is required')
          return render(request, 'customers/edit_customers.html')   
       
       date = request.POST['date']

       if not date:
          messages.error(request, 'Date is required')
          return render(request, 'customers/edit_customers.html')
       

       phone = request.POST['phone']
    
       if not phone:
          messages.error(request, 'Phone is required')
          return render(request, 'customers/edit_customers.html')
       
       address = request.POST['address']

       if not address:
          messages.error(request, 'Address is required')
          return render(request, 'customers/edit_customers.html')
       
       
       city = request.POST['city']
       country = request.POST['country']
       postalcode = request.POST['postalcode']
       customertitle = request.POST['customertitle']
       companyname = request.POST['companyname']


     

       customer.customername=customername
       customer.email=email
       customer.phone=phone
       customer.date=date
       customer.address=address
       customer.city=city
       customer.country=country
       customer.postalcode=postalcode
       customer.customertitle=customertitle
       customer.companyname=companyname

       customer.save()

       messages.success(request, 'Customer Updated successfully')    

       return redirect('display_customer')   
   
def delete_customer(request, id):
      customer = Customer.objects.get(pk=id)
      customer.delete()
      messages.success(request, 'Customer removed')
      return redirect('display_customer')   