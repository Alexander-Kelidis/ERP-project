from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):

    USER_ROLES = (
        ('retail_store', 'Retail Store'),
        ('distributor', 'Distributor'),
        ('manufacturer', 'Manufacturer'),
        ('supplier', 'Supplier'),
    )
    user_role = models.CharField(max_length=20, choices=USER_ROLES, default='retail_store')

     # Add Ethereum address field
    eth_address = models.CharField(max_length=42, unique=True, null=True, blank=True)  # Ethereum addresses are 42 characters long
