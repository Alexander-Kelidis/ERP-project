import json
from web3 import Web3 
from pathlib import Path
import os
from .models import Delivery, Order
from warehouse.models import Product
from members.models import CustomUser
from django.contrib.auth import get_user_model
from django.utils import timezone

# Step 1: Load environment variables from .env (optional)
from dotenv import load_dotenv
load_dotenv()

User = get_user_model()
# Step 2: Connect to the local Ganache blockchain
ganache_url = os.getenv('WEB3_PROVIDER', 'http://127.0.0.1:8545')  # Default to Ganache CLI port 8545
web3 = Web3(Web3.HTTPProvider(ganache_url))

# Check if the connection is successful
if not web3.is_connected():
    raise Exception("Could not connect to the Ethereum blockchain")

# Step 3: Load the ABI (from the Truffle build folder)
def load_contract(contract_name):
    with open(Path(__file__).resolve().parent / f"smart_contracts/build/contracts/{contract_name}.json") as f:
        contract_json = json.load(f)  # Load the contract JSON
        contract_abi = contract_json['abi']  # Get the ABI from the JSON file

        # Step 4: Get the deployed contract address (from the Truffle JSON file)
        contract_address = contract_json['networks']['5777']['address']  # Ensure the network ID matches Ganache
        return web3.eth.contract(address=contract_address, abi=contract_abi)

# Step 5: Create the contract instances for each contract
delivery_contract = load_contract("DeliveryContract")
retail_store_contract = load_contract("RetailstoreContract")
distributor_contract = load_contract("DistributorContract")
manufacturer_contract = load_contract("ManufacturerContract")

# Example function to interact with the contract
def initiate_delivery(order_id, product_id, quantity, retail_store_address):
    # Sender's account address (from Ganache)
    sender_address = web3.eth.accounts[1]

    print(f"Sender Address: {sender_address}")
    print(f"Retail Store Address: {retail_store_address}")
    
    
    # Ensure product_id is an integer
    product_id = int(product_id)
    
    # Ensure retail_store_address is a valid Ethereum address
    if not Web3.is_address(retail_store_address):
        raise ValueError("Invalid Ethereum address for the retail store.")

    # Send the transaction to the blockchain
    transaction = delivery_contract.functions.initiateDelivery(
        order_id,  # uint256
        product_id,  # uint256
        quantity,  # uint256
        retail_store_address  # address
    ).build_transaction({
        'from': sender_address,
        'nonce': web3.eth.get_transaction_count(sender_address),
        'gas': 2000000,
        'gasPrice': Web3.to_wei('50', 'gwei')
    })

    # Sign the transaction with the private key
    private_key = os.getenv("PRIVATE_KEY_DISTRIBUTOR")
    signed_txn = web3.eth.account.sign_transaction(transaction, private_key)

    # Send the signed transaction
    tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)

    # If the transaction is successful, update the Delivery model
    try:
        distributor_user = User.objects.get(eth_address=sender_address)  # Adjust this to your user model
        retail_store_user = User.objects.get(eth_address=retail_store_address)  # Adjust this to your user model
        
        delivery = Delivery.objects.create(
            order_id=order_id,
            delivery_status='in_transit',
            distributor=distributor_user,
            retail_store=retail_store_user
        )
        delivery.save()
    except User.DoesNotExist:
        raise Exception("Distributor or Retail store user not found in the database.")
    except Exception as e:
        raise Exception(f"Failed to create the delivery record in the database: {str(e)}")

    # Return the transaction hash
    return web3.to_hex(tx_hash)

    




def confirm_delivery(order_id, retail_store_user):
    # Retrieve the sender address associated with the retail store user
    sender_address = web3.eth.accounts[0] 

    try:
        # Check if the delivery exists and is in the 'in transit' state
        delivery = Delivery.objects.get(order__id=order_id)
        if delivery.delivery_status != 'in_transit':
            raise Exception("Delivery has not been initiated or is not in a confirmable state.")
        
        # Build the transaction manually
        transaction = delivery_contract.functions.confirmDelivery(
            order_id  # uint256
        ).build_transaction({
            'from': sender_address,
            'nonce': web3.eth.get_transaction_count(sender_address),
            'gas': 2000000,
            'gasPrice': Web3.to_wei('50', 'gwei')
        })

        # Get the private key from the environment
        private_key = os.getenv("PRIVATE_KEY_RETAIL_STORE")

        # Sign the transaction
        signed_txn = web3.eth.account.sign_transaction(transaction, private_key)

        # Send the signed transaction
        tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)

        # If the transaction is successful, update the Delivery model
        delivery.delivery_status = 'delivered'
        delivery.delivered_at = timezone.now()
        delivery.save()

        # Return the transaction hash as a hex string
        return web3.to_hex(tx_hash)

    except Delivery.DoesNotExist:
        # Raise an exception for a delivery that doesn't exist
        raise Exception("Delivery has not been initiated for this order.")
    except Exception as e:
        # Re-raise other exceptions
        raise Exception(f"An error occurred during delivery confirmation: {str(e)}")



def update_delivery_status(order_id, new_status):
    sender_address = web3.eth.accounts[1]  # The sender's address (retail store or admin)
    
    # Build the transaction object
    transaction = delivery_contract.functions.updateStatus(order_id, new_status).build_transaction({
        'from': sender_address,
        'nonce': web3.eth.get_transaction_count(sender_address),
        'gas': 2000000,
        'gasPrice': Web3.to_wei('50', 'gwei')
    })

    # Sign the transaction with the private key
    private_key = os.getenv("PRIVATE_KEY_DISTRIBUTOR")
    signed_txn = web3.eth.account.sign_transaction(transaction, private_key)

    # Send the signed transaction
    tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)

    # Update the database after successful transaction
    delivery = Delivery.objects.get(order__id=order_id)
    status_map = {0: 'in_transit', 1: 'delivered', 2: 'cancelled'}
    delivery.delivery_status = status_map.get(new_status, 'unknown')
    if new_status == 1:  # If status is 'delivered'
        delivery.delivered_at = timezone.now()
    delivery.save()

    # Convert HexBytes to a hex string before returning it
    return Web3.to_hex(tx_hash)


def get_delivery_details(order_id):
    delivery_details = delivery_contract.functions.getDeliveryDetails(
        order_id  # uint256
    ).call()
    return delivery_details  # Returns the details as a tuple (orderId, productId, quantity, retailStore, status)


def place_order(order_id, product_id, quantity, retail_store_user):
    sender_address = web3.eth.accounts[0]  # Assuming the retail store's account
    
    # Build the transaction
    transaction = retail_store_contract.functions.placeOrder(
        order_id,
        product_id,
        quantity
    ).build_transaction({
        'from': sender_address,
        'nonce': web3.eth.get_transaction_count(sender_address),
        'gas': 2000000,
        'gasPrice': Web3.to_wei('50', 'gwei')
    })

    # Sign the transaction with the private key
    private_key = os.getenv("PRIVATE_KEY_RETAIL_STORE")
    signed_txn = web3.eth.account.sign_transaction(transaction, private_key)

    # Send the signed transaction
    tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)

    # Update the order in the database only if the transaction is successful
    try:
        product = Product.objects.get(id=product_id)
        order = Order.objects.create(
            product=product,
            quantity=quantity,
            retail_store=retail_store_user,
            status='pending'
        )
        order.save()
    except Product.DoesNotExist:
        raise Exception(f"Product with ID {product_id} does not exist.")
    except Exception as e:
        raise Exception(f"Failed to create the order in the database: {str(e)}")

    # Convert HexBytes to a hex string before returning it
    return Web3.to_hex(tx_hash)



def process_order(order_id, product_id, quantity):
    # Sender's account address (assuming distributor's account)
    sender_address = web3.eth.accounts[1]  # Use the distributor's account in Ganache

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

    order = Order.objects.get(id=order_id)
    order.status = 'processed'
    order.save()

    # Return the transaction hash
    return Web3.to_hex(tx_hash)


def check_inventory(product_id, quantity):
    # Use the distributor's account and private key
    sender_address = web3.eth.accounts[1]  # Distributor's account in Ganache

    # Call checkInventory as a view function
    try:
        product = Product.objects.get(id=product_id)
        if product.quantity >= quantity:
            # Call blockchain function to double-check (if needed)
            is_available = distributor_contract.functions.checkInventory(
                product_id,
                quantity
            ).call({
                'from': sender_address  # Specify the sender address
            })
            return is_available
        else:
            return False  # Not enough quantity in stock
    except Product.DoesNotExist:
        raise Exception(f"Product with ID {product_id} does not exist.")
    except Exception as e:
        raise Exception(f"Failed to check inventory: {str(e)}")



def create_product(order_id, product_id, quantity):
    sender_address = web3.eth.accounts[2]  # Assuming the manufacturer's account
    
    # Ensure the parameters are integers
    order_id = int(order_id)
    product_id = int(product_id)
    quantity = int(quantity)

    transaction = manufacturer_contract.functions.createProduct(
        order_id,
        product_id,
        quantity
    ).build_transaction({
        'from': sender_address,
        'nonce': web3.eth.get_transaction_count(sender_address),
        'gas': 2000000,
        'gasPrice': Web3.to_wei('50', 'gwei')
    })

    private_key = os.getenv("PRIVATE_KEY_MANUFACTURER")
    signed_txn = web3.eth.account.sign_transaction(transaction, private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)

    return Web3.to_hex(tx_hash)



