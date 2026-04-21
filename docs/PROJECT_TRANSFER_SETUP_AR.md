# دليل نقل المشروع وتشغيله (لصديقك)

هذا الملف يشرح:
- أمثلة `.env` لكل خدمة بقيم وهمية.
- طريقة تشغيل المشروع.
- كيف يعمل إنشاء الأدمن تلقائيًا من `run_all_services.bat`.

## 1) متطلبات التشغيل

- Python 3.10+
- Node.js 18+
- PostgreSQL (محلي)

## 2) إعداد ملفات البيئة `.env`

انسخ القيم التالية لكل خدمة داخل ملف `.env` ضمن مجلد الخدمة نفسها.

مهم:
- القيم التالية وهمية (آمنة للمشاركة).
- يجب أن يكون `INTERNAL_SERVICE_TOKEN` نفسه في كل الخدمات التي تستخدمه.

### `api-gateway/.env`
```env
DJANGO_ENV=development
DEBUG=true
SECRET_KEY=fake_gateway_secret_key_123
ALLOWED_HOSTS=localhost,127.0.0.1

DB_ENGINE=django.db.backends.postgresql
DB_NAME=student_housing_gateway_db
DB_USER=postgres
DB_PASSWORD=fake_postgres_password
DB_HOST=localhost
DB_PORT=5432

AUTH_SERVICE_URL=http://localhost:8001/auth
USER_SERVICE_URL=http://localhost:8002/users
HOUSING_SERVICE_URL=http://localhost:8003/housing
SEARCH_SERVICE_URL=http://localhost:8004/search
BOOKING_SERVICE_URL=http://localhost:8005/bookings
PAYMENT_SERVICE_URL=http://localhost:8006/payments
NOTIFICATION_SERVICE_URL=http://localhost:8007/notifications
AI_SERVICE_URL=http://localhost:8008/ai
ROOMMATE_SERVICE_URL=http://localhost:8012
MODERATION_SERVICE_URL=http://localhost:8009/moderation
ADMIN_SERVICE_URL=http://localhost:8010/admin
REPORTING_SERVICE_URL=http://localhost:8011/reports

GATEWAY_UPSTREAM_TIMEOUT_SECONDS=20
RATE_LIMIT_IP_PER_MINUTE=120
RATE_LIMIT_IP_BURST=30
RATE_LIMIT_USER_PER_MINUTE=240
RATE_LIMIT_USER_BURST=60
GATEWAY_LOG_LEVEL=INFO

CORS_ALLOW_ALL_ORIGINS=false
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://127.0.0.1:5173,http://localhost:5174,http://127.0.0.1:5174
INTERNAL_SERVICE_TOKEN=fake_internal_service_token_shared
```

### `auth-service/.env`
```env
DJANGO_ENV=development
DEBUG=true
SECRET_KEY=fake_auth_secret_key_123
ALLOWED_HOSTS=localhost,127.0.0.1

DB_ENGINE=django.db.backends.postgresql
DB_NAME=student_housing_auth_db
DB_USER=postgres
DB_PASSWORD=fake_postgres_password
DB_HOST=localhost
DB_PORT=5432

JWT_SECRET_KEY=fake_jwt_secret_key_123
JWT_ALGORITHM=HS256
JWT_ACCESS_TTL_MINUTES=15
JWT_REFRESH_TTL_DAYS=7
PASSWORD_RESET_TTL_MINUTES=60
EXPOSE_PASSWORD_RESET_TOKEN=true

INTERNAL_SERVICE_TOKEN=fake_internal_service_token_shared
```

### `user-service/.env`
```env
DJANGO_ENV=development
DEBUG=true
SECRET_KEY=fake_user_service_secret
ALLOWED_HOSTS=localhost,127.0.0.1

DB_ENGINE=django.db.backends.postgresql
DB_NAME=student_housing_user_db
DB_USER=postgres
DB_PASSWORD=fake_postgres_password
DB_HOST=localhost
DB_PORT=5432

AUTH_SERVICE_JWT_SECRET=fake_jwt_secret_key_123
AUTH_SERVICE_JWT_ALGORITHM=HS256
INTERNAL_SERVICE_TOKEN=fake_internal_service_token_shared
```

### `housing-service/.env`
```env
DJANGO_ENV=development
DEBUG=true
SECRET_KEY=fake_housing_service_secret
ALLOWED_HOSTS=localhost,127.0.0.1

DB_ENGINE=django.db.backends.postgresql
DB_NAME=student_housing_housing_db
DB_USER=postgres
DB_PASSWORD=fake_postgres_password
DB_HOST=localhost
DB_PORT=5432

AUTH_SERVICE_JWT_SECRET=fake_jwt_secret_key_123
AUTH_SERVICE_JWT_ALGORITHM=HS256
INTERNAL_SERVICE_TOKEN=fake_internal_service_token_shared
```

### `search-service/.env`
```env
DJANGO_ENV=development
DEBUG=true
SECRET_KEY=fake_search_service_secret
ALLOWED_HOSTS=*

DB_ENGINE=django.db.backends.postgresql
DB_NAME=student_housing_search_db
DB_USER=postgres
DB_PASSWORD=fake_postgres_password
DB_HOST=localhost
DB_PORT=5432

AUTH_SERVICE_JWT_SECRET=fake_jwt_secret_key_123
AUTH_SERVICE_JWT_ALGORITHM=HS256
HOUSING_SERVICE_BASE_URL=http://localhost:8003
INTERNAL_SERVICE_TOKEN=fake_internal_service_token_shared
```

### `booking-service/.env`
```env
DJANGO_ENV=development
DEBUG=true
SECRET_KEY=fake_booking_service_secret
ALLOWED_HOSTS=*

DB_ENGINE=django.db.backends.postgresql
DB_NAME=student_housing_booking_db
DB_USER=postgres
DB_PASSWORD=fake_postgres_password
DB_HOST=localhost
DB_PORT=5432

AUTH_SERVICE_JWT_SECRET=fake_jwt_secret_key_123
AUTH_SERVICE_JWT_ALGORITHM=HS256
HOUSING_SERVICE_BASE_URL=http://localhost:8003
PAYMENT_SERVICE_BASE_URL=http://localhost:8006
NOTIFICATION_SERVICE_BASE_URL=http://localhost:8007
BOOKING_LOCK_MINUTES=15
INTERNAL_SERVICE_TOKEN=fake_internal_service_token_shared
```

### `payment-service/.env`
```env
DJANGO_ENV=development
DEBUG=true
SECRET_KEY=fake_payment_service_secret
ALLOWED_HOSTS=*

DB_ENGINE=django.db.backends.postgresql
DB_NAME=student_housing_payment_db
DB_USER=postgres
DB_PASSWORD=fake_postgres_password
DB_HOST=localhost
DB_PORT=5432

AUTH_SERVICE_JWT_SECRET=fake_jwt_secret_key_123
AUTH_SERVICE_JWT_ALGORITHM=HS256
BOOKING_SERVICE_BASE_URL=http://localhost:8005
NOTIFICATION_SERVICE_BASE_URL=http://localhost:8007
INTERNAL_SERVICE_TOKEN=fake_internal_service_token_shared
```

### `notification-service/.env`
```env
DJANGO_ENV=development
DEBUG=true
SECRET_KEY=fake_notification_service_secret
ALLOWED_HOSTS=*

DB_ENGINE=django.db.backends.postgresql
DB_NAME=student_housing_notification_db
DB_USER=postgres
DB_PASSWORD=fake_postgres_password
DB_HOST=localhost
DB_PORT=5432

AUTH_SERVICE_JWT_SECRET=fake_jwt_secret_key_123
AUTH_SERVICE_JWT_ALGORITHM=HS256
INTERNAL_SERVICE_TOKEN=fake_internal_service_token_shared
```

### `ai-service/.env`
```env
DJANGO_ENV=development
DEBUG=true
SECRET_KEY=fake_ai_service_secret
ALLOWED_HOSTS=*

DB_ENGINE=django.db.backends.postgresql
DB_NAME=student_housing_ai_recommendation_db
DB_USER=postgres
DB_PASSWORD=fake_postgres_password
DB_HOST=localhost
DB_PORT=5432

AUTH_SERVICE_JWT_SECRET=fake_jwt_secret_key_123
AUTH_SERVICE_JWT_ALGORITHM=HS256
USER_SERVICE_BASE_URL=http://localhost:8002
HOUSING_SERVICE_BASE_URL=http://localhost:8003
SEARCH_SERVICE_BASE_URL=http://localhost:8004
NOTIFICATION_SERVICE_BASE_URL=http://localhost:8007
INTERNAL_SERVICE_TOKEN=fake_internal_service_token_shared
AI_UPSTREAM_TIMEOUT_SECONDS=3.0
AI_NOTIFICATION_TIMEOUT_SECONDS=1.5
```

### `moderation-service/.env`
```env
DJANGO_ENV=development
DEBUG=true
SECRET_KEY=fake_moderation_service_secret
ALLOWED_HOSTS=*

DB_ENGINE=django.db.backends.postgresql
DB_NAME=student_housing_moderation_db
DB_USER=postgres
DB_PASSWORD=fake_postgres_password
DB_HOST=localhost
DB_PORT=5432

AUTH_SERVICE_JWT_SECRET=fake_jwt_secret_key_123
AUTH_SERVICE_JWT_ALGORITHM=HS256
NOTIFICATION_SERVICE_BASE_URL=http://localhost:8007
HOUSING_SERVICE_BASE_URL=http://localhost:8003
BOOKING_SERVICE_BASE_URL=http://localhost:8005
ADMIN_SERVICE_BASE_URL=http://localhost:8010
INTERNAL_SERVICE_TOKEN=fake_internal_service_token_shared
```

### `admin-service/.env`
```env
DJANGO_ENV=development
DEBUG=true
SECRET_KEY=fake_admin_service_secret
ALLOWED_HOSTS=*

DB_ENGINE=django.db.backends.postgresql
DB_NAME=student_housing_admin_db
DB_USER=postgres
DB_PASSWORD=fake_postgres_password
DB_HOST=localhost
DB_PORT=5432

AUTH_SERVICE_JWT_SECRET=fake_jwt_secret_key_123
AUTH_SERVICE_JWT_ALGORITHM=HS256
INTERNAL_SERVICE_TOKEN=fake_internal_service_token_shared

AUTH_SERVICE_BASE_URL=http://localhost:8001
USER_SERVICE_BASE_URL=http://localhost:8002
HOUSING_SERVICE_BASE_URL=http://localhost:8003
BOOKING_SERVICE_BASE_URL=http://localhost:8005
PAYMENT_SERVICE_BASE_URL=http://localhost:8006
NOTIFICATION_SERVICE_BASE_URL=http://localhost:8007
ROOMMATE_SERVICE_BASE_URL=http://localhost:8012
MODERATION_SERVICE_BASE_URL=http://localhost:8009
```

### `reporting-service/.env`
```env
DJANGO_ENV=development
DEBUG=true
SECRET_KEY=fake_reporting_service_secret
ALLOWED_HOSTS=*

DB_ENGINE=django.db.backends.postgresql
DB_NAME=student_housing_reporting_db
DB_USER=postgres
DB_PASSWORD=fake_postgres_password
DB_HOST=localhost
DB_PORT=5432

AUTH_SERVICE_JWT_SECRET=fake_jwt_secret_key_123
AUTH_SERVICE_JWT_ALGORITHM=HS256
INTERNAL_SERVICE_TOKEN=fake_internal_service_token_shared

ADMIN_SERVICE_BASE_URL=http://localhost:8010
BOOKING_SERVICE_BASE_URL=http://localhost:8005
PAYMENT_SERVICE_BASE_URL=http://localhost:8006
HOUSING_SERVICE_BASE_URL=http://localhost:8003
NOTIFICATION_SERVICE_BASE_URL=http://localhost:8007
AI_SERVICE_BASE_URL=http://localhost:8008
ROOMMATE_SERVICE_BASE_URL=http://localhost:8012
MODERATION_SERVICE_BASE_URL=http://localhost:8009

METRICS_SAMPLE_USER_IDS=1,2,3
METRICS_SAMPLE_PAYMENT_IDS=1,2,3
```

### `roommate-service/.env`
```env
DJANGO_ENV=development
DEBUG=true
SECRET_KEY=fake_roommate_service_secret
ALLOWED_HOSTS=*

DB_ENGINE=django.db.backends.postgresql
DB_NAME=student_housing_roommate_db
DB_USER=postgres
DB_PASSWORD=fake_postgres_password
DB_HOST=localhost
DB_PORT=5432

AUTH_SERVICE_JWT_SECRET=fake_jwt_secret_key_123
AUTH_SERVICE_JWT_ALGORITHM=HS256
USER_SERVICE_BASE_URL=http://localhost:8002
NOTIFICATION_SERVICE_BASE_URL=http://localhost:8007
INTERNAL_SERVICE_TOKEN=fake_internal_service_token_shared
```

### `frontend-user/.env`
```env
VITE_API_BASE_URL=http://localhost:8000
```

### `frontend-admin/.env`
```env
VITE_ADMIN_API_BASE_URL=http://localhost:8000
```

## 3) طريقة التشغيل

من داخل جذر المشروع:

```bat
run_all_services.bat
```

السكريبت سيقوم بـ:
- إنشاء `venv` لكل خدمة إن لم يوجد.
- تثبيت المتطلبات.
- `makemigrations` ثم `migrate`.
- تشغيل كل خدمة على بورتها.

ثم شغّل الواجهات:

```powershell
cd frontend-user
npm install
npm run dev
```

```powershell
cd frontend-admin
npm install
npm run dev
```

## 4) منطق إنشاء الأدمن تلقائيًا

تم تحديث `run_all_services.bat` بحيث في خدمة `auth-service` بعد الـ migrations:
- يشغّل `sync_auth_defaults`.
- ثم يفحص إن كان يوجد أي مستخدم بدور `admin`.
- إذا لا يوجد أدمن، ينشئ حساب Bootstrap Admin:
  - Email: `admin@gmail.local`
  - Password: `Admin@123`


