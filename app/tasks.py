from celery import shared_task
from django.conf import settings
from app.models import UploadedFile, CleanedDataset
from app.utils.file_parser import parse_file
from app.utils.data_cleaner import clean_dataframe
from app.utils.ai_insights import build_insights_summary
import pandas as pd
import json

@shared_task
def process_uploaded_file_task(file_id, options=None):
    try:
        uploaded_file = UploadedFile.objects.get(id=file_id)
        
        # In Django, file fields must be accessed correctly. 
        # But for file_parser it needs a path or file object.
        # file_parser.py takes a file_path string.
        file_path = uploaded_file.file.path
        df = parse_file(file_path)
        
        # Enforce maximum 5000 rows for safety
        if len(df) > 5000:
            df = df.head(5000)
            
        cleaned_df, cleaning_result = clean_dataframe(df, options=options)
        
        uploaded_file.row_count = len(cleaned_df)
        uploaded_file.column_count = len(cleaned_df.columns)
        uploaded_file.save()
        
        ai_insights_data = build_insights_summary(cleaned_df, cleaning_result['health_report'])

        # Serialize safely via pandas
        # Serialize safely via pandas
        safe_stats = json.loads(pd.Series(cleaning_result['stats']).to_json()) if cleaning_result['stats'] else {}
        
        # Default cleaning options if none provided
        default_options = {
            'remove_duplicates': True,
            'normalize_headers': True,
            'trim_whitespace': True,
            'remove_empty_rows': True,
            'remove_empty_columns': True,
            'coerce_numeric': True,
        }
        
        # If recleaning, dataset exists. If new upload, we create.
        dataset, created = CleanedDataset.objects.get_or_create(
            uploaded_file=uploaded_file,
            defaults={
                'columns': list(cleaned_df.columns),
                'rows': None,
                'cleaning_log': cleaning_result['log'],
                'stats': safe_stats,
                'raw_snapshot': cleaning_result['raw_snapshot'],
                'raw_columns': cleaning_result['raw_columns'],
                'health_report': cleaning_result['health_report'],
                'quality_score': cleaning_result['quality_score'],
                'cleaning_actions': cleaning_result['actions'],
                'before_after': cleaning_result['before_after'],
                'ai_insights': ai_insights_data,
                'cell_annotations': cleaning_result['cell_annotations'],
                'cleaning_options': options or default_options,
            }
        )
        
        if not created:
            dataset.columns = list(cleaned_df.columns)
            dataset.rows = None
            dataset.cleaning_log = cleaning_result['log']
            dataset.stats = safe_stats
            dataset.raw_snapshot = cleaning_result['raw_snapshot']
            dataset.raw_columns = cleaning_result['raw_columns']
            dataset.health_report = cleaning_result['health_report']
            dataset.quality_score = cleaning_result['quality_score']
            dataset.cleaning_actions = cleaning_result['actions']
            dataset.before_after = cleaning_result['before_after']
            dataset.ai_insights = ai_insights_data
            dataset.cell_annotations = cleaning_result['cell_annotations']
            dataset.cleaning_options = options or default_options
            dataset.save()
            
        # Save to Parquet
        from app.utils.parquet_helpers import save_dataframe_to_parquet
        save_dataframe_to_parquet(cleaned_df, dataset)

        # Save all sheets for multi-sheet viewer (Excel only)
        if uploaded_file.file_type in ('xlsx', 'xls', 'xlsm', 'xlsb'):
            from app.utils.file_parser import parse_excel_all_sheets
            try:
                all_sheets = parse_excel_all_sheets(file_path)
                dataset.all_sheets_data = all_sheets
                dataset.save(update_fields=['all_sheets_data'])
                print(f'[Sheets] Saved {len(all_sheets)} sheets for file {file_id}')
            except Exception as e:
                print(f'[Sheets] Could not parse all sheets: {e}')

        return {'status': 'success', 'file_id': file_id}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {'status': 'error', 'error': str(e)}

@shared_task
def scan_watched_inbox():
    """Celery Beat task — scans watched_inbox and ingests any new files."""
    import os
    from django.conf import settings
    from django.core.files import File
    from django.contrib.auth.models import User
    from app.models import UploadedFile

    watch_dir = str(getattr(
        settings, 'WATCHED_INBOX_DIR',
        os.path.join(settings.BASE_DIR, 'watched_inbox')
    ))
    os.makedirs(watch_dir, exist_ok=True)

    allowed = {'.csv', '.xlsx', '.xls', '.xlsm', '.json'}
    system_user, _ = User.objects.get_or_create(
        username='system',
        defaults={'email': 'system@datapro.local'}
    )

    for filename in os.listdir(watch_dir):
        ext = os.path.splitext(filename)[1].lower()
        if ext not in allowed:
            continue
        file_path = os.path.join(watch_dir, filename)
        try:
            with open(file_path, 'rb') as f:
                uf = UploadedFile(
                    user=system_user,
                    original_filename=filename,
                    file_type=ext.lstrip('.'),
                    custom_name=f'Auto-Ingested {filename}',
                )
                uf.file.save(filename, File(f))
                uf.save()
            process_uploaded_file_task.delay(uf.id)
            os.remove(file_path)
            print(f'[Beat] Ingested and queued: {filename}')
        except Exception as e:
            print(f'[Beat] Error ingesting {filename}: {e}')
