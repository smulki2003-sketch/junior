@echo off
setlocal

echo ============================
echo SYNC SEARCH INDEX (UniNest)
echo ============================

cd search-service || exit /b 1
python manage.py shell < ..\scripts\sync_search_index.py
set _err=%errorlevel%
cd ..

if not "%_err%"=="0" (
  echo Search sync failed.
  pause
  exit /b %_err%
)

echo Search sync completed successfully.
pause
exit /b 0
