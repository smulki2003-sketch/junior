@echo off
setlocal EnableExtensions

set "ROOT=%~dp0"

echo ==========================================
echo Reset all service databases (flush data)
echo Root: %ROOT%
echo ==========================================

call :reset_service "api-gateway" || goto :failed
call :reset_service "auth-service" || goto :failed
call :reset_service "user-service" || goto :failed
call :reset_service "housing-service" || goto :failed
call :reset_service "booking-service" || goto :failed
call :reset_service "payment-service" || goto :failed
call :reset_service "moderation-service" || goto :failed
call :reset_service "notification-service" || goto :failed
call :reset_service "admin-service" || goto :failed
call :reset_service "reporting-service" || goto :failed
call :reset_service "ai-service" || goto :failed
call :reset_service "roommate-service" || goto :failed
call :reset_service "search-service" || goto :failed

echo.
echo All databases were reset successfully.
exit /b 0

:reset_service
set "SERVICE=%~1"
echo.
echo [RESET] %SERVICE%
pushd "%ROOT%%SERVICE%" >nul || (
  echo [ERROR] Cannot open folder: %SERVICE%
  exit /b 1
)

if exist "venv\Scripts\python.exe" (
  set "PYTHON_BIN=venv\Scripts\python.exe"
) else (
  set "PYTHON_BIN=python"
)

%PYTHON_BIN% manage.py migrate --noinput
if errorlevel 1 (
  popd >nul
  echo [ERROR] migrate failed in %SERVICE%
  exit /b 1
)

%PYTHON_BIN% manage.py flush --noinput
if errorlevel 1 (
  popd >nul
  echo [ERROR] flush failed in %SERVICE%
  exit /b 1
)

popd >nul
exit /b 0

:failed
echo.
echo Reset aborted due to an error.
exit /b 1
