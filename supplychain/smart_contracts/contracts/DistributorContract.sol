// SPDX-License-Identifier: MIT

pragma solidity ^0.8.17;

import "./DeliveryContract.sol";
import "./ManufacturerContract.sol";

// Contract for handling distributor operations in a supply chain.
contract DistributorContract{
    address public manufacturer;         // Address of the manufacturer
    address public deliveryContract;     // Address of the delivery contract         // Address of the distributor

    
    event OrderProcessed(uint orderId, uint productId, uint quantity, bool isAvailable);   // Event emitted when an order is processed
    
    event ManufacturerContacted(uint orderId, uint productId, uint quantity);   // Event emitted when the manufacturer is contacted

    

    // Constructor to initialize the manufacturer and delivery contract addresses
    constructor(address _manufacturer, address _deliveryContract) {
        manufacturer = _manufacturer;
        deliveryContract = _deliveryContract;
      
    }


    // Function to process an order
    function processOrder(uint orderId, uint productId, uint quantity) external {
        // Check inventory availability
        require(quantity > 0, "Quantity must be greater than zero"); // Validate input quantity
        bool isAvailable = checkInventory(productId, quantity);
        if (isAvailable) {
            // If available, initiate delivery through the delivery contract.
            DeliveryContract(deliveryContract).initiateDelivery(orderId, productId, quantity, msg.sender);
            emit OrderProcessed(orderId, productId, quantity, true);   // Emit an event indicating the order was processed and available.
        } else {
            // If not available, contact the manufacturer to create the product
            ManufacturerContract(manufacturer).createProduct(orderId, productId, quantity);
            emit ManufacturerContacted(orderId, productId, quantity);   // Emit an event indicating the manufacturer was contacted.
        }
    }


    // Internal function to check inventory
    function checkInventory(uint productId, uint quantity) public pure returns (bool) {
        // Implement inventory check logic here
        require(productId > 0, "Invalid productId");
        require(quantity > 0, "Quantity must be greater than zero");
        return true; // Placeholder for actual inventory check
    }
}