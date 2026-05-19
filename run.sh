#!/bin/bash
echo "Starting Data Pro..."
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Please run python -m venv venv and pip install -r requirements.txt first."
    exit 1
fi
source venv/bin/activate
echo "Running migrations..."
python manage.py makemigrations
python manage.py migrate
echo "Starting server..."
python manage.py runserver
