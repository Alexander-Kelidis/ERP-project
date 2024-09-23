import json
from web3 import Web3  
from pathlib import Path 
import os  
from .models import Delivery, Order  
from warehouse.models import Product  
from members.models import CustomUser  
from django.contrib.auth import get_user_model  
from django.utils import timezone  
import logging  

logger = logging.getLogger('blockchain_services')  # Set up a logger for logging blockchain services

# Step 1: Load environment variables from .env
from dotenv import load_dotenv  # Library to load environment variables from a .env file
load_dotenv()  # Load environment variables from the .env file

User = get_user_model()  # Get Django's user model (CustomUser or default user model)

# Step 2: Connect to the local Ganache blockchain
ganache_url = os.getenv('WEB3_PROVIDER', 'http://127.0.0.1:7545')  # Get the blockchain provider URL from the environment or use Ganache default
web3 = Web3(Web3.HTTPProvider(ganache_url))  # Create a Web3 instance using HTTP connection to the blockchain

# Check if the connection is successful
if not web3.is_connected():  # Verify the connection to the blockchain
    raise Exception("Could not connect to the Ethereum blockchain")  # Raise an exception if the connection fails


# Step 3: Load the ABI (from the Truffle build folder)
def load_contract(contract_name):
    """Load a contract's ABI and address by its name."""
    with open(Path(__file__).resolve().parent / f"smart_contracts/build/contracts/{contract_name}.json") as f:
        contract_json = json.load(f)  # Load the contract's JSON file
        contract_abi = contract_json['abi']  # Extract the ABI (Application Binary Interface) from the JSON

        # Step 4: Get the deployed contract address (from the Truffle JSON file)
        contract_address = contract_json['networks']['5777']['address']  # Use the address deployed on the network with ID 5777 (Ganache)
        return web3.eth.contract(address=contract_address, abi=contract_abi)  # Create a contract instance and return it


# Step 5: Create the contract instances for each contract
delivery_contract = load_contract("DeliveryContract")  # Load the Delivery contract
retail_store_contract = load_contract("RetailstoreContract")  # Load the Retail Store contract
distributor_contract = load_contract("DistributorContract")  # Load the Distributor contract
manufacturer_contract = load_contract("ManufacturerContract")  # Load the Manufacturer contract



# Function to check if an order exists in the database
def check_order_exists(order_id):
    """Check if the given order_id exists in the database. If not, raise an exception."""
    if not Order.objects.filter(id=order_id).exists():  # Query the Order model to check if the order exists
        raise ValueError(f"Order with ID {order_id} does not exist.")  # Raise an error if the order doesn't exist





# Function to interact with the DeliveryContract
def initiate_delivery(order_id, product_id, quantity, retail_store_address):
    """Initiate a delivery process by interacting with the blockchain and updating the database."""
    check_order_exists(order_id)  # Verify that the order exists

    # Sender's account address from Ganache
    sender_address = web3.eth.accounts[1]  # Use the second account in Ganache as the distributor's address

    print(f"Sender Address: {sender_address}")
    print(f"Retail Store Address: {retail_store_address}")

    # Ensure product_id is an integer
    product_id = int(product_id)  # Convert product ID to an integer
    
    # Ensure the retail_store_address is a valid Ethereum address
    if not Web3.is_address(retail_store_address):
        raise ValueError("Invalid Ethereum address for the retail store.")  # Raise an error if the address is invalid

    try:
        # Check if the delivery already exists in the database
        delivery = Delivery.objects.get(order_id=order_id)  # Fetch the delivery record by order_id
        
        # Check if the delivery has already been initiated or delivered
        if delivery.delivery_status == 'in_transit':
            raise Exception("This delivery has already been initiated.")  # Error if already initiated
        elif delivery.delivery_status == 'delivered':
            raise Exception("This delivery has already been delivered and cannot be initiated again.")  # Error if already delivered

    except Delivery.DoesNotExist:  # If the delivery does not exist, we skip the error
        pass

    # Send the transaction to the blockchain to initiate delivery
    transaction = delivery_contract.functions.initiateDelivery(
        order_id,  # uint256
        product_id,  # uint256
        quantity,  # uint256
        retail_store_address  # address
    ).build_transaction({
        'from': sender_address,  # The sender address is the distributor's Ethereum account
        'nonce': web3.eth.get_transaction_count(sender_address),  # Get the current nonce for the sender
        'gas': 2000000,  # Set the gas limit
        'gasPrice': Web3.to_wei('50', 'gwei')  # Set the gas price in gwei
    })

    # Sign the transaction with the distributor's private key
    private_key = os.getenv("PRIVATE_KEY_DISTRIBUTOR")  # Get the private key from environment variables
    signed_txn = web3.eth.account.sign_transaction(transaction, private_key)  # Sign the transaction

    # Send the signed transaction to the blockchain
    tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)  # Send the signed transaction

    # If the transaction is successful, update the Delivery model in the database
    try:
        distributor_user = User.objects.get(eth_address=sender_address)  # Get the distributor user from the database
        retail_store_user = User.objects.get(eth_address=retail_store_address)  # Get the retail store user from the database
        
        # Create or update the Delivery record in the database
        delivery, created = Delivery.objects.get_or_create(
            order_id=order_id,
            defaults={  # Default values for a new delivery
                'delivery_status': 'in_transit',
                'distributor': distributor_user,
                'retail_store': retail_store_user
            }
        )

        if not created:  # If the delivery already exists, update its status
            delivery.delivery_status = 'in_transit'
            delivery.save()  # Save changes to the database

    except User.DoesNotExist:  # Handle missing users in the database
        raise Exception("Distributor or Retail store user not found in the database.")
    except Exception as e:  # Catch other errors
        raise Exception(f"Failed to create the delivery record in the database: {str(e)}")

    # Return the transaction hash as a hexadecimal string
    return web3.to_hex(tx_hash)




# Function to confirm delivery on the blockchain
def confirm_delivery(order_id, retail_store_user):
    """Confirm delivery for a specific order and update the blockchain and database."""
    check_order_exists(order_id)  # Ensure the order exists

    sender_address = web3.eth.accounts[0]  # Use the first account in Ganache as the sender (retail store)

    try:
        # Fetch the delivery record from the database
        delivery = Delivery.objects.get(order__id=order_id)

        # Check if the delivery is already confirmed (delivered)
        if delivery.delivery_status == 'delivered':
            raise Exception("This delivery has already been confirmed.")  # Error if already confirmed

        # Ensure that the delivery is in transit
        if delivery.delivery_status != 'in_transit':
            raise Exception("Delivery must be in transit to be confirmed.")  # Error if not in transit

        # Build the transaction to confirm delivery on the blockchain
        transaction = delivery_contract.functions.confirmDelivery(
            order_id  # uint256
        ).build_transaction({
            'from': sender_address,  # The sender address is the retail store
            'nonce': web3.eth.get_transaction_count(sender_address),  # Get the current nonce
            'gas': 2000000,  # Set the gas limit
            'gasPrice': Web3.to_wei('50', 'gwei')  # Set the gas price
        })

        private_key = os.getenv("PRIVATE_KEY_RETAIL_STORE")  # Get the private key for the retail store from environment
        signed_txn = web3.eth.account.sign_transaction(transaction, private_key)  # Sign the transaction

        # Send the signed transaction to the blockchain
        tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)  # Send the transaction

        # Update the delivery status in the database upon success
        delivery.delivery_status = 'delivered'  # Set the delivery status to 'delivered'
        delivery.delivered_at = timezone.now()  # Record the delivery time
        delivery.save()  # Save changes to the database

        # Return the transaction hash as a hexadecimal string
        return Web3.to_hex(tx_hash)

    except Delivery.DoesNotExist:  # If the delivery does not exist
        raise Exception("Delivery has not been initiated for this order.")
    except Exception as e:  # Catch other errors
        raise Exception(f"An error occurred during delivery confirmation: {str(e)}")





# Function to update delivery status on the blockchain
def update_delivery_status(order_id, new_status):
    """Update the status of a delivery on the blockchain and in the database."""
    check_order_exists(order_id)  # Ensure the order exists

    sender_address = web3.eth.accounts[1]  # Use the second account in Ganache (distributor or admin)

    order_id = int(order_id)  # Convert the order ID to an integer

    # Build the transaction to update delivery status on the blockchain
    transaction = delivery_contract.functions.updateStatus(order_id, new_status).build_transaction({
        'from': sender_address,  # Sender's address
        'nonce': web3.eth.get_transaction_count(sender_address),  # Get the current nonce
        'gas': 2000000,  # Set gas limit
        'gasPrice': Web3.to_wei('50', 'gwei')  # Set gas price
    })

    # Sign the transaction with the distributor's private key
    private_key = os.getenv("PRIVATE_KEY_DISTRIBUTOR")  # Get the private key from environment
    signed_txn = web3.eth.account.sign_transaction(transaction, private_key)  # Sign the transaction

    # Send the signed transaction to the blockchain
    tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)  # Send the transaction

    # Update the database after the transaction is successful
    delivery = Delivery.objects.get(order__id=order_id)  # Fetch the delivery from the database
    status_map = {0: 'in_transit', 1: 'delivered', 2: 'cancelled'}  # Map status codes to human-readable status
    delivery.delivery_status = status_map.get(new_status, 'unknown')  # Update the delivery status

    if new_status == 1:  # If the new status is 'delivered'
        delivery.delivered_at = timezone.now()  # Record the delivery time
    delivery.save()  # Save changes to the database

    # Return the transaction hash as a hexadecimal string
    return Web3.to_hex(tx_hash)





# Function to get delivery details from the blockchain
def get_delivery_details(order_id):
    """Get delivery details from the blockchain."""
    delivery_details = delivery_contract.functions.getDeliveryDetails(
        order_id  # uint256
    ).call()  # Call the smart contract to get the delivery details
    return delivery_details  # Return the delivery details (tuple)





# Function to place an order on the blockchain and update the database
def place_order(order_id, product_id, quantity, retail_store_user):
    """Place an order on the blockchain and update the database."""
    sender_address = web3.eth.accounts[0]  # Use the first account in Ganache as the retail store's address

    # Ensure that order_id, product_id, and quantity are integers
    order_id = int(order_id)
    product_id = int(product_id)
    quantity = int(quantity)

    logging.info(f"Placing order with Product ID: {product_id}, Quantity: {quantity}, Order ID: {order_id}")  # Log the order placement

    # Build the transaction to place an order on the blockchain
    transaction = retail_store_contract.functions.placeOrder(
        order_id,  # uint256
        product_id,  # uint256
        quantity  # uint256
    ).build_transaction({
        'from': sender_address,  # Retail store's Ethereum address
        'nonce': web3.eth.get_transaction_count(sender_address),  # Get the current nonce
        'gas': 2000000,  # Set gas limit
        'gasPrice': Web3.to_wei('50', 'gwei')  # Set gas price
    })

    # Sign the transaction with the retail store's private key
    private_key = os.getenv("PRIVATE_KEY_RETAIL_STORE")  # Get the private key from environment
    signed_txn = web3.eth.account.sign_transaction(transaction, private_key)  # Sign the transaction

    # Send the signed transaction to the blockchain
    tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)  # Send the transaction

    # Update the order in the database after the transaction is successful
    try:
        product = Product.objects.get(product_id=product_id)  # Get the product from the database by its ID
        order = Order.objects.create(  # Create a new order in the database
            product=product,
            quantity=quantity,
            retail_store=retail_store_user,
            status='pending'
        )
        order.save()  # Save the order

    except Product.DoesNotExist:  # Handle case where the product does not exist
        raise Exception(f"Product with ID {product_id} does not exist.")
    except Exception as e:  # Catch any other exceptions
        raise Exception(f"Failed to create the order in the database: {str(e)}")

    # Return the transaction hash as a hexadecimal string
    return Web3.to_hex(tx_hash)




# Example of a commented-out function for processing orders, left in the code for reference
"""
def process_order(order_id, product_id, quantity):
    sender_address = web3.eth.accounts[1]  # Use the distributor's account in Ganache

    # Log the Product ID
    logger.debug(f"[Blockchain Service] Product ID for processing order: {product_id}")

    # Convert IDs to integers
    product_id = int(product_id)
    order_id = int(order_id)
    quantity = int(quantity)

    # Build the transaction to call the `processOrder` function in the DistributorContract
    transaction = distributor_contract.functions.processOrder(
        order_id,
        product_id,
        quantity
    ).build_transaction({
        'from': sender_address,
        'nonce': web3.eth.get_transaction_count(sender_address),
        'gas': 2000000,
        'gasPrice': Web3.to_wei('50', 'gwei')
    })

    # Sign the transaction with the distributor's private key
    private_key = os.getenv("PRIVATE_KEY_DISTRIBUTOR")
    signed_txn = web3.eth.account.sign_transaction(transaction, private_key)

    # Send the signed transaction
    tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)

    try:
        # Log Product ID again for verification
        logger.debug(f"[Blockchain Service] Verifying Product ID after sending to blockchain: {product_id}")

        product = Product.objects.get(product_id=product_id)
        order = Order.objects.get(id=order_id)
        order.status = 'processed'
        order.save()
    
    except Product.DoesNotExist:
        raise Exception(f"Product with ID {product_id} does not exist.")
    except Exception as e:
        raise Exception(f"Failed to create the order in the database: {str(e)}")

    # Return the transaction hash
    return Web3.to_hex(tx_hash)
"""




# Function to check inventory on the blockchain
def check_inventory(order_id, product_id, quantity):
    """Check inventory status on the blockchain for a given order and product."""
    check_order_exists(order_id)  # Ensure the order exists

    # Use the distributor's account in Ganache
    sender_address = web3.eth.accounts[1]  # Distributor's Ethereum address

    try:
        # Convert order_id, product_id, and quantity to integers
        order_id = int(order_id)
        product_id = product_id.strip()  # Strip any surrounding whitespace
        product_id = int(product_id)  # Convert product_id to integer
        quantity = int(quantity)  # Convert quantity to integer

        # Build the transaction to check inventory on the blockchain
        transaction = distributor_contract.functions.checkInventory(
            order_id,  # uint256: Order ID
            product_id,  # uint256: Product ID
            quantity  # uint256: Quantity
        ).build_transaction({
            'from': sender_address,  # Distributor's Ethereum address
            'nonce': web3.eth.get_transaction_count(sender_address),  # Get the current nonce
            'gas': 2000000,  # Set the gas limit
            'gasPrice': Web3.to_wei('50', 'gwei')  # Set gas price
        })

        # Sign the transaction with the distributor's private key
        private_key = os.getenv("PRIVATE_KEY_DISTRIBUTOR")  # Get private key from environment
        signed_txn = web3.eth.account.sign_transaction(transaction, private_key)  # Sign the transaction

        # Send the signed transaction
        tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)  # Send the transaction to the blockchain

        # Wait for the transaction receipt to get the return value
        tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)  # Wait for the transaction to be confirmed
        
        # Extract the logs to check if the inventory is available
        logs = distributor_contract.events.ManufacturerNotified().process_receipt(tx_receipt)  # Process the receipt logs
        
        if logs:  # If a ManufacturerNotified event was emitted
            return False  # Inventory is not available
        else:
            return True  # Inventory is available

    except ValueError:  # Handle conversion errors
        raise Exception(f"Invalid order ID, product ID, or quantity provided.")
    except Exception as e:  # Catch other exceptions
        raise Exception(f"Failed to check inventory on the blockchain: {str(e)}")





# Function to update inventory on the blockchain
def update_inventory_on_blockchain(product_id, quantity):
    """Update the inventory of a product on the blockchain."""
    sender_address = web3.eth.accounts[1]  # Distributor's Ethereum address

    # Convert product_id and quantity to integers
    product_id = Web3.to_int(product_id)  # Convert product ID to uint256
    quantity = Web3.to_int(quantity)  # Convert quantity to uint256

    # Build the transaction to update the inventory on the blockchain
    transaction = distributor_contract.functions.updateInventory(
        product_id,  # uint256: Product ID
        quantity  # uint256: Quantity
    ).build_transaction({
        'from': sender_address,  # Distributor's Ethereum address
        'nonce': web3.eth.get_transaction_count(sender_address),  # Get the current nonce
        'gas': 2000000,  # Set gas limit
        'gasPrice': Web3.to_wei('50', 'gwei')  # Set gas price
    })

    # Sign the transaction with the distributor's private key
    private_key = os.getenv("PRIVATE_KEY_DISTRIBUTOR")  # Get the private key from environment
    signed_txn = web3.eth.account.sign_transaction(transaction, private_key)  # Sign the transaction

    # Send the signed transaction to the blockchain
    tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)  # Send the transaction

    # Return the transaction hash as a hexadecimal string
    return Web3.to_hex(tx_hash)





# Function to create a product on the blockchain
def create_product(order_id, product_id, quantity):
    """Create a new product on the blockchain as part of an order."""
    check_order_exists(order_id)  # Ensure the order exists

    sender_address = web3.eth.accounts[2]  # Use the manufacturer's account (third account in Ganache)
    
    # Ensure the order_id, product_id, and quantity are integers
    order_id = int(order_id)
    product_id = int(product_id)
    quantity = int(quantity)

    # Build the transaction to create the product on the blockchain
    transaction = manufacturer_contract.functions.createProduct(
        order_id,  # uint256: Order ID
        product_id,  # uint256: Product ID
        quantity  # uint256: Quantity
    ).build_transaction({
        'from': sender_address,  # Manufacturer's Ethereum address
        'nonce': web3.eth.get_transaction_count(sender_address),  # Get the current nonce
        'gas': 2000000,  # Set gas limit
        'gasPrice': Web3.to_wei('50', 'gwei')  # Set gas price
    })

    # Sign the transaction with the manufacturer's private key
    private_key = os.getenv("PRIVATE_KEY_MANUFACTURER")  # Get the private key from environment
    signed_txn = web3.eth.account.sign_transaction(transaction, private_key)  # Sign the transaction

    # Send the signed transaction to the blockchain
    tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)  # Send the transaction

    # Return the transaction hash as a hexadecimal string
    return Web3.to_hex(tx_hash)
