import pandas as pd
import pyarrow.parquet as pq
import pyarrow as pa
import os
from django.conf import settings

def save_dataframe_to_parquet(df, dataset):
    """
    Saves a Pandas DataFrame as a Parquet file and updates the dataset's parquet_path.
    """
    parquet_dir = os.path.join(settings.MEDIA_ROOT, 'parquet_data')
    os.makedirs(parquet_dir, exist_ok=True)
    
    file_path = os.path.join(parquet_dir, f'dataset_{dataset.id}.parquet')
    
    # Save to parquet
    table = pa.Table.from_pandas(df)
    pq.write_table(table, file_path)
    
    dataset.parquet_path = file_path
    dataset.rows = None # Clear out rows to save space in the DB
    dataset.save()
    
    return file_path

def get_dataframe(dataset):
    """
    Returns a Pandas DataFrame from the dataset's Parquet file.
    If the parquet file doesn't exist but rows exist in DB, returns DataFrame from rows.
    """
    if dataset.parquet_path and os.path.exists(dataset.parquet_path):
        table = pq.read_table(dataset.parquet_path)
        return table.to_pandas()
    elif dataset.rows:
        return pd.DataFrame(dataset.rows)
    else:
        return pd.DataFrame()
