# Reporting and Analytics Service

Independent Django + DRF microservice for KPI snapshots, operational reporting, and CSV exports.

## Implemented Phase
- Phase 13 (`docs/13-reporting-analytics-service.md`)

## Endpoints
- `GET /reports/kpis`
- `GET /reports/bookings`
- `GET /reports/payments`
- `GET /reports/housing`
- `GET /reports/ai/recommendations`
- `GET /reports/ai/roommates`
- `GET /reports/moderation`
- `GET /reports/export`

## Scheduled Aggregation
- Management command: `python manage.py aggregate_daily_metrics [--date YYYY-MM-DD]`

## Integration
- Collects daily source snapshots from Admin, Booking, Payment, Housing, Notification, AI, Roommate, and Moderation services.
- Stores independent metric tables (`kpi_daily`, `booking_metrics_daily`, `payment_metrics_daily`, `ai_metrics_daily`, `moderation_metrics_daily`).
- Supports filterable date-range analytics and downloadable CSV reports.

## Run
1. Copy `.env.example` to `.env`
2. `pip install -r requirements/dev.txt`
3. `python manage.py migrate`
4. `python manage.py aggregate_daily_metrics`
5. `python manage.py runserver 0.0.0.0:8012`

## Tests
- `set DJANGO_ENV=test && python manage.py test`

