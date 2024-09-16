from django.db import models
from django.utils.timezone import now
from django.conf import settings

# Create your models here.

class Customer(models.Model):
    date = models.DateField(auto_now_add=True)
    customername = models.CharField('Full name', max_length=100)
    email = models.EmailField('Email', max_length=100, unique=True)
    phone = models.CharField('Phone number', max_length=15)
    address = models.CharField('Address', max_length=100)
    city = models.CharField('City', max_length=50)
    country = models.CharField('Country', max_length=50)
    postalcode = models.CharField('Postal code', max_length=20)
    customertitle = models.CharField('Customer title', max_length=50)
    companyname = models.CharField('Company name', max_length=50)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    
    def __str__(self):
        return (f"{self.customername}") 
    
    class Meta:
        verbose_name_plural = 'Customers'
        ordering: ['-date']