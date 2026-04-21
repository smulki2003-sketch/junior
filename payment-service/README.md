# Payment Service

Independent Django + DRF microservice for payment intent simulation, transaction outcomes, callbacks, and refunds.

## Implemented Phase
- Phase 07 (`docs/07-payment-service.md`)

## Endpoints
- `POST /payments/intents`
- `POST /payments/{payment_id}/simulate-success`
- `POST /payments/{payment_id}/simulate-failure`
- `POST /payments/{payment_id}/refund`
- `GET /payments/{payment_id}`
- `POST /payments/callbacks/booking-status`

## Run
1. Copy `.env.example` to `.env`
2. `pip install -r requirements/dev.txt`
3. `python manage.py migrate`
4. `python manage.py runserver 0.0.0.0:8006`

## Tests
- `set DJANGO_ENV=test && python manage.py test`

