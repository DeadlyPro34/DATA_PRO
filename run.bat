@echo off
echo Starting Data Pro...
if not exist "venv\Scripts\activate.bat" (
    echo Virtual environment not found. Please run python -m venv venv and pip install -r requirements.txt first.
    exit /b 1
)
call venv\Scripts\activate.bat
echo Running migrations...
python manage.py makemigrations
python manage.py migrate
echo Starting server...
python manage.py runserver
