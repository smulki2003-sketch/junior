@echo off
setlocal

echo =========================================
echo MASSA REAL DATA SEED (ADMIN + HOUSING)
echo =========================================

echo [1/3] Preparing auth defaults and admin account...
call :seed_auth_admin_only
if errorlevel 1 goto :failed

echo [2/3] Seeding housing dataset...
call :seed_housing
if errorlevel 1 goto :failed

echo [3/3] Syncing search index...
call :sync_search
if errorlevel 1 goto :failed

echo.
echo =========================================
echo FINISHED SUCCESSFULLY
echo =========================================
echo - Admin account: admin@gmail.local / Admin@123
echo - Seeded housing titles now use prefix: UniNest
echo - Search index is refreshed from seeded housing units
pause
exit /b 0

:prepare_service
set "SERVICE_DIR=%~1"
cd /d "%SERVICE_DIR%" || exit /b 1

if not exist venv (
  echo Creating virtual environment for %SERVICE_DIR%...
  python -m venv venv
  if errorlevel 1 (
    set "_err=%errorlevel%"
    cd ..
    exit /b %_err%
  )
)

set "SERVICE_PYTHON=venv\Scripts\python.exe"
if not exist "%SERVICE_PYTHON%" (
  echo Missing Python executable at %SERVICE_DIR%\%SERVICE_PYTHON%
  cd ..
  exit /b 1
)

call "%SERVICE_PYTHON%" -c "import django" >nul 2>&1
if errorlevel 1 (
  echo Django not found for %SERVICE_DIR%. Installing requirements...
  call "%SERVICE_PYTHON%" -m pip install --upgrade pip
  if errorlevel 1 (
    set "_err=%errorlevel%"
    cd ..
    exit /b %_err%
  )

  if exist requirements\base.txt (
    call "%SERVICE_PYTHON%" -m pip install -r requirements\base.txt
    if errorlevel 1 (
      set "_err=%errorlevel%"
      cd ..
      exit /b %_err%
    )
  )

  if exist requirements\dev.txt (
    call "%SERVICE_PYTHON%" -m pip install -r requirements\dev.txt
    if errorlevel 1 (
      set "_err=%errorlevel%"
      cd ..
      exit /b %_err%
    )
  )
)

echo Applying migrations for %SERVICE_DIR%...
call "%SERVICE_PYTHON%" manage.py migrate
set "_err=%errorlevel%"
cd ..
exit /b %_err%

:seed_auth_admin_only
call :prepare_service auth-service
if errorlevel 1 exit /b 1
cd auth-service || exit /b 1
venv\Scripts\python.exe manage.py shell -c "from apps.authentication.services import ensure_default_roles,hash_password,set_user_roles; from apps.authentication.models import AuthUser; ensure_default_roles(); admin,_=AuthUser.objects.get_or_create(email='admin@gmail.local', defaults={'password_hash':hash_password('Admin@123'),'is_active':True}); set_user_roles(admin,['admin']); print('AUTH READY admin_id=',admin.id)"
set _err=%errorlevel%
cd ..
exit /b %_err%

:seed_housing
call :prepare_service housing-service
if errorlevel 1 exit /b 1
cd housing-service || exit /b 1
venv\Scripts\python.exe manage.py shell < ..\scripts\seed_housing_units.py
set _err=%errorlevel%
cd ..
exit /b %_err%

:sync_search
call :prepare_service search-service
if errorlevel 1 exit /b 1
cd search-service || exit /b 1
venv\Scripts\python.exe manage.py shell < ..\scripts\sync_search_index.py
set _err=%errorlevel%
cd ..
exit /b %_err%

:failed
echo.
echo Seed process failed. Review logs above.
pause
exit /b 1
