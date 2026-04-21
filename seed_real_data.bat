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
echo - Admin account: admin@massa.local / Admin@12345
echo - Seeded housing titles now use prefix: UniNest
echo - Search index is refreshed from seeded housing units
pause
exit /b 0

:seed_auth_admin_only
cd auth-service || exit /b 1
python manage.py shell -c "from apps.authentication.services import ensure_default_roles,hash_password,set_user_roles; from apps.authentication.models import AuthUser; ensure_default_roles(); admin,_=AuthUser.objects.get_or_create(email='admin@massa.local', defaults={'password_hash':hash_password('Admin@12345'),'is_active':True}); set_user_roles(admin,['admin']); print('AUTH READY admin_id=',admin.id)"
set _err=%errorlevel%
cd ..
exit /b %_err%

:seed_housing
cd housing-service || exit /b 1
python manage.py shell < ..\scripts\seed_housing_units.py
set _err=%errorlevel%
cd ..
exit /b %_err%

:sync_search
cd search-service || exit /b 1
python manage.py shell < ..\scripts\sync_search_index.py
set _err=%errorlevel%
cd ..
exit /b %_err%

:failed
echo.
echo Seed process failed. Review logs above.
pause
exit /b 1
