@echo off
setlocal

echo ============================
echo SEED HOUSING (UniNest Data)
echo ============================

call :prepare_housing_service
if errorlevel 1 goto :failed

cd housing-service || exit /b 1
venv\Scripts\python.exe manage.py shell < ..\scripts\seed_housing_units.py
set _err=%errorlevel%
cd ..

if not "%_err%"=="0" (
  goto :failed
)

echo Housing seed completed successfully.
pause
exit /b 0

:prepare_housing_service
cd /d housing-service || exit /b 1

if not exist venv (
  echo Creating virtual environment for housing-service...
  python -m venv venv
  if errorlevel 1 (
    set "_err=%errorlevel%"
    cd ..
    exit /b %_err%
  )
)

set "SERVICE_PYTHON=venv\Scripts\python.exe"
if not exist "%SERVICE_PYTHON%" (
  echo Missing Python executable at housing-service\%SERVICE_PYTHON%
  cd ..
  exit /b 1
)

call "%SERVICE_PYTHON%" -c "import django" >nul 2>&1
if errorlevel 1 (
  echo Django not found for housing-service. Installing requirements...
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

echo Applying migrations for housing-service...
call "%SERVICE_PYTHON%" manage.py migrate
set "_err=%errorlevel%"
cd ..
exit /b %_err%

:failed
echo Housing seed failed. Review logs above.
pause
exit /b 1
