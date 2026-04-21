# Moderation Service

Independent Django + DRF microservice for complaint intake, moderation case handling, and enforcement actions.

## Implemented Phase
- Phase 11 (`docs/11-complaint-moderation-service.md`)

## Endpoints
- `POST /moderation/complaints`
- `GET /moderation/complaints/{complaint_id}`
- `GET /moderation/complaints`
- `PATCH /moderation/complaints/{complaint_id}/status`
- `POST /moderation/cases/{case_id}/actions`
- `POST /moderation/cases/{case_id}/comments`

## Integration
- Accepts Auth Service JWT access tokens for user/admin identity.
- Emits complaint lifecycle notifications through Notification Service.
- Executes moderation enforcement against Admin/Housing/Booking services.
- Supplies complaint/case/action data for Admin and Reporting services.

## Run
1. Copy `.env.example` to `.env`
2. `pip install -r requirements/dev.txt`
3. `python manage.py migrate`
4. `python manage.py runserver 0.0.0.0:8010`

## Tests
- `set DJANGO_ENV=test && python manage.py test`

