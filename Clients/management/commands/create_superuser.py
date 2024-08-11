import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Create a superuser if it does not exist'

    def handle(self, *args, **options):
        User = get_user_model()
        email = os.getenv('DJANGO_SUPERUSER_EMAIL', 'admin@example.com') 
        password = os.getenv('DJANGO_SUPERUSER_PASSWORD', 'adminpassword')  

        if not User.objects.filter(email=email).exists():
            User.objects.create_superuser(email=email, password=password)
            self.stdout.write(self.style.SUCCESS(f'Successfully created superuser with email {email}'))
        else:
            self.stdout.write(self.style.WARNING(f'Superuser with email {email} already exists'))
