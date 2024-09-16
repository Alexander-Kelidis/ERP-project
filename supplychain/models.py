from django.db import models
from warehouse.models import Product
from django.utils.timezone import now
from django.conf import settings

# Create your models here.


class Order(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    retail_store = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('processed', 'Processed'), ('delivered', 'Delivered')])
    created_at = models.DateTimeField(default=now)

    def __str__(self):
        return f"Order {self.id} - {self.product.name} ({self.quantity})"

class Delivery(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    delivery_status = models.CharField(max_length=20, choices=[('in_transit', 'In Transit'), ('delivered', 'Delivered'), ('cancelled', 'Cancelled')])
    delivered_at = models.DateTimeField(null=True, blank=True)
    distributor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='deliveries')
    retail_store = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='received_deliveries')

    def __str__(self):
        return f"Delivery for Order {self.order.id} - Status: {self.delivery_status}"
