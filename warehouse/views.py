from django.shortcuts import render,redirect, get_list_or_404
from .models import Product,Unitofmesurment
from django.contrib import messages
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required

# Create your views here.

@login_required(login_url="/members/login_user")
def add_product(request): 
    unitofmesurments = Unitofmesurment.objects.all()
    context = {
       'values': request.POST,
       'unitofmesurments': unitofmesurments
    }
    if request.method == 'GET':
            
      return render(request, 'products/add_products.html', context)

    if request.method == 'POST':
       product_id = request.POST.get('product_id')
       
       if not product_id:
          messages.warning(request, 'Product id is required')
          return render(request, 'products/add_products.html', context)

    
       name = request.POST['name']

       if not name:
          messages.warning(request, 'Name is required')
          return render(request, 'products/add_products.html', context)
    
       description = request.POST['description']

       if not description:
          messages.warning(request, 'Description is required')
          return render(request, 'products/add_products.html', context)   
       
       date = request.POST['date']

       if not date:
          messages.warning(request, 'Date is required')
          return render(request, 'products/add_products.html', context)
       

       quantity = request.POST['quantity']
    
       if not quantity:
          messages.warning(request, 'Quantity is required')
          return render(request, 'products/add_products.html', context)
       

       reorderpoint = request.POST['reorderpoint']

       if not reorderpoint:
          messages.warning(request, 'Reorder Point is required')
          return render(request, 'products/add_products.html', context)
       
       price = request.POST['price']

       if not price:
          messages.warning(request, 'Price is required')
          return render(request, 'products/add_products.html', context)


       unitofmesurment = request.POST['unitofmesurment']
       supplierinfo = request.POST['supplierinfo']
       comments = request.POST['comments']


       

       try:
            Product.objects.create(
                product_id=product_id,
                name=name,
                description=description,
                unitofmesurment=unitofmesurment,
                quantity=quantity,
                date=date,
                reorderpoint=reorderpoint,
                price=price,
                supplierinfo=supplierinfo,
                comments=comments,
                created_by=request.user
            )
            messages.success(request, 'Product saved successfully')
            return redirect('display_product')  
       except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return render(request, 'products/add_products.html', context)  
    
@login_required(login_url="/members/login_user")
def display_product(request):
    products = Product.objects.filter(created_by=request.user)
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

@login_required(login_url="/members/login_user")
def edit_product(request, id):
   product = Product.objects.get(pk=id, created_by=request.user)
   products = Product.objects.filter(created_by=request.user)
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
       
       product_id = request.POST['product_id']
       
       if not product_id:
          messages.warning(request, 'Product id is required')
          return render(request, 'products/edit_products.html')

       name = request.POST['name']

       if not name:
          messages.warning(request, 'Name is required')
          return render(request, 'products/edit_products.html')
    
       description = request.POST['description']

       if not description:
          messages.warning(request, 'Description is required')
          return render(request, 'products/edit_products.html')   
       
       date = request.POST['date']

       if not date:
          messages.warning(request, 'Date is required')
          return render(request, 'products/edit_products.html')
       

       quantity = request.POST['quantity']
    
       if not quantity:
          messages.warning(request, 'Quantity is required')
          return render(request, 'products/edit_products.html')
       
       
       reorderpoint = request.POST['reorderpoint']
       price = request.POST['price']
       supplierinfo = request.POST['supplierinfo']
       comments = request.POST['comments']

       product.product_id=product_id
       product.name=name
       product.description=description
       product.quantity=quantity
       product.date=date
       product.reorderpoint=reorderpoint
       product.price=price
       product.supplierinfo=supplierinfo
       product.comments=comments

       product.save()

       messages.success(request, 'Product Updated successfully')    

       return redirect('display_product')
   
@login_required(login_url="/members/login_user")
def delete_product(request, id):
      product = Product.objects.get(pk=id, created_by=request.user)
      product.delete()
      messages.success(request, 'Product removed')
      return redirect('display_product')
      



        
           
       
       