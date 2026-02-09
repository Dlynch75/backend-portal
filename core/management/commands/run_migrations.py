"""
Django management command to run migrations.
This can be run via Vercel CLI or as a one-time script.
"""
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import connection
import sys


class Command(BaseCommand):
    help = 'Run all pending database migrations'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting database migrations...'))
        
        try:
            # Check database connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            self.stdout.write(self.style.SUCCESS('✓ Database connection successful'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Database connection failed: {str(e)}'))
            sys.exit(1)
        
        try:
            # Run migrations
            call_command('migrate', verbosity=2, interactive=False)
            self.stdout.write(self.style.SUCCESS('✓ All migrations completed successfully!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Migration failed: {str(e)}'))
            sys.exit(1)
