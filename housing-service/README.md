# Housing Service

Independent Django + DRF microservice for housing inventory and availability management.

## Implemented Phase
- Phase 04 (`docs/04-housing-service.md`).

## Endpoints
- `POST /housing/units`
- `GET /housing/units`
- `GET /housing/units/{unit_id}`
- `PATCH /housing/units/{unit_id}`
- `DELETE /housing/units/{unit_id}`
- `PUT /housing/units/{unit_id}/availability`
- `GET /housing/amenities`
- `POST /housing/amenities`

## Auth Integration
- Uses Auth Service JWT access token (`sub`, `roles`).
- Listing modifications allowed for owner or admin.
- Amenity creation restricted to admin role.

## Run
1. Copy `.env.example` to `.env`.
2. `pip install -r requirements/dev.txt`
3. `python manage.py migrate`
4. `python manage.py runserver 0.0.0.0:8003`

## Tests
- `set DJANGO_ENV=test && python manage.py test`
