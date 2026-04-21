from django.core.management.base import BaseCommand

from apps.authentication.services import ensure_default_roles


class Command(BaseCommand):
    help = "Create required default auth roles."

    def handle(self, *args, **options):
        ensure_default_roles()
        self.stdout.write(self.style.SUCCESS("Default roles synced: student, admin"))

