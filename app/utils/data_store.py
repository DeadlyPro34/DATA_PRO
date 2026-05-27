"""
data_store.py — Unified DataFrame persistence helper for DATA_PRO
=================================================================

Provides two simple functions:
  - save_dataframe(df, file_id)  → saves as Parquet, returns path string
  - get_dataframe(dataset)       → reads Parquet if available, else falls
                                   back to dataset.rows JSON

Uses pyarrow for Parquet I/O. No external AI / LLM dependencies.
"""

import os
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from django.conf import settings


def save_dataframe(df: pd.DataFrame, file_id: int) -> str:
    """
    Save a DataFrame as a Parquet file under media/parquet/{file_id}.parquet.

    Parameters
    ----------
    df      : cleaned pandas DataFrame to persist
    file_id : integer ID of the UploadedFile (used as filename)

    Returns
    -------
    str — absolute path to the saved .parquet file
    """
    parquet_dir = os.path.join(settings.MEDIA_ROOT, 'parquet')
    os.makedirs(parquet_dir, exist_ok=True)

    file_path = os.path.join(parquet_dir, f'{file_id}.parquet')

    table = pa.Table.from_pandas(df, preserve_index=False)
    pq.write_table(table, file_path)

    return file_path


def get_dataframe(dataset) -> pd.DataFrame:
    """
    Return a DataFrame for the given CleanedDataset instance.

    Priority:
      1. Read from dataset.parquet_path if the file exists on disk.
      2. Fall back to pd.DataFrame(dataset.rows) if rows are stored in DB.
      3. Return an empty DataFrame as a last resort.

    Parameters
    ----------
    dataset : CleanedDataset model instance

    Returns
    -------
    pd.DataFrame
    """
    if dataset.parquet_path and os.path.exists(dataset.parquet_path):
        table = pq.read_table(dataset.parquet_path)
        return table.to_pandas()

    if dataset.rows:
        return pd.DataFrame(dataset.rows)

    return pd.DataFrame()
