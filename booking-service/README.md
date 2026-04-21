# Booking Service

Independent Django + DRF microservice for booking lifecycle and reservation state transitions.

## Implemented Phase
- Phase 06 (`docs/06-booking-service.md`).

## Endpoints
- `POST /bookings`
- `GET /bookings/{booking_id}`
- `GET /bookings/users/{user_id}`
- `PATCH /bookings/{booking_id}/status`
- `POST /bookings/{booking_id}/cancel`
- `GET /bookings/{booking_id}/timeline`

## Integration
- Uses Auth Service JWT identity (`sub`, `roles`).
- Verifies housing availability through Housing Service before creating bookings.
- Triggers payment intent creation in Payment Service.
- Emits lifecycle notification hooks for Notification Service and admin workflows.

## Run
1. Copy `.env.example` to `.env`.
2. `pip install -r requirements/dev.txt`
3. `python manage.py migrate`
4. `python manage.py runserver 0.0.0.0:8005`

## Tests
- `set DJANGO_ENV=test && python manage.py test`

