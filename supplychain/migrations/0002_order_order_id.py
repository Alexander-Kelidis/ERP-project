# Generated by Django 4.2.5 on 2024-09-16 13:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('supplychain', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='order_id',
            field=models.CharField(default=1, max_length=50, unique=True, verbose_name='Order ID'),
            preserve_default=False,
        ),
    ]
