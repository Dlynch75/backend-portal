#!/usr/bin/env python
"""
One-time migration script for production deployment.
This script can be run via Vercel CLI or directly.

Usage:
    vercel env pull .env.production
    python run_migrations.py
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'school_project.settings')
django.setup()

from django.core.management import call_command
from django.db import connection


def main():
    print("=" * 60)
    print("Running Database Migrations")
    print("=" * 60)
    
    # Check database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        print("✓ Database connection successful")
    except Exception as e:
        print(f"✗ Database connection failed: {str(e)}")
        sys.exit(1)
    
    # Run migrations
    try:
        print("\nRunning migrations...")
        call_command('migrate', verbosity=2, interactive=False)
        print("\n✓ All migrations completed successfully!")
        print("=" * 60)
    except Exception as e:
        print(f"\n✗ Migration failed: {str(e)}")
        print("=" * 60)
        sys.exit(1)


if __name__ == '__main__':
    main()
