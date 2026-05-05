from django.core.management.base import BaseCommand

from apps.authentication.models import AuthRole, AuthUser
from apps.authentication.services import ensure_default_roles, hash_password, set_user_roles, verify_password


class Command(BaseCommand):
    help = "Enforce a single bootstrap admin account with exact credentials."

    def add_arguments(self, parser):
        parser.add_argument("--email", type=str, default="admin@gmail.local")
        parser.add_argument("--password", type=str, default="Admin@123")

    def handle(self, *args, **options):
        email = str(options["email"]).strip().lower()
        password = str(options["password"])

        ensure_default_roles()

        admin_users = AuthUser.objects.filter(
            role_links__role__name=AuthRole.ROLE_ADMIN,
        ).distinct()
        admin_count = admin_users.count()

        desired_user = AuthUser.objects.filter(email=email).first()
        desired_is_valid = False
        if desired_user:
            desired_roles = set(
                desired_user.role_links.values_list("role__name", flat=True)
            )
            desired_is_valid = (
                desired_user.is_active
                and AuthRole.ROLE_ADMIN in desired_roles
                and verify_password(password, desired_user.password_hash)
            )

        # Desired state: exactly one admin and it matches the configured credentials.
        if desired_is_valid and admin_count == 1:
            self.stdout.write(self.style.SUCCESS(f"Bootstrap admin already aligned: {email}"))
            return

        # Any mismatch: remove current admin users and rebuild bootstrap admin from configured values.
        removed_admins = admin_users.count()
        if removed_admins:
            admin_users.delete()

        stale_target_user = AuthUser.objects.filter(email=email).first()
        if stale_target_user:
            stale_target_user.delete()

        user = AuthUser.objects.create(
            email=email,
            password_hash=hash_password(password),
            is_active=True,
        )
        set_user_roles(user, [AuthRole.ROLE_ADMIN])

        self.stdout.write(
            self.style.SUCCESS(
                f"Bootstrap admin reset complete: {email} (removed_admins={removed_admins})"
            )
        )
