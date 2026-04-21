# Search Service

Independent Django + DRF microservice for housing search, filtering, and saved filter presets.

## Implemented Phase
- Phase 05 (`docs/05-search-service.md`).

## Endpoints
- `GET /search/housing`
- `GET /search/housing/suggestions`
- `POST /search/index/sync`
- `POST /search/saved-filters`
- `GET /search/saved-filters/{user_id}`
- `DELETE /search/saved-filters/{filter_id}`

## Integration
- Validates JWT access tokens from Auth Service.
- Supports pulling listing index data from Housing Service for sync jobs.
- Captures query logs for Reporting and Analytics consumers.

## Run
1. Copy `.env.example` to `.env`.
2. `pip install -r requirements/dev.txt`
3. `python manage.py migrate`
4. `python manage.py runserver 0.0.0.0:8004`

## Tests
- `set DJANGO_ENV=test && python manage.py test`

