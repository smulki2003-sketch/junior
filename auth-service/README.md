# Auth Service

Independent Django + DRF authentication microservice for the student housing platform.

## Phase 02 Scope Implemented
- User registration, login, logout, token refresh, and identity endpoint.
- JWT access and refresh token flow.
- Role model (`student`, `admin`) and admin-only role assignment API.
- Password reset request/confirm workflow.
- Security audit logging.

## API Endpoints
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/logout`
- `POST /auth/refresh`
- `GET /auth/me`
- `POST /auth/password-reset/request`
- `POST /auth/password-reset/confirm`
- `PATCH /auth/users/{id}/roles`

## Quick Start
1. Copy `.env.example` to `.env`.
2. Install dependencies:
   - `pip install -r requirements/dev.txt`
3. Apply migrations:
   - `python manage.py migrate`
4. Ensure default roles:
   - `python manage.py sync_auth_defaults`
5. Run service:
   - `python manage.py runserver 0.0.0.0:8001`

## Run Tests
- `set DJANGO_ENV=test && python manage.py test`

## Folder Layout
- `apps/authentication/` Core auth domain.
- `config/settings/` Environment-based Django settings.
- `tests/` Integration tests for auth lifecycle.
