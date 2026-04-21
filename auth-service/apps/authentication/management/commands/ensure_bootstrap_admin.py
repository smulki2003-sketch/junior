from django.core.management.base import BaseCommand

from apps.authentication.models import AuthRole, AuthUser
from apps.authentication.services import ensure_default_roles, hash_password, set_user_roles


class Command(BaseCommand):
    help = "Ensure at least one admin user exists. If no admin exists, create bootstrap admin."

    def add_arguments(self, parser):
        parser.add_argument("--email", type=str, default="admin@gmail.local")
        parser.add_argument("--password", type=str, default="Admin@123")

    def handle(self, *args, **options):
        email = str(options["email"]).strip().lower()
        password = str(options["password"])

        ensure_default_roles()

        any_admin_exists = AuthUser.objects.filter(
            role_links__role__name=AuthRole.ROLE_ADMIN,
            is_active=True,
        ).exists()
        if any_admin_exists:
            self.stdout.write(self.style.SUCCESS("Admin already exists. No bootstrap admin created."))
            return

        user, created = AuthUser.objects.get_or_create(
            email=email,
            defaults={
                "password_hash": hash_password(password),
                "is_active": True,
            },
        )
        if not created:
            user.password_hash = hash_password(password)
            user.is_active = True
            user.save(update_fields=["password_hash", "is_active", "updated_at"])

        set_user_roles(user, [AuthRole.ROLE_ADMIN])
        self.stdout.write(self.style.SUCCESS(f"Bootstrap admin ready: {email}"))
