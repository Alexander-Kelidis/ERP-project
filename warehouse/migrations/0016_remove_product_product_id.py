# Generated by Django 4.2.5 on 2024-09-15 20:20

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse', '0015_product_product_id'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='product_id',
        ),
    ]
