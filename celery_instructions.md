# Starting Celery and Redis

## Install Redis
- **Windows**: Use WSL (Windows Subsystem for Linux) and run `sudo apt install redis-server`, then `sudo service redis-server start`.
- **Mac**: `brew install redis` and `brew services start redis`
- **Linux**: `sudo apt install redis-server` and `sudo systemctl start redis`

## Start Django Server
```bash
python manage.py runserver
```

## Start Celery Worker
```bash
# On Windows, you might need to use Eventlet/Gevent or run it via WSL
celery -A data_pro_project worker -l INFO --pool=solo
```

## Start Celery Beat
```bash
celery -A data_pro_project beat -l INFO
```

**Note**: Make sure `USE_CELERY = True` in `settings.py` before starting!
