from django.core.management.base import BaseCommand
from django.conf import settings
from app.utils.folder_watcher import start_watcher
import os

class Command(BaseCommand):
    help = 'Starts the folder watcher to auto-ingest datasets'

    def handle(self, *args, **options):
        watch_dir = os.path.join(settings.BASE_DIR, 'watched_inbox')
        self.stdout.write(self.style.SUCCESS(f'Starting folder watcher on {watch_dir}'))
        start_watcher(watch_dir)
