# User Service

Independent Django + DRF microservice for student profiles and preferences.

## Implemented Phase
- Phase 03 (`docs/03-user-service.md`).

## Endpoints
- `GET /users/{user_id}/profile`
- `PUT /users/{user_id}/profile`
- `GET /users/{user_id}/preferences/housing`
- `PUT /users/{user_id}/preferences/housing`
- `GET /users/{user_id}/preferences/lifestyle`
- `PUT /users/{user_id}/preferences/lifestyle`
- `GET /users/{user_id}/profile-completion`

## Auth Integration
- Validates JWT access token issued by Auth Service.
- Uses token `sub` as authenticated `user_id`.
- Allows admins (`roles` includes `admin`) to manage any user profile.

## Run
1. Copy `.env.example` to `.env`.
2. `pip install -r requirements/dev.txt`
3. `python manage.py migrate`
4. `python manage.py runserver 0.0.0.0:8002`

## Tests
- `set DJANGO_ENV=test && python manage.py test`
