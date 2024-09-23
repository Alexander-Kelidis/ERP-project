// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import "./DeliveryContract.sol";
import "./ManufacturerContract.sol";

contract DistributorContract {
    address public manufacturer;
    address public deliveryContract;

    // Inventory structure to track product quantities
    struct InventoryItem {
        uint256 productId;
        uint256 quantity;
    }

    // Mapping to track the inventory for each product ID
    mapping(uint256 => InventoryItem) public inventory;

    //event OrderProcessed(uint256 orderId, uint256 productId, uint256 quantity, bool isAvailable);
    event ManufacturerContacted(uint256 orderId, uint256 productId, uint256 quantity);
    event InventoryUpdated(uint256 productId, uint256 newQuantity);  // New event for inventory updates
    event ManufacturerNotified(uint256 orderId, uint256 productId, uint256 quantity);

    constructor(address _manufacturer, address _deliveryContract) {
        manufacturer = _manufacturer;
        deliveryContract = _deliveryContract;
    }

    // Function to process an order
    /*function processOrder(uint256 orderId, uint256 productId, uint256 quantity) external {
        require(quantity > 0, "Quantity must be greater than zero");

        // Check inventory availability
        bool isAvailable = checkInventory(productId, quantity);
        if (isAvailable) {
            // Initiate delivery if the product is available
            DeliveryContract(deliveryContract).initiateDelivery(orderId, productId, quantity, msg.sender);
            
            // Update inventory after order processing
            inventory[productId].quantity -= quantity;
            emit InventoryUpdated(productId, inventory[productId].quantity);
            
            emit OrderProcessed(orderId, productId, quantity, true);
        } else {
            // Contact the manufacturer if the product is not available
            ManufacturerContract(manufacturer).createProduct(orderId, productId, quantity);
            emit ManufacturerContacted(orderId, productId, quantity);
        }
    }
   */ 

     function checkInventory(uint256 orderId, uint256 productId, uint256 quantity) public returns (bool) {
        // Ensure productId is valid and in stock
        if (inventory[productId].quantity >= quantity) {
            return true;
        } else {
            // Notify manufacturer if inventory is insufficient
            emit ManufacturerNotified(orderId, productId, quantity);
            return false;
        }
    }


    // Function to add or update inventory (For demonstration purposes)
    function updateInventory(uint256 productId, uint256 quantity) external {
        inventory[productId] = InventoryItem(productId, quantity);
        emit InventoryUpdated(productId, quantity);
    }

    
}
