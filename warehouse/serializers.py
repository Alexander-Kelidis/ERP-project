from rest_framework import serializers
from .models import Product, Unitofmesurment

class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'

class UnitofmesurmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unitofmesurment
        fields = '__all__'
