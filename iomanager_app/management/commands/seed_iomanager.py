from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create default login user for iomanager"

    def add_arguments(self, parser):
        parser.add_argument("--username", default="manager")
        parser.add_argument("--password", default="manager1234")

    def handle(self, *args, **options):
        username = options["username"]
        password = options["password"]
        user_model = get_user_model()

        if user_model.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f"User already exists: {username}"))
            return

        user_model.objects.create_user(username=username, password=password, is_staff=True)
        self.stdout.write(self.style.SUCCESS(f"Created default user: {username}"))
