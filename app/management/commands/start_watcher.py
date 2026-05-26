from django.core.management.base import BaseCommand
from django.conf import settings
from pathlib import Path
from app.utils.folder_watcher import start_watcher

class Command(BaseCommand):
    help = 'Starts the folder watcher to auto-ingest CSV/Excel/JSON files from a directory'

    def handle(self, *args, **options):
        # Honour settings.WATCHED_INBOX_DIR; fall back to BASE_DIR / 'watched_inbox'
        watch_dir = getattr(settings, 'WATCHED_INBOX_DIR', Path(settings.BASE_DIR) / 'watched_inbox')
        watch_dir = str(watch_dir)          # watchdog needs a plain string path

        # Create the directory if it doesn't exist yet
        import os
        os.makedirs(watch_dir, exist_ok=True)

        self.stdout.write(self.style.SUCCESS(
            f'[DATA_PRO] Folder watcher started — monitoring: {watch_dir}'
        ))
        self.stdout.write('Drop CSV / Excel / JSON files into that folder to auto-ingest them.')
        self.stdout.write('Press Ctrl+C to stop.\n')

        start_watcher(watch_dir)

