from django.shortcuts import render  
from .blockchain_service import (  
    initiate_delivery, confirm_delivery, update_delivery_status, 
    get_delivery_details, place_order, check_inventory, create_product, 
    update_inventory_on_blockchain, check_order_exists
)
from hexbytes import HexBytes  
from web3 import Web3  
from django.contrib import messages  
from warehouse.models import Product  
from .models import Delivery, Order  
from django.utils import timezone  
from django.contrib.auth.decorators import user_passes_test, login_required 
from django.db import models  
from django.core.paginator import Paginator  
from django.db.models import Max  
import logging  

# Set up a logger for supply chain operations
logger = logging.getLogger('supplychain')


# Check if the user is a distributor by checking the `user_role`
def is_distributor(user):
    return user.user_role == 'distributor'

# Check if the user is a retail store by checking the `user_role`
def is_retail_store(user):
    return user.user_role == 'retail_store'

# Check if the user is a manufacturer by checking the `user_role`
def is_manufacturer(user):
    return user.user_role == 'manufacturer'

# Check if the user is either a retail store or distributor
def is_retail_store_or_distributor(user):
    return user.user_role in ['retail_store', 'distributor']





# View to initiate delivery, accessible only to distributors
@login_required(login_url="/members/login_user")  # Ensure user is logged in, redirect to login if not
@user_passes_test(is_distributor)  # Ensure user passes the distributor test
def initiate_delivery_view(request):
    if request.method == 'POST':  # Check if the form is submitted via POST method
        order_id = request.POST.get('order_id')  # Get order ID from the form
        product_id = request.POST.get('product_id')  # Get product ID from the form
        quantity = request.POST.get('quantity')  # Get quantity from the form
        retail_store_address = request.POST.get('retail_store_address')  # Get Ethereum address of the retail store

        try:
            # Ensure that the order exists in the database
            check_order_exists(order_id)

            # Fetch the product from the database
            product = Product.objects.get(product_id=product_id)
            order_id = int(order_id)  # Convert order_id to integer
            product_id = int(product_id)  # Convert product_id to integer
            quantity = int(quantity)  # Convert quantity to integer

            # Check if delivery has already been initiated for this order
            if Delivery.objects.filter(order_id=order_id).exists():
                messages.warning(request, "Delivery for this order has already been initiated.")
            else:
                # Call blockchain service to initiate delivery
                tx_hash = initiate_delivery(order_id, product_id, quantity, retail_store_address)
                # Display success message with the transaction hash
                messages.success(request, f"Transaction was successful! Transaction Hash: {tx_hash}")

        except Product.DoesNotExist:  # Handle case where the product doesn't exist
            messages.warning(request, "Product does not exist.")
        except Exception as e:  # Handle general exceptions
            messages.warning(request, f"An error occurred: {str(e)}")

    # Render the initiate delivery form
    return render(request, 'initiate_delivery.html')





# View to confirm delivery, accessible only to retail stores
@login_required(login_url="/members/login_user")  # Ensure user is logged in
@user_passes_test(is_retail_store)  # Ensure the user is a retail store
def confirm_delivery_view(request):
    if request.method == 'POST':  # Check if the form is submitted via POST method
        order_id = int(request.POST.get('order_id'))  # Get order ID from the form and convert it to an integer

        try:
            check_order_exists(order_id)  # Ensure that the order exists

            # Fetch the delivery from the database
            delivery = Delivery.objects.get(order__id=order_id)

            # Check if the delivery has already been confirmed
            if delivery.delivery_status == 'delivered':
                messages.warning(request, "This delivery has already been confirmed.")
                return render(request, 'confirm_delivery.html')

            # Call blockchain service to confirm delivery
            tx_hash = confirm_delivery(order_id, request.user)

            # Update the delivery status to 'delivered' and save the delivery time
            delivery.delivery_status = 'delivered'
            delivery.delivered_at = timezone.now()  # Record the delivery time
            delivery.save()  # Save the delivery record

            # Display success message with the transaction hash
            messages.success(request, f"Delivery confirmed! Transaction Hash: {tx_hash}")
        except Delivery.DoesNotExist:  # Handle case where delivery doesn't exist
            messages.warning(request, "Delivery has not been initiated for this order.")
        except Exception as e:  # Handle other exceptions
            messages.warning(request, f"An error occurred: {str(e)}")

    # Render the confirm delivery form
    return render(request, 'confirm_delivery.html')





# View to update the delivery status, accessible only to distributors
@login_required(login_url="/members/login_user")  # Ensure user is logged in
@user_passes_test(is_distributor)  # Ensure the user is a distributor
def update_delivery_status_view(request):
    if request.method == 'POST':  # Check if the form is submitted via POST method
        try:
            # Get order ID and new status from the form
            order_id = int(request.POST.get('order_id'))
            new_status = int(request.POST.get('new_status'))  # New status (0 = in transit, 1 = delivered, 2 = cancelled)

            # Validate if the new status is valid
            if new_status not in [0, 1, 2]:
                raise ValueError("Invalid status value.")

            # Fetch all deliveries with the given order_id
            deliveries = Delivery.objects.filter(order__id=order_id)
            check_order_exists(order_id)  # Ensure the order exists

            # Call blockchain service to update the status
            tx_hash = update_delivery_status(order_id, new_status)

            
            
            for delivery in deliveries:
                status_map = {0: 'in_transit', 1: 'delivered', 2: 'cancelled'} # Update the status of all deliveries in the database
                delivery.delivery_status = status_map.get(new_status, 'unknown')
                if new_status == 1:  # If status is 'delivered', record the delivery time
                    delivery.delivered_at = timezone.now()
                delivery.save()  # Save each delivery update

            # Display success message
            messages.success(request, f"Delivery status updated for {deliveries.count()} deliveries! Transaction Hash: {tx_hash}")

        except ValueError as ve:  # Handle validation errors
            messages.warning(request, f"Invalid input: {ve}")
        except Exception as e:  # Handle general exceptions
            messages.warning(request, f"An error occurred: {str(e)}")

    # Render the update delivery status form
    return render(request, 'update_delivery_status.html')






# View to get delivery details, accessible to retail stores and distributors
@login_required(login_url="/members/login_user")  # Ensure user is logged in
@user_passes_test(is_retail_store_or_distributor)  # Ensure the user is either a retail store or distributor
def get_delivery_details_view(request):
    if request.method == 'POST':  # Check if the form is submitted via POST method
        order_id = int(request.POST.get('order_id'))  # Get order ID from the form and convert it to an integer

        try:
            # Call blockchain service to get delivery details
            delivery_details = get_delivery_details(order_id)
            # Render the delivery details page with the retrieved details
            return render(request, 'delivery_details.html', {'details': delivery_details})
        except Exception as e:  # Handle exceptions
            messages.warning(request, f"An error occurred: {str(e)}")

    # Render the get delivery details form
    return render(request, 'get_delivery_details.html')






# View to place an order, accessible only to retail stores
@login_required(login_url="/members/login_user")  # Ensure user is logged in
@user_passes_test(is_retail_store)  # Ensure the user is a retail store
def place_order_view(request):
    # Determine the next order ID by finding the max existing order ID
    next_order_id = Order.objects.aggregate(max_id=Max('id'))['max_id']
    next_order_id = (next_order_id + 1) if next_order_id else 1  # Start from 1 if no orders exist

    if request.method == 'POST':  # Check if the form is submitted via POST method
        product_id = request.POST.get('product_id')  # Get product ID from the form
        quantity = int(request.POST.get('quantity'))  # Get quantity from the form and convert it to integer

        try:
            # Log the product ID received from the form
            logger.debug(f"Product ID from form: {product_id}")

            # Validate the product exists in the warehouse
            product = Product.objects.get(product_id=product_id)
            logger.debug(f"Fetched Product: ID={product_id}, Product ID={product.product_id}, Name={product.name}")

            # Call blockchain service to place the order
            tx_hash = place_order(next_order_id, product.product_id, quantity, request.user)

            # Display success message with the transaction hash and order ID
            messages.success(request, f"Order placed successfully with Order ID {next_order_id}! Transaction Hash: {tx_hash}")

            # Fetch the next order ID again after the order is placed
            next_order_id = Order.objects.aggregate(max_id=Max('id'))['max_id'] + 1

        except Product.DoesNotExist:  # Handle case where the product doesn't exist
            messages.warning(request, "Product does not exist.")
        except Exception as e:  # Handle general exceptions
            messages.warning(request, f"An error occurred: {str(e)}")

    # Fetch all orders placed by the logged-in user (retail store)
    user_orders = Order.objects.filter(retail_store=request.user)

    # Set up pagination (3 orders per page)
    paginator = Paginator(user_orders, 3)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Render the place order form with the paginated orders
    return render(request, 'place_order.html', {
        'user_orders': page_obj,  # Paginated user orders
        'next_order_id': next_order_id  # Next available order ID
    })






""""
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

"""






# View to check inventory, accessible only to distributors
@login_required(login_url="/members/login_user")  # Ensure user is logged in
@user_passes_test(is_distributor)  # Ensure the user is a distributor
def check_inventory_view(request):
    if request.method == 'POST':  # Check if the form is submitted via POST method
        order_id = int(request.POST.get('order_id'))  # Get order ID from the form
        product_id = int(request.POST.get('product_id'))  # Get product ID from the form
        quantity = int(request.POST.get('quantity'))  # Get quantity from the form

        try:
            check_order_exists(order_id)  # Ensure the order exists

            # Validate the product exists in the warehouse
            product = Product.objects.get(product_id=product_id)

            # Update the product inventory on the blockchain
            update_inventory_on_blockchain(int(product.product_id), int(product.quantity))

            # Call blockchain service to check inventory availability
            is_available = check_inventory(order_id, product.product_id, quantity)
            if is_available:
                messages.success(request, "Product is available.")
            else:
                messages.warning(request, "Product is not available. Manufacturer has been notified.")

        except Product.DoesNotExist:  # Handle case where the product doesn't exist
            messages.warning(request, "Product does not exist.")
        except Exception as e:  # Handle general exceptions
            messages.warning(request, f"An error occurred: {str(e)}")

    # Render the check inventory form
    return render(request, 'check_inventory.html')






# View to create a new product, accessible only to manufacturers
@login_required(login_url="/members/login_user")  # Ensure user is logged in
@user_passes_test(is_manufacturer)  # Ensure the user is a manufacturer
def create_product_view(request):
    if request.method == 'POST':  # Check if the form is submitted via POST method
        order_id = int(request.POST.get('order_id'))  # Get order ID from the form
        product_id = request.POST.get('product_id')  # Get product ID from the form
        quantity = int(request.POST.get('quantity'))  # Get quantity from the form and convert it to integer

        try:
            check_order_exists(order_id)  # Ensure the order exists

            product_id = int(product_id)  # Convert product ID to integer
            # Call blockchain service to create the product on the blockchain
            tx_hash = create_product(order_id, product_id, quantity)

            # Display success message with the transaction hash
            messages.success(request, f"Product created successfully! Transaction Hash: {tx_hash}")

        except Exception as e:  # Handle general exceptions
            messages.warning(request, f"An error occurred: {str(e)}")

    # Render the create product form
    return render(request, 'create_product.html')
