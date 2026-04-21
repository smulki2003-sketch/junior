# Admin Control Service

Independent Django + DRF microservice for centralized admin orchestration across user, housing, booking, payment, notification, and moderation domains.

## Implemented Phase
- Phase 12 (`docs/12-admin-control-service.md`)

## Endpoints
- `GET /admin/dashboard/overview`
- `GET /admin/users`
- `PATCH /admin/users/{user_id}/status`
- `GET /admin/housing/pending`
- `PATCH /admin/housing/{unit_id}/approval`
- `GET /admin/bookings`
- `PATCH /admin/bookings/{booking_id}/status`
- `GET /admin/payments`
- `POST /admin/notifications/broadcast`
- `GET /admin/complaints`

## Integration
- Uses Auth Service JWT admin identity checks.
- Orchestrates operations by calling Auth, User, Housing, Booking, Payment, Notification, Moderation, and Roommate services.
- Persists audit trails in `admin_action_logs` and contextual governance notes in `admin_notes`.

## Run
1. Copy `.env.example` to `.env`
2. `pip install -r requirements/dev.txt`
3. `python manage.py migrate`
4. `python manage.py runserver 0.0.0.0:8011`

## Tests
- `set DJANGO_ENV=test && python manage.py test`

