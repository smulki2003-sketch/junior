@echo off
setlocal

echo ============================
echo SEED HOUSING (UniNest Data)
echo ============================

cd housing-service || exit /b 1
python manage.py shell < ..\scripts\seed_housing_units.py
set _err=%errorlevel%
cd ..

if not "%_err%"=="0" (
  echo Housing seed failed.
  pause
  exit /b %_err%
)

echo Housing seed completed successfully.
pause
exit /b 0
