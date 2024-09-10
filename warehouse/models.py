from django.db import models
from django.utils.timezone import now


# Create your models here.
class Product(models.Model):
    date = models.DateField(default=now)
    name = models.CharField('Product Name', max_length = 100)
    description = models.CharField('Description Product', max_length = 100)
    unitofmesurment = models.CharField('Unit Of Mesurment', max_length = 60)
    quantity = models.FloatField('Quantity', max_length = 10)
    reorderpoint = models.FloatField('Reorder Point', max_length = 10)
    price = models.FloatField('Price', max_length = 10)
    supplierinfo = models.CharField('Supplier Info', max_length = 100)
    category = models.CharField('Category', max_length = 100)
    comments = models.CharField('Comments', max_length = 100)
    # image = models.ImageField()

    def __str__(self):
        return(f"{self.name} {self.description}")
    
    class Meta:
        verbose_name_plural = 'Products'
        ordering: ['-date']

class Unitofmesurment(models.Model):
     name=models.CharField(max_length = 50)


     class Meta:
        verbose_name_plural = 'Unitofmesurments'

     def __str__(self):
          return self.name
          