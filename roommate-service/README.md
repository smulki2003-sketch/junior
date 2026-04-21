# Roommate Matching Service

Independent Django + DRF microservice implementing Phase 10 roommate questionnaire, vectorization, and compatibility matching.

## Endpoints
- `GET /ai/roommates/questionnaire`
- `POST /ai/roommates/answers/{user_id}`
- `POST /ai/roommates/matches/{user_id}/refresh`
- `GET /ai/roommates/matches/{user_id}`
- `GET /ai/roommates/matches/{user_id}/explain/{candidate_user_id}`
- `POST /ai/roommates/questionnaire`

## Scoring
- Deterministic vector scoring using cosine similarity (default) and optional euclidean mode.
- No model training, no deep learning.

## Run
1. Copy `.env.example` to `.env`
2. `pip install -r requirements/dev.txt`
3. `python manage.py migrate`
4. `python manage.py runserver 0.0.0.0:8009`

## Tests
- `set DJANGO_ENV=test && python manage.py test`

