import pandas as pd
import numpy as np

def clean_dataframe(df):
    """
    Cleans the given DataFrame according to the following logic:
    1. Drop fully empty rows and columns
    2. Normalize column headers (lowercase, replace spaces with underscores, strip non-alphanumeric chars except underscores)
    3. Strip whitespace from all string/object columns
    4. Remove duplicate rows
    5. Attempts to auto-cast columns to numeric where possible
    6. Fills missing numeric values with column mean
    7. Fills missing string values with "unknown"
    Returns (cleaned_df, cleaning_log)
    """
    # Work on a copy of the dataframe
    df = df.copy()
    cleaning_log = []
    
    # 1. Drop fully empty rows and columns
    initial_rows, initial_cols = df.shape
    df = df.dropna(how='all')
    dropped_rows = initial_rows - df.shape[0]
    if dropped_rows > 0:
        cleaning_log.append(f"Dropped {dropped_rows} fully empty row(s).")
        
    df = df.dropna(how='all', axis=1)
    dropped_cols = initial_cols - df.shape[1]
    if dropped_cols > 0:
        cleaning_log.append(f"Dropped {dropped_cols} fully empty column(s).")

    # 2. Normalize column headers
    old_columns = list(df.columns)
    new_columns = []
    renamed_count = 0
    for col in old_columns:
        # Stringify column header just in case it's not a string
        new_col = str(col).strip().lower().replace(' ', '_')
        # Remove any other non-alphanumeric chars except underscores
        new_col = ''.join(c for c in new_col if c.isalnum() or c == '_')
        if not new_col:
            new_col = f"column_{len(new_columns) + 1}"
        if new_col != col:
            renamed_count += 1
        new_columns.append(new_col)
    
    df.columns = new_columns
    if renamed_count > 0:
        cleaning_log.append(f"Normalized {renamed_count} column header(s).")

    # 3. Strip whitespace from all string columns
    for col in df.columns:
        if df[col].dtype == 'object':
            df[col] = df[col].apply(lambda x: x.strip() if isinstance(x, str) else x)

    # 4. Removes duplicate rows
    initial_rows = df.shape[0]
    df = df.drop_duplicates()
    duplicate_rows = initial_rows - df.shape[0]
    if duplicate_rows > 0:
        cleaning_log.append(f"Removed {duplicate_rows} duplicate row(s).")

    # 5. Attempts to auto-cast columns to numeric where possible, and fill missing values
    for col in df.columns:
        if df[col].dtype == 'object':
            try:
                # errors='coerce' turns non-convertible items to NaN
                converted = pd.to_numeric(df[col], errors='coerce')
                # If the ratio of non-NaN values is substantial, keep it
                valid_count = converted.notna().sum()
                if valid_count > 0 and (valid_count / len(converted)) > 0.5:
                    df[col] = converted
                    cleaning_log.append(f"Auto-cast column '{col}' to numeric.")
            except Exception:
                pass
        
        # 6 & 7. Fill missing values
        if np.issubdtype(df[col].dtype, np.number):
            null_count = df[col].isna().sum()
            if null_count > 0:
                mean_val = df[col].mean()
                if pd.isna(mean_val):
                    mean_val = 0
                df[col] = df[col].fillna(mean_val)
                cleaning_log.append(f"Filled {null_count} missing value(s) in numeric column '{col}' with column mean ({round(float(mean_val), 2)}).")
        else:
            null_count = df[col].isna().sum()
            if null_count > 0:
                df[col] = df[col].fillna("unknown")
                cleaning_log.append(f"Filled {null_count} missing value(s) in column '{col}' with 'unknown'.")

    return df, cleaning_log
