from celery import shared_task
from django.conf import settings
from app.models import UploadedFile, CleanedDataset
from app.utils.file_parser import parse_file
from app.utils.data_cleaner import clean_dataframe
from app.utils.ai_insights import generate_insights
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
        
        ai_insights_data = generate_insights(cleaned_df, cleaning_result['health_report'], cleaning_result['stats'])

        # Serialize safely via pandas
        safe_rows = json.loads(cleaned_df.to_json(orient='records', date_format='iso'))
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
                'rows': safe_rows,
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
            dataset.rows = safe_rows
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
            
        return {'status': 'success', 'file_id': file_id}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {'status': 'error', 'error': str(e)}
