// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import "./DistributorContract.sol";
import "./DeliveryContract.sol";


// Contract for handling retail store operations in a supply chain.
contract RetailStoreContract {
    address public distributor;       // Address of the distributor
    address public deliveryContract;  // Address of the delivery contract
    

  
    event OrderPlaced(uint orderId, uint productId, uint quantity, address retailStore);     // Event emitted when an order is placed
    
    event DeliveryConfirmed(uint orderId);  // Event emitted when the delivery is confirmed

   
    // Constructor to initialize the manufacturer and delivery contract addresses
    constructor(address _distributor, address _deliveryContract) {
        distributor = _distributor;
        deliveryContract = _deliveryContract;
        
    }

    // Function to place an order
    function placeOrder(uint orderId, uint productId, uint quantity) external {
        require(quantity > 0, "Quantity must be greater than zero"); // Validate input quantity
        emit OrderPlaced(orderId, productId, quantity, msg.sender);    // Emit an event indicating the order was placed
        
        
    }

    // Function to confirm delivery
    function confirmDelivery(uint orderId) external{
        DeliveryContract(deliveryContract).confirmDelivery(orderId);    // Call the confirmDelivery function in the DeliveryContract to confirm the delivery
        emit DeliveryConfirmed(orderId);  // Emit an event indicating the delivery was confirmed.
    }
}