# Generated by Django 4.2.5 on 2024-02-15 12:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('warehouse', '0007_alter_product_options'),
    ]

    operations = [
        migrations.CreateModel(
            name='Unitofmesurment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
            ],
        ),
        migrations.AlterModelOptions(
            name='product',
            options={},
        ),
    ]
