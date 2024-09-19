# supplychain/management/commands/reset_order_sequence.py

from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Resets the order sequence in the database'

    def handle(self, *args, **kwargs):
        with connection.cursor() as cursor:
            # Replace 'supplychain_order' with your actual table name if different
            cursor.execute("DELETE FROM sqlite_sequence WHERE name='supplychain_order';")
            self.stdout.write(self.style.SUCCESS('Successfully reset the order sequence.'))
