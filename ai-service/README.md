# AI Recommendation Service

Independent Django + DRF microservice implementing Phase 09 housing recommendations with deterministic content-based scoring.

## Endpoints
- `POST /ai/recommendations/housing/{user_id}/refresh`
- `GET /ai/recommendations/housing/{user_id}`
- `POST /ai/recommendations/housing/{user_id}/feedback`
- `GET /ai/recommendations/housing/{user_id}/explain/{unit_id}`

## Tech
- numpy, pandas, scikit-learn cosine similarity
- Deterministic, explainable, no model training

## Run
1. Copy `.env.example` to `.env`
2. `pip install -r requirements/dev.txt`
3. `python manage.py migrate`
4. `python manage.py runserver 0.0.0.0:8008`

## Tests
- `set DJANGO_ENV=test && python manage.py test`

