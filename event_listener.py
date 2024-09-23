
import sys
import os
from pathlib import Path

# Set up the Django environment to work with models outside the Django app
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))  # Add the base directory to the system path for imports
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erpproject.settings')  # Set up Django settings to use models

import django
django.setup()  # Initialize Django, allowing use of models and the ORM

import json
from web3 import Web3  
from django.utils import timezone  
import threading  
import time  
import logging  

# Load environment variables from the .env file
from dotenv import load_dotenv
load_dotenv()

# Import models from the Django app
from supplychain.models import Delivery, Order 
from warehouse.models import Product 
from notifications.models import Notification  
from django.contrib.auth import get_user_model  # Utility to get the current user model

# Set up logging format and level
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# Connect to the local Ethereum blockchain (Ganache, in this case)
ganache_url = os.getenv('WEB3_PROVIDER', 'http://127.0.0.1:7545')  # Get the URL from the environment variables
web3 = Web3(Web3.HTTPProvider(ganache_url))  # Connect to Ethereum blockchain using HTTP provider


# Check if the connection to Ethereum is successful
if not web3.is_connected():
    raise Exception("Could not connect to the Ethereum blockchain")  # Raise an error if the connection fails



# Function to load a smart contract from the Truffle build folder
def load_contract(contract_name):
    with open(Path(__file__).resolve().parent / f"supplychain/smart_contracts/build/contracts/{contract_name}.json") as f:
        contract_json = json.load(f)  # Load contract's JSON (ABI and address)
        contract_abi = contract_json['abi']  # Extract ABI
        contract_address = contract_json['networks']['5777']['address']  # Extract contract address for the network (Ganache: network ID 5777)
        return web3.eth.contract(address=contract_address, abi=contract_abi)  # Return contract instance to interact with
    

# Load all the smart contracts needed
delivery_contract = load_contract("DeliveryContract")
retail_store_contract = load_contract("RetailStoreContract")
distributor_contract = load_contract("DistributorContract")
manufacturer_contract = load_contract("ManufacturerContract")


User = get_user_model()  # Get the custom user model used in the Django application


# Utility function to generate an event topic hash based on the event signature
def get_event_topic_hash(event_signature):
    return "0x" + web3.keccak(text=event_signature).hex()



### Event Listener Functions ###

# Function to listen for the 'OrderPlaced' event from the blockchain
def listen_order_placed_event(stop_event):
    latest_block = web3.eth.block_number  # Get the current block number

    # Continuously listen for new events until the stop_event is triggered
    while not stop_event.is_set():
        try:
            # Set up an event filter to listen for 'OrderPlaced' events from the retail store contract
            event_filter = {
                'fromBlock': latest_block + 1,
                'toBlock': 'latest',
                'address': retail_store_contract.address,
                'topics': [get_event_topic_hash("OrderPlaced(uint256,uint256,uint256,address)")]
            }

            # Fetch logs (events) that match the filter
            events = web3.eth.get_logs(event_filter)

            # Process each event found
            for event in events:
                processed_event = retail_store_contract.events.OrderPlaced().process_log(event)
                handle_order_placed_event(processed_event)  # Handle the 'OrderPlaced' event

            latest_block = web3.eth.block_number  # Update the latest block number

        except Exception as e:
            logging.error(f"An error occurred while listening for OrderPlaced events: {str(e)}")

        time.sleep(2)  # Sleep for 2 seconds between polling


# Handler for the 'OrderPlaced' event
def handle_order_placed_event(event):
    order_id = event['args']['orderId']  # Extract order ID from the event
    product_id = event['args']['productId']  # Extract product ID
    quantity = event['args']['quantity']  # Extract quantity
    retail_store_address = event['args']['retailStore']  # Extract the retail store's Ethereum address

    logging.info(f"[Event Listener] Received OrderPlaced event with Product ID: {product_id}")

    try:
        # Check if the product exists in the database
        product = Product.objects.get(product_id=product_id)
        retail_store_user = User.objects.get(eth_address__iexact=retail_store_address)  # Get the retail store user by Ethereum address
        distributor_user = User.objects.get(user_role='distributor')  # Get the distributor user

        # Check if the order already exists or create it
        order, created = Order.objects.get_or_create(
            id=order_id,
            defaults={
                'product': product,
                'quantity': quantity,
                'status': 'pending',
                'retail_store': retail_store_user
            }
        )

        # Create a notification for the distributor
        notification_message = f"New order placed. Order ID: {order_id}, Product ID: {product_id}, Quantity: {quantity}."
        Notification.objects.create(
            sender=retail_store_user,
            receiver=distributor_user,
            message=notification_message,
        )
        logging.debug(f"Notification created for Order ID {order_id}")

        if created:
            logging.info(f"Order ID {order_id} placed successfully.")
        else:
            logging.info(f"Order ID {order_id} already exists, skipping creation.")
            
    except Product.DoesNotExist:
        logging.warning(f"Product with ID {product_id} does not exist in the database.")
    except User.DoesNotExist:
        logging.warning(f"Retail store user with Ethereum address {retail_store_address} does not exist in the database.")
    except Exception as e:
        logging.error(f"An error occurred while handling OrderPlaced event: {str(e)}")





### Event Listener for 'OrderProcessed' Event ###
def listen_order_processed_event(stop_event):
    latest_block = web3.eth.block_number  # Get the latest block

    while not stop_event.is_set():
        try:
            event_filter = {
                'fromBlock': latest_block + 1,
                'toBlock': 'latest',
                'address': distributor_contract.address,
                'topics': [get_event_topic_hash("OrderProcessed(uint256,uint256,uint256,bool)")]
            }

            events = web3.eth.get_logs(event_filter)

            for event in events:
                processed_event = distributor_contract.events.OrderProcessed().process_log(event)
                handle_order_processed_event(processed_event)  # Process the 'OrderProcessed' event

            latest_block = web3.eth.block_number  # Update latest block number

        except Exception as e:
            logging.error(f"An error occurred while listening for OrderProcessed events: {str(e)}")

        time.sleep(2)


# Handler for 'OrderProcessed' event
def handle_order_processed_event(event):
    order_id = event['args']['orderId']
    product_id = event['args']['productId']
    quantity = event['args']['quantity']
    is_available = event['args']['isAvailable']  # Whether the product is available for processing

    logging.info(f"OrderProcessed event received for Order ID: {order_id}, Product ID: {product_id}, Quantity: {quantity}, Availability: {is_available}")

    try:
        # Fetch the order from the database
        order = Order.objects.get(id=order_id)

        # If available, mark the order as processed and create a delivery
        if is_available:
            order.status = 'processed'
            order.save()

            delivery, created = Delivery.objects.get_or_create(
                order=order,
                defaults={
                    'delivery_status': 'in_transit',
                    'retail_store': order.retail_store,
                    'distributor': User.objects.get(user_role='distributor')  # Get the distributor user
                }
            )

            logging.info(f"Order ID {order_id} processed successfully. Delivery {'created' if created else 'already exists'}.")

        else:
            order.status = 'awaiting_manufacture'
            order.save()
            logging.info(f"Order ID {order_id} marked as awaiting manufacture.")

    except Order.DoesNotExist:
        logging.warning(f"Order with ID {order_id} does not exist in the database.")
    except User.DoesNotExist:
        logging.warning("Distributor user does not exist in the database.")
    except Exception as e:
        logging.error(f"An error occurred while handling OrderProcessed event: {str(e)}")




### Listener for 'DeliveryInitiated' Event ###
def listen_delivery_initiated_event(stop_event):
    latest_block = web3.eth.block_number

    while not stop_event.is_set():
        try:
            event_filter = {
                'fromBlock': latest_block + 1,
                'toBlock': 'latest',
                'address': delivery_contract.address,
                'topics': [get_event_topic_hash("DeliveryInitiated(uint256,uint256,uint256,address)")]
            }

            events = web3.eth.get_logs(event_filter)

            for event in events:
                processed_event = delivery_contract.events.DeliveryInitiated().process_log(event)
                handle_delivery_initiated_event(processed_event)  # Process the 'DeliveryInitiated' event

            latest_block = web3.eth.block_number

        except Exception as e:
            logging.error(f"An error occurred while listening for DeliveryInitiated events: {str(e)}")

        time.sleep(2)


# Handler for 'DeliveryInitiated' event
def handle_delivery_initiated_event(event):
    order_id = event['args']['orderId']
    product_id = event['args']['productId']
    quantity = event['args']['quantity']
    retail_store_address = event['args']['retailStore']

    logging.info(f"Received DeliveryInitiated event for Order ID: {order_id}")

    try:
        # Get the retail store user by Ethereum address
        retail_store_user = User.objects.get(eth_address__iexact=retail_store_address)# Get the retail store user by Ethereum address 
        distributor_user = User.objects.get(user_role='distributor')  # Get the distributor user 

        # Fetch the product and update its quantity
        product = Product.objects.get(product_id=product_id)
        product.quantity -= quantity  # Decrease the product's stock by the delivered quantity
        product.save()

        # Notify the retail store about the initiated delivery
        notification_message = f"Delivery initiated for Order ID: {order_id}. Product ID: {product_id}, Quantity: {quantity}."
        Notification.objects.create(
            sender=distributor_user,
            receiver=retail_store_user,
            message=notification_message,
        )
        logging.info(f"Notification sent to retail store for Order ID {order_id}")

    except User.DoesNotExist as e:
        logging.error(f"User does not exist: {str(e)}")
    except Exception as e:
        logging.error(f"An error occurred while handling DeliveryInitiated event: {str(e)}")





### Listener and Handler for 'DeliveryConfirmed' Event ###
def listen_delivery_confirmed_event(stop_event):
    latest_block = web3.eth.block_number

    while not stop_event.is_set():
        try:
            event_filter = {
                'fromBlock': latest_block + 1,
                'toBlock': 'latest',
                'address': delivery_contract.address,
                'topics': [get_event_topic_hash("DeliveryConfirmed(uint256,address)")]
            }

            events = web3.eth.get_logs(event_filter)

            for event in events:
                processed_event = delivery_contract.events.DeliveryConfirmed().process_log(event)
                handle_delivery_confirmed_event(processed_event)  # Process the 'DeliveryConfirmed' event

            latest_block = web3.eth.block_number

        except Exception as e:
            logging.error(f"An error occurred while listening for DeliveryConfirmed events: {str(e)}")

        time.sleep(2)


# Handler for 'DeliveryConfirmed' event
def handle_delivery_confirmed_event(event):
    order_id = event['args']['orderId']
    retail_store_address = event['args']['retailStore']

    try:
        retail_store_user = User.objects.get(eth_address__iexact=retail_store_address)# Get the retail store user by Ethereum address
        distributor_user = User.objects.get(user_role='distributor')# Get distributor user 

        # Notify the distributor that the delivery has been confirmed
        notification_message = f"Delivery confirmed for Order ID: {order_id}"
        Notification.objects.create(
            sender=retail_store_user,
            receiver=distributor_user,
            message=notification_message,
        )
        logging.info(f"Notification created for DeliveryConfirmed event - Order ID {order_id}")
        
    except User.DoesNotExist as e:
        logging.warning(f"User does not exist: {str(e)}")
    except Exception as e:
        logging.error(f"An error occurred while handling DeliveryConfirmed event: {str(e)}")





### Listener and Handler for 'ManufacturerContacted' Event ###
def listen_manufacturer_contacted_event(stop_event):
    latest_block = web3.eth.block_number

    while not stop_event.is_set():
        try:
            event_filter = {
                'fromBlock': latest_block + 1,
                'toBlock': 'latest',
                'address': distributor_contract.address,
                'topics': [get_event_topic_hash("ManufacturerContacted(uint256,uint256,uint256)")]
            }

            events = web3.eth.get_logs(event_filter)

            for event in events:
                processed_event = distributor_contract.events.ManufacturerContacted().process_log(event)
                handle_manufacturer_contacted_event(processed_event)

            latest_block = web3.eth.block_number

        except Exception as e:
            logging.error(f"An error occurred while listening for ManufacturerContacted events: {str(e)}")

        time.sleep(2)


# Handler for 'ManufacturerContacted' event
def handle_manufacturer_contacted_event(event):
    order_id = event['args']['orderId']
    product_id = event['args']['productId']
    quantity = event['args']['quantity']

    try:
        distributor_user = User.objects.get(user_role='distributor')   # Get the distributor user
        manufacturer_user = User.objects.get(user_role='manufacturer') # Get the manufacturer user 

        # Notify the manufacturer about the contact for this order
        notification_message = f"Manufacturer contacted for Order ID: {order_id}, Product ID: {product_id}, Quantity: {quantity}"
        Notification.objects.create(
            sender=distributor_user,
            receiver=manufacturer_user,
            message=notification_message,
        )
        logging.info(f"Notification created for ManufacturerContacted event - Order ID {order_id}")
        
    except User.DoesNotExist as e:
        logging.warning(f"User does not exist: {str(e)}")
    except Exception as e:
        logging.error(f"An error occurred while handling ManufacturerContacted event: {str(e)}")





### Listener and Handler for 'ProductCreated' Event ###
def listen_product_created_event(stop_event):
    latest_block = web3.eth.block_number

    while not stop_event.is_set():
        try:
            event_filter = {
                'fromBlock': latest_block + 1,
                'toBlock': 'latest',
                'address': manufacturer_contract.address,
                'topics': [get_event_topic_hash("ProductCreated(uint256,uint256,uint256)")]
            }

            events = web3.eth.get_logs(event_filter)

            for event in events:
                processed_event = manufacturer_contract.events.ProductCreated().process_log(event)
                handle_product_created_event(processed_event)

            latest_block = web3.eth.block_number

        except Exception as e:
            logging.error(f"An error occurred while listening for ProductCreated events: {str(e)}")

        time.sleep(2)



# Handler for 'ProductCreated' event
def handle_product_created_event(event):
    order_id = event['args']['orderId']
    product_id = event['args']['productId']
    quantity = event['args']['quantity']

    logging.info(f"ProductCreated event received for Order ID: {order_id}, Product ID: {product_id}, Quantity: {quantity}")

    try:
        distributor_user = User.objects.get(user_role='distributor')  # Get the distributor user 
        manufacturer_user = User.objects.get(user_role='manufacturer')  # Get the manufacturer user

        # Update the product quantity in the database
        product = Product.objects.get(product_id=product_id)
        product.quantity += quantity  # Increase product quantity based on event
        product.save()

        # Notify the distributor that the product was created
        notification_message = f"Product created with new quantity for Order ID: {order_id}, Product ID: {product_id}"
        Notification.objects.create(
            sender=manufacturer_user,
            receiver=distributor_user,
            message=notification_message,
        )
        logging.info(f"Product ID {product_id} updated with new quantity: {product.quantity}")

    except Product.DoesNotExist:
        logging.warning(f"Product with ID {product_id} does not exist in the database.")
    except Exception as e:
        logging.error(f"An error occurred while handling ProductCreated event: {str(e)}")






### Listener and Handler for 'ManufacturerNotified' Event ###
def listen_manufacturer_notified_event(stop_event):
    latest_block = web3.eth.block_number

    while not stop_event.is_set():
        try:
            event_filter = {
                'fromBlock': latest_block + 1,
                'toBlock': 'latest',
                'address': distributor_contract.address,
                'topics': [get_event_topic_hash("ManufacturerNotified(uint256,uint256,uint256)")]
            }

            events = web3.eth.get_logs(event_filter)

            for event in events:
                processed_event = distributor_contract.events.ManufacturerNotified().process_log(event)
                handle_manufacturer_notified_event(processed_event)

            latest_block = web3.eth.block_number

        except Exception as e:
            logging.error(f"An error occurred while listening for ManufacturerNotified events: {str(e)}")

        time.sleep(2)


# Handler for 'ManufacturerNotified' event
def handle_manufacturer_notified_event(event):
    order_id = event['args']['orderId']
    product_id = event['args']['productId']
    quantity = event['args']['quantity']

    try:
        distributor_user = User.objects.get(user_role='distributor')  # Get the distributor user
        manufacturer_user = User.objects.get(user_role='manufacturer')  # Get the manufacturer user 

        # Notify the manufacturer that they were contacted for this order
        notification_message = f"Manufacturer notified for Order ID: {order_id}, Product ID: {product_id}, Quantity: {quantity}"
        Notification.objects.create(
            sender=distributor_user,
            receiver=manufacturer_user,
            message=notification_message,
        )
        logging.info(f"Notification created for ManufacturerNotified event - Order ID {order_id}, Product ID {product_id}")
        
    except User.DoesNotExist as e:
        logging.warning(f"User does not exist: {str(e)}")
    except Exception as e:
        logging.error(f"An error occurred while handling ManufacturerNotified event: {str(e)}")




### Running all Event Listeners in Parallel Threads ###
if __name__ == "__main__":
    stop_event = threading.Event()  # Event to stop all listeners when needed
    try:
        listeners = [
            threading.Thread(target=listen_order_placed_event, args=(stop_event,)),
            threading.Thread(target=listen_delivery_initiated_event, args=(stop_event,)),
            threading.Thread(target=listen_product_created_event, args=(stop_event,)),
            threading.Thread(target=listen_manufacturer_contacted_event, args=(stop_event,)),
            threading.Thread(target=listen_delivery_confirmed_event, args=(stop_event,)),
            threading.Thread(target=listen_order_processed_event, args=(stop_event,)),
            threading.Thread(target=listen_manufacturer_notified_event, args=(stop_event,)),
        ]
        
        for listener in listeners:
            listener.start()  # Start each event listener in a separate thread

        while True:
            time.sleep(1)  # Keep the main thread alive

    except KeyboardInterrupt:
        logging.info("Event listener stopped.")  # Log that listeners were stopped
        stop_event.set()  # Set the stop event to terminate all listeners

        for listener in listeners:
            listener.join()  # Wait for each thread to finish cleanly
