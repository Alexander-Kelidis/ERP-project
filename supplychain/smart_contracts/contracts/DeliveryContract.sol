// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;


contract DeliveryContract {     // Contract for handling delivery operations in a supply chain.
    
    enum DeliveryStatus { InTransit, Delivered, Cancelled }

    struct Delivery {
        uint orderId;    // Unique identifier for the order
        uint productId;   // Unique identifier for the product
        uint quantity;    // Quantity of the product in the delivery
        address retailStore;  // Address of the retail store to which delivery is made
        DeliveryStatus status;   // Current status of the delivery (e.g., "In Transit", "Delivered")
    }

    struct InventoryItem {
    uint256 productId;
    uint256 quantity;
}


    mapping(uint => Delivery) public deliveries; // Mapping to store deliveries by orderId
    mapping(uint256 => InventoryItem) public inventory; // Add inventory mapping here if needed

   
    
    event DeliveryInitiated(uint orderId, uint productId, uint quantity, address retailStore);   // Event emitted when a delivery is initiated
    
    event DeliveryConfirmed(uint orderId, address retailStore);  // Event emitted when a delivery is confirmed by retail store
    
    event StatusUpdated(uint orderId, DeliveryStatus status);   // Event emitted when the status of a delivery is updated

   



    function initiateDelivery(uint orderId, uint productId, uint quantity, address retailStore) external {
    require(quantity > 0, "Quantity must be greater than 0");

    Delivery storage delivery = deliveries[orderId];
    require(delivery.status == DeliveryStatus.Cancelled || delivery.status == DeliveryStatus(0), "Delivery has already been initiated or delivered");

    // Create a new delivery entry with status "In Transit"
    deliveries[orderId] = Delivery(orderId, productId, quantity, retailStore, DeliveryStatus.InTransit);

    emit DeliveryInitiated(orderId, productId, quantity, retailStore);  
    emit StatusUpdated(orderId, DeliveryStatus.InTransit);    
}


    

    // Function to confirm delivery
    function confirmDelivery(uint orderId) external {
        Delivery storage delivery = deliveries[orderId];  // Fetch the delivery details using the orderId.
        require(delivery.retailStore == msg.sender, "Only the assigned retail store can confirm this delivery");   // Ensure that only the assigned retail store can confirm the delivery.
        require(delivery.status == DeliveryStatus.InTransit, "Delivery must be in transit to be confirmed");   // Ensure that delivery is in the correct status for confirmation.
        
        delivery.status = DeliveryStatus.Delivered;  // Update the status of the delivery to "Delivered".
        emit DeliveryConfirmed(orderId, msg.sender);  // Emit an event to confirm the delivery.
        emit StatusUpdated(orderId, DeliveryStatus.Delivered);   // Emit an event for the updated status.
    }

    // Function to update the status of a delivery
    function updateStatus(uint orderId, DeliveryStatus newStatus) external  {
        Delivery storage delivery = deliveries[orderId];   // Fetch the delivery details using the orderId.
        delivery.status = newStatus;   // Update the status of the delivery.
        emit StatusUpdated(orderId, newStatus);    // Emit an event for the updated status.
    }

    // Function to get the deteails of a delivery
     function getDeliveryDetails(uint orderId) external view returns (uint, uint, uint, address, string memory) {
        Delivery storage delivery = deliveries[orderId];
        return (delivery.orderId, delivery.productId, delivery.quantity, delivery.retailStore, _getStatusString(delivery.status));
    }


     // Get the status as a string because enum returns integers.
    function getDeliveryStatusAsString(uint orderId) external view returns (string memory) {
        Delivery storage delivery = deliveries[orderId];
        return _getStatusString(delivery.status);
    }

    // Helper function to convert enum to string
    function _getStatusString(DeliveryStatus status) internal pure returns (string memory) {
        if (status == DeliveryStatus.InTransit) {
            return "In Transit";
        } else if (status == DeliveryStatus.Delivered) {
            return "Delivered";
        } else if (status == DeliveryStatus.Cancelled) {
            return "Cancelled";
        } else {
            return "Unknown";
        }
    }
}