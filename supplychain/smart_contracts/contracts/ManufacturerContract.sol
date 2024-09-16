// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import "./DeliveryContract.sol";

// Contract for handling manufacturer operations in a supply chain.
contract ManufacturerContract {

    address public deliveryContract;   // Address of the delivery contract
    

    
    event ProductCreated(uint orderId, uint productId, uint quantity);   // Event emitted when a product is created
  
    event RawMaterialsRequested(uint productId, uint quantity);     // Event emitted when raw materials are requested

    event RawMaterialsSupplied(uint productId, uint quantity);    // Event emitted when raw materials are supplied


    // Constructor to initialize the supplier and delivery contract addresses
    constructor(address _deliveryContract) {
        deliveryContract = _deliveryContract;
        
    }

    // Function to create a product
    function createProduct(uint orderId, uint productId, uint quantity) external {
        require(quantity > 0, "Quantity must be greater than zero");   // Validate input quantity
        emit RawMaterialsRequested(productId, quantity);   // Emit an event indicating raw materials were requested.
        emit RawMaterialsSupplied(productId, quantity);    // Emit an event indicating raw materials were supplied.
        emit ProductCreated(orderId, productId, quantity);  // Emit an event indicating the product was created.

    }

}