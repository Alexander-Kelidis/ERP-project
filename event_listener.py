# event_listener.py
import sys
import os
from pathlib import Path

# Set up the Django environment
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'erpproject.settings')

import django
django.setup()

import json
from web3 import Web3
from django.utils import timezone
import threading
import time
import logging

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Import models
from supplychain.models import Delivery, Order
from warehouse.models import Product
from notifications.models import Notification
from django.contrib.auth import get_user_model

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# Connect to the local Ganache blockchain
ganache_url = os.getenv('WEB3_PROVIDER', 'http://127.0.0.1:7545')
web3 = Web3(Web3.HTTPProvider(ganache_url))

if not web3.is_connected():
    raise Exception("Could not connect to the Ethereum blockchain")

def load_contract(contract_name):
    with open(Path(__file__).resolve().parent / f"supplychain/smart_contracts/build/contracts/{contract_name}.json") as f:
        contract_json = json.load(f)
        contract_abi = contract_json['abi']
        
        # Make sure this is the new address from the redeployed contract
        contract_address = contract_json['networks']['5777']['address']
        
        return web3.eth.contract(address=contract_address, abi=contract_abi)

# Load contracts
delivery_contract = load_contract("DeliveryContract")
retail_store_contract = load_contract("RetailStoreContract")
distributor_contract = load_contract("DistributorContract")
manufacturer_contract = load_contract("ManufacturerContract")

User = get_user_model()

# Helper function to get event topic hash
def get_event_topic_hash(event_signature):
    return "0x" + web3.keccak(text=event_signature).hex()

### Event Listener Functions ###
def listen_order_placed_event(stop_event):
    latest_block = web3.eth.block_number

    while not stop_event.is_set():
        try:
            event_filter = {
                'fromBlock': latest_block + 1,
                'toBlock': 'latest',
                'address': retail_store_contract.address,
                'topics': [get_event_topic_hash("OrderPlaced(uint256,uint256,uint256,address)")]
            }

            events = web3.eth.get_logs(event_filter)

            for event in events:
                processed_event = retail_store_contract.events.OrderPlaced().process_log(event)
                handle_order_placed_event(processed_event)

            latest_block = web3.eth.block_number

        except Exception as e:
            logging.error(f"An error occurred while listening for OrderPlaced events: {str(e)}")

        time.sleep(2)


def handle_order_placed_event(event):
    order_id = event['args']['orderId']
    product_id = event['args']['productId']
    quantity = event['args']['quantity']
    retail_store_address = event['args']['retailStore']

    logging.info(f"[Event Listener] Received OrderPlaced event with Product ID: {product_id}")

    try:
        # Ensure the product exists
        product = Product.objects.get(product_id=product_id)
        logging.info(f"[Event Listener] Found Product in DB with ID: {product_id}")
        retail_store_user = User.objects.get(eth_address__iexact=retail_store_address)

        # Get the distributor user
        distributor_user = User.objects.get(user_role='distributor')

        # Check if the order already exists
        order, created = Order.objects.get_or_create(
            id=order_id,
            defaults={
                'product': product,
                'quantity': quantity,
                'status': 'pending',
                'retail_store': retail_store_user
            }
        )

        # Create a notification regardless of whether the order was newly created
        notification_message = f"New order placed. Order ID: {order_id}, Product ID: {product_id}, Quantity: {quantity}. Click to delete it"
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


# In event_listener.py

def listen_order_processed_event(stop_event):
    latest_block = web3.eth.block_number

    while not stop_event.is_set():
        try:
            event_filter = {
                'fromBlock': latest_block + 1,
                'toBlock': 'latest',
                'address': distributor_contract.address,
                'topics': [get_event_topic_hash("OrderProcessed(uint256,uint256,uint256,bool)")]
            }

            # Get logs for the specified filter
            events = web3.eth.get_logs(event_filter)

            for event in events:
                processed_event = distributor_contract.events.OrderProcessed().process_log(event)
                handle_order_processed_event(processed_event)

            latest_block = web3.eth.block_number

        except Exception as e:
            logging.error(f"An error occurred while listening for OrderProcessed events: {str(e)}")

        time.sleep(2)

def handle_order_processed_event(event):
    order_id = event['args']['orderId']
    product_id = event['args']['productId']
    quantity = event['args']['quantity']
    is_available = event['args']['isAvailable']

    logging.info(f"OrderProcessed event received for Order ID: {order_id}, Product ID: {product_id}, Quantity: {quantity}, Availability: {is_available}")

    try:
        # Update the order in the database
        
        order = Order.objects.get(id=order_id)

        if is_available:
            order.status = 'processed'
            order.save()

            # Optionally, initiate delivery in the Django database if needed
            delivery, created = Delivery.objects.get_or_create(
                order=order,
                defaults={
                    'delivery_status': 'in_transit',
                    'retail_store': order.retail_store,
                    'distributor': User.objects.get(user_role='distributor')  # Adjust as necessary
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
                handle_delivery_initiated_event(processed_event)

            latest_block = web3.eth.block_number

        except Exception as e:
            logging.error(f"An error occurred while listening for DeliveryInitiated events: {str(e)}")

        time.sleep(2)


def handle_delivery_initiated_event(event):
    order_id = event['args']['orderId']
    product_id = event['args']['productId']
    quantity = event['args']['quantity']
    retail_store_address = event['args']['retailStore']

    logging.info(f"Received DeliveryInitiated event for Order ID: {order_id}")

    try:
        # Get the retail store user by Ethereum address
        retail_store_user = User.objects.get(eth_address__iexact=retail_store_address)

        # Get the distributor user (assuming there's only one distributor)
        distributor_user = User.objects.get(user_role='distributor')

        # Create a notification for the retail store
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






def listen_delivery_confirmed_event(stop_event):
    latest_block = web3.eth.block_number

    while not stop_event.is_set():
        try:
            event_filter = {
                'fromBlock': latest_block + 1,
                'toBlock': 'latest',
                'address': delivery_contract.address,  # Ensure this is the correct contract address
                'topics': [get_event_topic_hash("DeliveryConfirmed(uint256,address)")]
            }

            events = web3.eth.get_logs(event_filter)

            for event in events:
                processed_event = delivery_contract.events.DeliveryConfirmed().process_log(event)
                handle_delivery_confirmed_event(processed_event)

            latest_block = web3.eth.block_number

        except Exception as e:
            logging.error(f"An error occurred while listening for DeliveryConfirmed events: {str(e)}")

        time.sleep(2)


def handle_delivery_confirmed_event(event):
    order_id = event['args']['orderId']
    retail_store_address = event['args']['retailStore']

    try:
        # Get the retail store user (sender)
        retail_store_user = User.objects.get(eth_address__iexact=retail_store_address)
        # Get the distributor user (receiver)
        distributor_user = User.objects.get(user_role='distributor')

        # Create a notification for the distributor
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













def listen_manufacturer_contacted_event(stop_event):
    latest_block = web3.eth.block_number

    while not stop_event.is_set():
        try:
            event_filter = {
                'fromBlock': latest_block + 1,
                'toBlock': 'latest',
                'address': distributor_contract.address,  # Ensure the correct contract address
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


def handle_manufacturer_contacted_event(event):
    order_id = event['args']['orderId']
    product_id = event['args']['productId']
    quantity = event['args']['quantity']

    try:
        # Get the distributor user (sender)
        distributor_user = User.objects.get(user_role='distributor')
        # Get the manufacturer user (receiver)
        manufacturer_user = User.objects.get(user_role='manufacturer')

        # Create a notification for the manufacturer
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




# In event_listener.py

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

            # Get logs for the specified filter
            events = web3.eth.get_logs(event_filter)

            for event in events:
                processed_event = manufacturer_contract.events.ProductCreated().process_log(event)
                handle_product_created_event(processed_event)

            latest_block = web3.eth.block_number

        except Exception as e:
            logging.error(f"An error occurred while listening for ProductCreated events: {str(e)}")

        time.sleep(2)

def handle_product_created_event(event):
    order_id = event['args']['orderId']
    product_id = event['args']['productId']
    quantity = event['args']['quantity']

    logging.info(f"ProductCreated event received for Order ID: {order_id}, Product ID: {product_id}, Quantity: {quantity}")

    try:

        # Get the distributor user (sender)
        distributor_user = User.objects.get(user_role='distributor')
        # Get the manufacturer user (receiver)
        manufacturer_user = User.objects.get(user_role='manufacturer')
        # Update the product in the database
        product = Product.objects.get(product_id=product_id)
        product.quantity += quantity  # Increase the product's quantity
        product.save()

         # Create a notification for the manufacturer
        notification_message = f"Distributor contacted for Order ID: {order_id}, Product ID: {product_id}, Quantity: {quantity}, Product created with new quantity: {product.quantity} "
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








# Similar changes should be made to other event listeners to ensure proper state management.
# Ensure delivery and processing happen only if the order exists and is in the expected state.

# Run the event listeners in separate threads
if __name__ == "__main__":
    stop_event = threading.Event()
    try:
        listeners = [
            threading.Thread(target=listen_order_placed_event, args=(stop_event,)),
            threading.Thread(target=listen_delivery_initiated_event, args=(stop_event,)),
            threading.Thread(target=listen_product_created_event, args=(stop_event,)),
            threading.Thread(target=listen_manufacturer_contacted_event, args=(stop_event,)),
            threading.Thread(target=listen_delivery_confirmed_event, args=(stop_event,)),
            threading.Thread(target=listen_order_processed_event, args=(stop_event,)),

            # Add other listeners as needed
        ]
        
        for listener in listeners:
            listener.start()

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("Event listener stopped.")
        stop_event.set()

        for listener in listeners:
            listener.join()
