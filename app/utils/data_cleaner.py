import pandas as pd
import numpy as np

def clean_dataframe(df):
    """
    Cleans a pandas DataFrame and returns the cleaned DataFrame and a log of actions.
    """
    log = []
    
    # 1. Normalize column names (strip whitespace, lowercase, replace spaces with underscores)
    original_cols = list(df.columns)
    df.columns = [str(c).strip().lower().replace(' ', '_') for c in df.columns]
    if original_cols != list(df.columns):
        log.append("Normalized column headers (lowercased, replaced spaces with underscores, stripped whitespace).")
    
    # 2. Strip whitespace from string columns
    str_cols = df.select_dtypes(include=['object']).columns
    for col in str_cols:
        try:
            df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)
        except Exception:
            pass
    if len(str_cols) > 0:
        log.append(f"Stripped leading/trailing whitespace from string columns.")
        
    # 3. Drop fully empty rows
    initial_rows = len(df)
    df.dropna(how='all', inplace=True)
    rows_dropped = initial_rows - len(df)
    if rows_dropped > 0:
        log.append(f"Dropped {rows_dropped} fully empty rows.")
        
    # 4. Remove duplicate rows
    initial_rows2 = len(df)
    df.drop_duplicates(inplace=True)
    dupes_dropped = initial_rows2 - len(df)
    if dupes_dropped > 0:
        log.append(f"Removed {dupes_dropped} duplicate rows.")
        
    # Generate simple stats
    stats = {}
    try:
        desc = df.describe(include='all').to_dict()
        for col, col_stats in desc.items():
            stats[col] = {k: v for k, v in col_stats.items() if pd.notna(v)}
    except Exception:
        pass
        
    if not log:
        log.append("No cleaning actions were necessary; the data looked good!")

    return df, log, stats
