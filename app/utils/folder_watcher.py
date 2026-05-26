import os
import time
import shutil
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from django.conf import settings
from django.core.files import File
from django.contrib.auth.models import User
from app.models import UploadedFile
from app.tasks import process_uploaded_file_task

class DatasetHandler(PatternMatchingEventHandler):
    patterns = ["*.csv", "*.xlsx", "*.xls", "*.xlsm", "*.json"]

    def __init__(self, watch_dir, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.watch_dir = watch_dir
        self.system_user, _ = User.objects.get_or_create(username='system', defaults={'email': 'system@example.com'})
        
        # Ensure uploads directory exists
        self.uploads_dir = os.path.join(settings.MEDIA_ROOT, 'uploads')
        os.makedirs(self.uploads_dir, exist_ok=True)

    def process_file(self, event):
        file_path = event.src_path
        filename = os.path.basename(file_path)
        print(f"New dataset detected: {filename}")
        
        # Wait a bit to ensure the file is completely written
        time.sleep(2)
        
        # We need to move it to the Django media/uploads directory so we can attach it to the model.
        # Alternatively, we can save it directly using Django's FileField.
        
        try:
            with open(file_path, 'rb') as f:
                uploaded_file = UploadedFile(
                    user=self.system_user,
                    original_filename=filename,
                    file_type=filename.split('.')[-1].lower(),
                    custom_name=f"Auto-Ingested {filename}"
                )
                uploaded_file.file.save(filename, File(f))
                uploaded_file.save()
            
            # Now trigger the celery task
            if getattr(settings, 'USE_CELERY', False):
                process_uploaded_file_task.delay(uploaded_file.id)
                print(f"Triggered celery task for {filename}")
            else:
                process_uploaded_file_task(uploaded_file.id)
                print(f"Processed synchronously for {filename}")
                
            # After successful processing (or triggering), remove the original dropped file
            try:
                os.remove(file_path)
                print(f"Removed original file {file_path}")
            except Exception as e:
                print(f"Warning: could not remove original file {file_path}: {e}")
                
        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")

    def on_created(self, event):
        self.process_file(event)

def start_watcher(watch_dir):
    os.makedirs(watch_dir, exist_ok=True)
    event_handler = DatasetHandler(watch_dir=watch_dir, ignore_directories=True)
    observer = Observer()
    observer.schedule(event_handler, watch_dir, recursive=False)
    observer.start()
    print(f"Started watching {watch_dir} for new datasets...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
