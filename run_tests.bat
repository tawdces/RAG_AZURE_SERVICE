@echo off
REM Local test runner script for Windows

echo Running tests locally...
pytest tests/ -v --cov=src --cov-report=html --cov-report=term

echo.
echo Test results summary:
echo =====================
echo HTML coverage report available at: htmlcov\index.html
echo Opening coverage report...
start htmlcov\index.html
