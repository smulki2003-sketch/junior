# Notification Service

Independent Django + DRF microservice for internal event notifications, user inbox, templates, preferences, and read tracking.

## Implemented Phase
- Phase 08 (`docs/08-notification-service.md`)

## Endpoints
- `POST /notifications/send`
- `GET /notifications/users/{user_id}`
- `PATCH /notifications/{notification_id}/read`
- `PATCH /notifications/users/{user_id}/read-all`
- `GET /notifications/templates`
- `POST /notifications/templates`
- `PUT /notifications/users/{user_id}/preferences`

## Compatibility Endpoint
- `POST /notifications/events` (bridge endpoint for existing booking-service integration)

## Run
1. Copy `.env.example` to `.env`
2. `pip install -r requirements/dev.txt`
3. `python manage.py migrate`
4. `python manage.py runserver 0.0.0.0:8007`

## Tests
- `set DJANGO_ENV=test && python manage.py test`

