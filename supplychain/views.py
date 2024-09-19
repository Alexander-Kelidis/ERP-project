from django.shortcuts import render
from .blockchain_service import initiate_delivery,confirm_delivery,update_delivery_status,get_delivery_details,place_order,process_order,check_inventory,create_product,update_inventory_on_blockchain
from hexbytes import HexBytes
from web3 import Web3 
from django.contrib import messages
from warehouse.models import Product
from .models import Delivery, Order
from django.utils import timezone
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.decorators import login_required
from django.db import models
from django.core.paginator import Paginator
from django.db.models import Max
import logging

logger = logging.getLogger('supplychain')

# Check if the user is a distributor
def is_distributor(user):
    return user.user_role == 'distributor'

# Check if the user is a retail store
def is_retail_store(user):
    return user.user_role == 'retail_store'

def is_manufacturer(user):
    return user.user_role == 'manufacturer'

def is_retail_store_or_distributor(user):
    return user.user_role in ['retail_store', 'distributor']

@login_required(login_url="/members/login_user")
@user_passes_test(is_distributor)
def initiate_delivery_view(request):
    if request.method == 'POST':
        order_id = request.POST.get('order_id')
        product_id = request.POST.get('product_id')
        quantity = request.POST.get('quantity')
        retail_store_address = request.POST.get('retail_store_address')

        try:
            # Validate the product ID exists in the warehouse
            product = Product.objects.get(product_id=product_id)
            # Convert form input values to correct types
            order_id = int(order_id)  # Convert order_id to integer
            product_id = int(product_id) # Convert product_id to integer
            quantity = int(quantity)  # Convert quantity to integer

             # Validate the retail_store_address as a proper Ethereum address
            if not Web3.is_address(retail_store_address):
                raise ValueError("Invalid Ethereum address for the retail store.")

            # Call the blockchain service function with the converted arguments
            tx_hash = initiate_delivery(order_id, product_id, quantity, retail_store_address)
            
           # Set a success message using Django's messaging framework
            messages.success(request, f"Transaction was successful! Transaction Hash: {tx_hash}")

        except Product.DoesNotExist:
            messages.warning(request, "Product does not exist.")
        except Exception as e:
            # Set an error message
            messages.warning(request, f"An error occurred: {str(e)}")

    return render(request, 'initiate_delivery.html')



@login_required(login_url="/members/login_user")
@user_passes_test(is_retail_store)
def confirm_delivery_view(request):
    if request.method == 'POST':
        order_id = int(request.POST.get('order_id'))

        try:
            # Call blockchain service to confirm delivery
            tx_hash = confirm_delivery(order_id, request.user)
            
            # Update the delivery status in the database
            delivery = Delivery.objects.get(order__id=order_id)
            delivery.delivery_status = 'delivered'
            delivery.delivered_at = timezone.now()
            delivery.save()

            messages.success(request, f"Delivery confirmed! Transaction Hash: {tx_hash}")
        except Delivery.DoesNotExist:
            messages.warning(request, "Delivery has not been initiated for this order.")
        except Exception as e:
            messages.warning(request, f"An error occurred: {str(e)}")

    return render(request, 'confirm_delivery.html')



@login_required(login_url="/members/login_user") 
@user_passes_test(is_distributor)
def update_delivery_status_view(request):
    if request.method == 'POST':
        try:
            # Retrieve the order_id and new_status from the form data
            order_id = int(request.POST.get('order_id'))
            new_status = int(request.POST.get('new_status'))  # new_status will be an integer (0, 1, or 2)

            # Validate the status values
            if new_status not in [0, 1, 2]:
                raise ValueError("Invalid status value.")
            
            # Fetch all deliveries with the given order_id
            deliveries = Delivery.objects.filter(order__id=order_id)

            if not deliveries.exists():
                messages.warning(request, "No delivery found for this order.")
            else:
                # Call the function to update the delivery status on the blockchain
                tx_hash = update_delivery_status(order_id, new_status)
                
                # Update the status of each delivery
                for delivery in deliveries:
                    status_map = {0: 'in_transit', 1: 'delivered', 2: 'cancelled'}
                    delivery.delivery_status = status_map.get(new_status, 'unknown')
                    if new_status == 1:  # If status is 'delivered'
                        delivery.delivered_at = timezone.now()
                    delivery.save()
                
                # Success message
                messages.success(request, f"Delivery status updated for {deliveries.count()} deliveries! Transaction Hash: {tx_hash}")

        except ValueError as ve:
            messages.warning(request, f"Invalid input: {ve}")
        except Exception as e:
            messages.warning(request, f"An error occurred: {str(e)}")
    
    return render(request, 'update_delivery_status.html')



@login_required(login_url="/members/login_user") 
@user_passes_test(is_retail_store_or_distributor)
def get_delivery_details_view(request):
    if request.method == 'POST':
        order_id = int(request.POST.get('order_id'))

        try:
            delivery_details = get_delivery_details(order_id)
            return render(request, 'delivery_details.html', {'details': delivery_details})
        except Exception as e:
            # Error message
            messages.warning(request, f"An error occurred: {str(e)}")

    # Return to the same page with messages
    return render(request, 'get_delivery_details.html')







@login_required(login_url="/members/login_user")
@user_passes_test(is_retail_store)
def place_order_view(request):
    # Determine the next order_id
    next_order_id = Order.objects.aggregate(max_id=Max('id'))['max_id']
    next_order_id = (next_order_id + 1) if next_order_id else 1  # Start from 1 if no orders exist

    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity'))

        try:
            logger.debug(f"Product ID from form: {product_id}")
            # Validate the product ID exists in the warehouse
            product = Product.objects.get(product_id=product_id)
            logger.debug(f"Fetched Product: ID={product_id}, Product ID={product.product_id}, Name={product.name}")

            # Call the blockchain service to place the order
            tx_hash = place_order(next_order_id, product.product_id, quantity, request.user)  # Pass request.user

            # Success message
            messages.success(request, f"Order placed successfully with Order ID {next_order_id}! Transaction Hash: {tx_hash}")

            # Directly fetch the next order ID again after the order is placed
            next_order_id = Order.objects.aggregate(max_id=Max('id'))['max_id'] + 1

        except Product.DoesNotExist:
            messages.warning(request, "Product does not exist.")
        except Exception as e:
            messages.warning(request, f"An error occurred: {str(e)}")

    # Fetch the user's orders
    user_orders = Order.objects.filter(retail_store=request.user)

    # Pagination: Create a Paginator object with 3 orders per page
    paginator = Paginator(user_orders, 3)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'place_order.html', {
        'user_orders': page_obj,
        'next_order_id': next_order_id
    })




@login_required(login_url="/members/login_user")
@user_passes_test(is_distributor)
def process_order_view(request):
    if request.method == 'POST':
        order_id = int(request.POST.get('order_id'))
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity'))

        try:
            # Log the Product ID received from the form
            logger.debug(f"[Process Order View] Product ID from form: {product_id}")

            # Validate the product ID exists in the warehouse
            product = Product.objects.get(product_id=product_id)

            # Log the Product ID from the database
            logger.debug(f"[Process Order View] Fetched Product from DB: ID={product.id}, Product ID={product.product_id}, Name={product.name}")

            # Call the blockchain service to process the order
            tx_hash = process_order(order_id, product.product_id, quantity)  # Use product.product_id here
            messages.success(request, f"Order processed successfully! Transaction Hash: {tx_hash}")

        except Product.DoesNotExist:
            messages.warning(request, "Product does not exist.")    
        except Exception as e:
            messages.warning(request, f"An error occurred: {str(e)}")

    return render(request, 'process_order.html')  # Return to the form page








@login_required(login_url="/members/login_user")
@user_passes_test(is_distributor)
def check_inventory_view(request):
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity'))  # Ensure `quantity` is an integer

        try:
            # Validate the product ID exists in the warehouse
            product = Product.objects.get(product_id=product_id)
            
            # Ensure product.quantity is converted to integer if it's not
            update_inventory_on_blockchain(product.id, int(product.quantity))

            # Call the blockchain service to check inventory
            is_available = check_inventory(product.id, quantity)
            if is_available:
                messages.success(request, "Product is available.")
            else:
                messages.warning(request, "Product is not available.")

        except Product.DoesNotExist:
            messages.warning(request, "Product does not exist.")
        except Exception as e:
            messages.warning(request, f"An error occurred: {str(e)}")

    return render(request, 'check_inventory.html')






@login_required(login_url="/members/login_user")
@user_passes_test(is_manufacturer)
def create_product_view(request):
    if request.method == 'POST':
        order_id = int(request.POST.get('order_id'))
        product_id = request.POST.get('product_id')
        quantity = int(request.POST.get('quantity'))

        try:
            
             # Convert product_id to integer
            product_id = int(product_id)
            # Call the blockchain service to create the product
            tx_hash = create_product(order_id, product_id, quantity)
            messages.success(request, f"Product created successfully! Transaction Hash: {tx_hash}")
            
        except Exception as e:
            messages.warning(request, f"An error occurred: {str(e)}")

    return render(request, 'create_product.html')  # Return to the form page


