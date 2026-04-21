# API Gateway Service

Single entry point for all frontend traffic in the student housing microservices platform.

## Implemented in Phase 01
- Django + DRF service scaffold.
- Environment-based settings (`development`, `production`, `test`).
- Route registry and proxy for `/api/v1/*`.
- Request correlation, structured logging, request auditing.
- Basic rate limiting by IP and authenticated user identifier.
- Gateway operational endpoints:
  - `GET /gateway/health`
  - `GET /gateway/ready`
  - `GET /gateway/routes`

## Quick Start
1. Create environment file:
   - Copy `.env.example` to `.env`.
2. Install dependencies:
   - `pip install -r requirements/dev.txt`
3. Run migrations:
   - `python manage.py migrate`
4. Seed defaults:
   - `python manage.py sync_gateway_routes`
5. Run server:
   - `python manage.py runserver 0.0.0.0:8000`

## Run Tests
- `set DJANGO_ENV=test && python manage.py test`

## Folder Layout
- `apps/gateway/` Gateway app (models, middleware, proxy views, commands).
- `config/settings/` Environment settings modules.
- `docs/` API behavior conventions.
- `tests/` Smoke tests for gateway behavior.
