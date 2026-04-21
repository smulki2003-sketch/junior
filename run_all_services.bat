@echo off
set BOOTSTRAP_ADMIN_EMAIL=admin@gmail.local
set BOOTSTRAP_ADMIN_PASSWORD=Admin@123

echo ======================================
echo FULL BACKEND START (ALL SERVICES)
echo ======================================

call :start_service api-gateway 8000
call :start_service auth-service 8001
call :start_service user-service 8002
call :start_service housing-service 8003
call :start_service search-service 8004
call :start_service booking-service 8005
call :start_service payment-service 8006
call :start_service notification-service 8007
call :start_service ai-service 8008
call :start_service moderation-service 8009
call :start_service admin-service 8010
call :start_service reporting-service 8011
call :start_service roommate-service 8012

echo.
echo ======================================
echo ALL SERVICES STARTED SUCCESSFULLY
echo ======================================
pause
goto :eof

:start_service
set SERVICE_NAME=%~1
set SERVICE_PORT=%~2

echo.
echo ================================
echo Processing %SERVICE_NAME%
echo ================================

cd %SERVICE_NAME%

IF NOT EXIST venv (
    echo Creating virtual environment for %SERVICE_NAME%...
    python -m venv venv
)

call venv\Scripts\activate

echo Upgrading pip...
python -m pip install --upgrade pip

echo Installing BASE requirements...
IF EXIST requirements\base.txt (
    pip install -r requirements\base.txt
)

echo Installing DEV requirements...
IF EXIST requirements\dev.txt (
    pip install -r requirements\dev.txt
)

echo Creating migrations...
python manage.py makemigrations

echo Running migrations...
python manage.py migrate

IF /I "%SERVICE_NAME%"=="auth-service" (
    echo Ensuring default roles...
    python manage.py sync_auth_defaults
    echo Ensuring bootstrap admin exists if no admin account is present...
    python manage.py ensure_bootstrap_admin --email "%BOOTSTRAP_ADMIN_EMAIL%" --password "%BOOTSTRAP_ADMIN_PASSWORD%"
)

echo Starting server on port %SERVICE_PORT%...
start cmd /k "venv\Scripts\activate && python manage.py runserver %SERVICE_PORT%"

cd ..
goto :eof
