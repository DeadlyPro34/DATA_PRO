import csv
import io
import pandas as pd
import numpy as np
from celery import shared_task
from django.db import transaction
from django.conf import settings
from .models import CSVDataset, DataPoint, Team, UploadedFile, CleanedDataset
from .signals import broadcast_team_update
from app.utils.file_parser import parse_file
from app.utils.data_cleaner import clean_dataframe

@shared_task
def process_csv_upload(csv_dataset_id, file_data_str, team_id):
    try:
        csv_dataset = CSVDataset.objects.get(id=csv_dataset_id)
        team = Team.objects.get(id=team_id)
    except (CSVDataset.DoesNotExist, Team.DoesNotExist):
        return "Dataset or Team not found"

    csv_dataset.status = 'processing'
    csv_dataset.save()

    try:
        csv_data = csv.reader(io.StringIO(file_data_str))
        datapoints_to_create = []
        imported_count = 0
        skipped_count = 0

        for row in csv_data:
            if not row:
                continue

            label = row[0].strip()
            if not label:
                continue

            if len(row) > 1:
                val_str = row[1].strip()
                # Remove common numeric formatting characters like commas
                cleaned_val = ''.join(c for c in val_str if c.isdigit() or c == '.')
                if cleaned_val:
                    try:
                        value = float(cleaned_val)
                        datapoints_to_create.append(DataPoint(
                            label=label,
                            value=value,
                            team=team,
                            csv_file=csv_dataset
                        ))
                        imported_count += 1
                    except ValueError:
                        skipped_count += 1
                else:
                    skipped_count += 1
            else:
                skipped_count += 1

            # Save in chunks of 500
            if len(datapoints_to_create) >= 500:
                with transaction.atomic():
                    DataPoint.objects.bulk_create(datapoints_to_create)
                datapoints_to_create = []

        if datapoints_to_create:
            with transaction.atomic():
                DataPoint.objects.bulk_create(datapoints_to_create)

        csv_dataset.imported_count = imported_count
        csv_dataset.skipped_count = skipped_count
        csv_dataset.status = 'done'
        csv_dataset.save()

        # Trigger real-time WebSocket dashboard/analytics updates
        broadcast_team_update(team)

        return f"Completed: {imported_count} imported, {skipped_count} skipped"
    except Exception as e:
        csv_dataset.status = 'failed'
        csv_dataset.save()
        return f"Failed: {str(e)}"


@shared_task
def process_csv_delete(csv_id, team_id):
    try:
        team = Team.objects.get(id=team_id)
    except Team.DoesNotExist:
        return "Team not found"

    try:
        # Perform optimized direct bulk deletion of children to avoid Django's cascade overhead in Python
        DataPoint.objects.filter(csv_file_id=csv_id).delete()
        # Delete the dataset object itself
        CSVDataset.objects.filter(id=csv_id, team=team).delete()

        # Trigger WebSocket update to refresh UI stats and charts for all connected team members
        broadcast_team_update(team)
        return f"Successfully deleted CSV {csv_id} and all related records."
    except Exception as e:
        return f"Failed to delete CSV {csv_id}: {str(e)}"


@shared_task
def process_uploaded_file(uploaded_file_id):
    try:
        uploaded_file = UploadedFile.objects.get(id=uploaded_file_id)
    except UploadedFile.DoesNotExist:
        return "UploadedFile not found"
        
    uploaded_file.status = 'processing'
    uploaded_file.save()
    
    try:
        # Open and parse the file
        uploaded_file.file.open('rb')
        df = parse_file(uploaded_file.file, uploaded_file.file_type)
        uploaded_file.file.close()
        
        row_count = len(df)
        column_count = len(df.columns)
        
        if row_count > 10000:
            chunks = np.array_split(df, (row_count // 10000) + 1)
            cleaned_chunks = []
            combined_log = []
            for chunk in chunks:
                c_df, log = clean_dataframe(chunk)
                cleaned_chunks.append(c_df)
                combined_log.extend(log)
            cleaned_df = pd.concat(cleaned_chunks, ignore_index=True)
            # Deduplicate logs
            seen = set()
            cleaning_log = []
            for item in combined_log:
                if item not in seen:
                    seen.add(item)
                    cleaning_log.append(item)
        else:
            cleaned_df, cleaning_log = clean_dataframe(df)
            
        # Standardize DataFrame rows for JSON (replace NaN/NaT with None so JSON serialization doesn't crash)
        cleaned_df = cleaned_df.replace({np.nan: None})
        
        # Prepare columns and rows
        columns = list(cleaned_df.columns)
        rows = cleaned_df.to_dict(orient='records')
        
        # Save to CleanedDataset
        cleaned_dataset, created = CleanedDataset.objects.update_or_create(
            uploaded_file=uploaded_file,
            defaults={
                'columns': columns,
                'rows': rows,
                'cleaning_log': cleaning_log
            }
        )
        
        # Generate summary
        ai_summary = ""
        openai_key = getattr(settings, 'OPENAI_API_KEY', '')
        if openai_key:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=openai_key)
                numeric_cols = [col for col in cleaned_df.columns if np.issubdtype(cleaned_df[col].dtype, np.number)]
                prompt = (
                    f"Provide a 3-5 sentence plain English summary of the following dataset:\n"
                    f"Original filename: {uploaded_file.original_filename}\n"
                    f"Column names: {', '.join(columns)}\n"
                    f"Row count: {row_count}\n"
                    f"Column count: {column_count}\n"
                )
                if numeric_cols:
                    prompt += "Numeric columns stats:\n"
                    for col in numeric_cols[:5]:
                        # Handle case where column contains None
                        col_vals = cleaned_df[col].dropna() if hasattr(cleaned_df[col], 'dropna') else [x for x in cleaned_df[col] if x is not None]
                        if len(col_vals) > 0:
                            prompt += f"- {col}: min={min(col_vals)}, max={max(col_vals)}\n"
                
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful data analyst. Write a concise, 3-5 sentence plain English summary/insights on the dataset."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=250,
                    temperature=0.7
                )
                ai_summary = response.choices[0].message.content.strip()
            except Exception as e:
                ai_summary = generate_fallback_summary(cleaned_df, columns, row_count, column_count)
        else:
            ai_summary = generate_fallback_summary(cleaned_df, columns, row_count, column_count)
            
        uploaded_file.row_count = row_count
        uploaded_file.column_count = column_count
        uploaded_file.ai_summary = ai_summary
        uploaded_file.status = 'done'
        uploaded_file.save()
        
        return f"Cleaned and summarized {uploaded_file.original_filename} successfully."
        
    except Exception as e:
        uploaded_file.status = 'failed'
        uploaded_file.ai_summary = f"Error processing file: {str(e)}"
        uploaded_file.save()
        return f"Failed to process {uploaded_file_id}: {str(e)}"


def generate_fallback_summary(df, columns, row_count, column_count):
    numeric_cols = []
    for col in columns:
        if col in df.columns and np.issubdtype(df[col].dtype, np.number):
            numeric_cols.append(col)
            
    summary = f"The dataset was successfully loaded with {row_count} rows and {column_count} columns. "
    summary += f"The detected features are: {', '.join(columns)}. "
    if numeric_cols:
        summary += f"Key numeric fields include {', '.join(numeric_cols[:3])}. "
        ranges = []
        for col in numeric_cols[:3]:
            non_null = df[col].dropna() if hasattr(df[col], 'dropna') else [x for x in df[col] if x is not None]
            if len(non_null) > 0:
                ranges.append(f"'{col}' (range: {min(non_null)} to {max(non_null)})")
        if ranges:
            summary += f"Notable ranges are: {', '.join(ranges)}."
    else:
        summary += "The columns consist primarily of categorical or text-based values."
    return summary
