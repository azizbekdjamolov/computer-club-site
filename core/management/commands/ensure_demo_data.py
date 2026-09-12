import os
import sys

from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = 'Create a default admin user and load demo data if the database is empty.'

    @transaction.atomic
    def handle(self, *args, **options):
        if not User.objects.filter(is_superuser=True).exists():
            username = os.environ.get('DJANGO_ADMIN_USER', 'admin')
            email = os.environ.get('DJANGO_ADMIN_EMAIL', 'admin@example.com')
            password = os.environ.get('DJANGO_ADMIN_PASSWORD')
            if not password:
                # Produktsiyada ochiq ma'lum bo'lgan parol yaratish mumkin emas
                if os.environ.get('DJANGO_DEBUG', 'True') == 'True':
                    password = 'Admin12345'
                else:
                    self.stderr.write(
                        self.style.WARNING(
                            'DJANGO_ADMIN_PASSWORD env o\'zgaruvchisi o\'rnatilmagan; '
                            'superuser yaratilmadi.'
                        )
                    )
            else:
                User.objects.create_superuser(
                    username=username, email=email, password=password
                )
                self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" created.'))

        from core.models import Room

        if not Room.objects.exists():
            try:
                call_command('loaddata', 'initial.json', verbosity=0)
                self.stdout.write(self.style.SUCCESS('Demo data loaded from initial.json.'))
            except Exception as exc:
                self.stderr.write(self.style.ERROR(f'Failed to load demo data: {exc}'))
                sys.exit(1)
        else:
            self.stdout.write('Demo data already present, skipping.')