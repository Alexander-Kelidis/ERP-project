from django.shortcuts import render,redirect
from .models import Product,Unitofmesurment
from django.contrib import messages
from django.core.paginator import Paginator


# Create your views here.

def add_product(request): 
    unitofmesurments = Unitofmesurment.objects.all()
    context = {
       'values': request.POST,
       'unitofmesurments': unitofmesurments
    }
    if request.method == 'GET':
            
      return render(request, 'products/add_products.html', context)

    if request.method == 'POST':
       name = request.POST['name']

       if not name:
          messages.error(request, 'Name is required')
          return render(request, 'products/add_products.html', context)
    
       description = request.POST['description']

       if not description:
          messages.error(request, 'Description is required')
          return render(request, 'products/add_products.html', context)   
       
       date = request.POST['date']

       if not date:
          messages.error(request, 'Date is required')
          return render(request, 'products/add_products.html', context)
       

       quantity = request.POST['quantity']
    
       if not quantity:
          messages.error(request, 'Quantity is required')
          return render(request, 'products/add_products.html', context)
       
       
       unitofmesurment = request.POST['unitofmesurment']
       reorderpoint = request.POST['reorderpoint']
       price = request.POST['price']
       supplierinfo = request.POST['supplierinfo']
       category = request.POST['category']
       comments = request.POST['comments']


       

       Product.objects.create(name=name,description=description,unitofmesurment=unitofmesurment,quantity=quantity,date=date,reorderpoint=reorderpoint,price=price,supplierinfo=supplierinfo,category=category,comments=comments) 
       messages.success(request, 'Product saves successfully')    

       return redirect('display_product')  
    

def display_product(request):
    products = Product.objects.all()
    unitofmesurments = Unitofmesurment.objects.all()
    paginator=Paginator(products, 5)
    page_number=request.GET.get('page')
    page_obj=Paginator.get_page(paginator,page_number)

    context = {
       'products': products,
       'unitofmesurments': unitofmesurments,
       'page_obj': page_obj
    }
    return render(request, 'products/display_products.html', context)


def edit_product(request, id):
   product = Product.objects.get(pk=id)
   products = Product.objects.all()
   unitofmesurments = Unitofmesurment.objects.all()
   context = {
      'product': product,
      'values': product,
      'products': products,
      'unitofmesurments': unitofmesurments
   }
   if request.method == 'GET':
       
      return render(request, 'products/edit_products.html', context)
   if request.method == 'POST':
       name = request.POST['name']

       if not name:
          messages.error(request, 'Name is required')
          return render(request, 'products/edit_products.html')
    
       description = request.POST['description']

       if not description:
          messages.error(request, 'Description is required')
          return render(request, 'products/edit_products.html')   
       
       date = request.POST['date']

       if not date:
          messages.error(request, 'Date is required')
          return render(request, 'products/edit_products.html')
       

       quantity = request.POST['quantity']
    
       if not quantity:
          messages.error(request, 'Quantity is required')
          return render(request, 'products/edit_products.html')
       
       
       reorderpoint = request.POST['reorderpoint']
       price = request.POST['price']
       supplierinfo = request.POST['supplierinfo']
       category = request.POST['category']
       comments = request.POST['comments']


       product.name=name
       product.description=description
       product.quantity=quantity
       product.date=date
       product.reorderpoint=reorderpoint
       product.price=price
       product.supplierinfo=supplierinfo
       product.category=category
       product.comments=comments

       product.save()

       messages.success(request, 'Product Updated successfully')    

       return redirect('display_product')
   

def delete_product(request, id):
      product = Product.objects.get(pk=id)
      product.delete()
      messages.success(request, 'Product removed')
      return redirect('display_product')
      



        
           
       
       