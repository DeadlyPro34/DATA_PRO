import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

class DataCleaningEngine:
    """
    Modular engine for applying cleaning operations sequentially.
    """

    def apply_pipeline(self, df: pd.DataFrame, pipeline: list) -> tuple[pd.DataFrame, list]:
        """
        Executes a sequence of cleaning operations.
        pipeline: list of dicts. Example:
        [
            {"operation": "remove_duplicates", "params": {}},
            {"operation": "fill_nulls", "params": {"column": "sales", "strategy": "mean"}},
            ...
        ]
        """
        logs = []
        df_clean = df.copy()

        for step in pipeline:
            op_name = step.get('operation')
            params = step.get('params', {})
            
            method = getattr(self, op_name, None)
            if method:
                try:
                    df_clean, log_msg = method(df_clean, **params)
                    if log_msg:
                        logs.append(log_msg)
                except Exception as e:
                    logger.error(f"Error in cleaning step {op_name}: {str(e)}")
                    logs.append(f"❌ Failed to apply '{op_name}': {str(e)}")
            else:
                logs.append(f"⚠️ Unknown operation: {op_name}")

        return df_clean, logs

    # ==========================================
    # BASIC CLEANING
    # ==========================================

    def remove_duplicates(self, df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
        initial_count = len(df)
        df.drop_duplicates(inplace=True)
        dropped = initial_count - len(df)
        if dropped > 0:
            return df, f"Removed {dropped} duplicate rows."
        return df, None

    def trim_whitespace(self, df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
        str_cols = df.select_dtypes(include=['object', 'string']).columns
        if not str_cols.empty:
            for c in str_cols:
                # Only trim strings, leave non-strings (like NaN/floats in mixed columns) alone
                df[c] = df[c].apply(lambda x: x.strip() if isinstance(x, str) else x)
            return df, f"Trimmed whitespace in {len(str_cols)} text columns."
        return df, None

    def remove_empty_rows(self, df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
        initial_count = len(df)
        df.dropna(how='all', inplace=True)
        dropped = initial_count - len(df)
        if dropped > 0:
            return df, f"Removed {dropped} completely empty rows."
        return df, None

    def remove_empty_columns(self, df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
        initial_count = len(df.columns)
        df.dropna(axis=1, how='all', inplace=True)
        dropped = initial_count - len(df.columns)
        if dropped > 0:
            return df, f"Removed {dropped} completely empty columns."
        return df, None

    # ==========================================
    # NULL HANDLING
    # ==========================================

    def fill_nulls(self, df: pd.DataFrame, column: str, strategy: str, custom_value=None) -> tuple[pd.DataFrame, str]:
        if column not in df.columns:
            return df, f"⚠️ Column '{column}' not found for fill_nulls."
            
        initial_nulls = df[column].isnull().sum()
        if initial_nulls == 0:
            return df, f"No missing values in '{column}' to fill."

        if strategy == 'mean':
            if pd.api.types.is_numeric_dtype(df[column]):
                val = df[column].mean()
                df[column] = df[column].fillna(val)
                return df, f"Filled {initial_nulls} nulls in '{column}' with mean ({val:.2f})."
            else:
                return df, f"⚠️ Cannot use 'mean' on non-numeric column '{column}'."
                
        elif strategy == 'median':
            if pd.api.types.is_numeric_dtype(df[column]):
                val = df[column].median()
                df[column] = df[column].fillna(val)
                return df, f"Filled {initial_nulls} nulls in '{column}' with median ({val:.2f})."
            else:
                return df, f"⚠️ Cannot use 'median' on non-numeric column '{column}'."
                
        elif strategy == 'mode':
            mode_series = df[column].mode()
            if not mode_series.empty:
                val = mode_series.iloc[0]
                df[column] = df[column].fillna(val)
                return df, f"Filled {initial_nulls} nulls in '{column}' with mode ('{val}')."
            return df, f"⚠️ Could not calculate mode for '{column}'."
            
        elif strategy == 'custom':
            if custom_value is not None:
                # Attempt to cast custom_value to numeric if column is numeric
                if pd.api.types.is_numeric_dtype(df[column]):
                    try:
                        custom_value = float(custom_value)
                    except ValueError:
                        pass
                df[column] = df[column].fillna(custom_value)
                return df, f"Filled {initial_nulls} nulls in '{column}' with custom value ('{custom_value}')."
            return df, f"⚠️ Custom value missing for fill_nulls."
            
        return df, f"⚠️ Unknown fill strategy '{strategy}'."

    def drop_null_rows(self, df: pd.DataFrame, columns: list = None) -> tuple[pd.DataFrame, str]:
        initial_count = len(df)
        if columns:
            df.dropna(subset=columns, inplace=True)
            msg = f"Dropped {initial_count - len(df)} rows with nulls in columns: {', '.join(columns)}."
        else:
            df.dropna(how='any', inplace=True)
            msg = f"Dropped {initial_count - len(df)} rows containing any nulls."
            
        if initial_count - len(df) > 0:
            return df, msg
        return df, None

    # ==========================================
    # DATA TYPE CLEANING
    # ==========================================

    def coerce_numeric(self, df: pd.DataFrame, column: str = None) -> tuple[pd.DataFrame, str]:
        cols_to_convert = [column] if column else df.columns
        converted_count = 0
        
        for c in cols_to_convert:
            if c not in df.columns:
                continue
            if df[c].dtype == object or str(df[c].dtype).startswith('string'):
                try:
                    # pd.to_numeric safely converts strings to numbers, replacing invalid with NaN if coerce
                    s_converted = pd.to_numeric(df[c], errors='coerce')
                    # only replace if we actually got some valid numbers (don't convert pure text cols to all NaNs)
                    # if more than 50% are valid numbers, accept the conversion
                    valid_ratio = s_converted.notna().mean()
                    if valid_ratio > 0.1: # if even 10% is numeric, we might want it. Let's say 50% for safety.
                        df[c] = s_converted
                        converted_count += 1
                except Exception:
                    pass
                    
        if converted_count > 0:
            return df, f"Coerced {converted_count} column(s) to numeric."
        return df, None

    # ==========================================
    # TEXT CLEANING
    # ==========================================

    def lowercase(self, df: pd.DataFrame, column: str) -> tuple[pd.DataFrame, str]:
        if column in df.columns and (df[column].dtype == object or str(df[column].dtype).startswith('string')):
            df[column] = df[column].apply(lambda x: x.lower() if isinstance(x, str) else x)
            return df, f"Converted '{column}' to lowercase."
        return df, f"⚠️ Column '{column}' is not a text column."

    def uppercase(self, df: pd.DataFrame, column: str) -> tuple[pd.DataFrame, str]:
        if column in df.columns and (df[column].dtype == object or str(df[column].dtype).startswith('string')):
            df[column] = df[column].apply(lambda x: x.upper() if isinstance(x, str) else x)
            return df, f"Converted '{column}' to uppercase."
        return df, f"⚠️ Column '{column}' is not a text column."

    def title_case(self, df: pd.DataFrame, column: str) -> tuple[pd.DataFrame, str]:
        if column in df.columns and (df[column].dtype == object or str(df[column].dtype).startswith('string')):
            df[column] = df[column].apply(lambda x: x.title() if isinstance(x, str) else x)
            return df, f"Converted '{column}' to title case."
        return df, f"⚠️ Column '{column}' is not a text column."

    def remove_special_chars(self, df: pd.DataFrame, column: str) -> tuple[pd.DataFrame, str]:
        if column in df.columns and (df[column].dtype == object or str(df[column].dtype).startswith('string')):
            # Keeps alphanumeric and spaces
            df[column] = df[column].astype(str).str.replace(r'[^a-zA-Z0-9\s]', '', regex=True)
            return df, f"Removed special characters from '{column}'."
        return df, f"⚠️ Column '{column}' is not a text column."

    # ==========================================
    # QUALITY & ADVANCED
    # ==========================================

    def remove_outliers(self, df: pd.DataFrame, column: str) -> tuple[pd.DataFrame, str]:
        if column in df.columns and pd.api.types.is_numeric_dtype(df[column]):
            initial_count = len(df)
            Q1 = df[column].quantile(0.25)
            Q3 = df[column].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            df = df[(df[column] >= lower_bound) & (df[column] <= upper_bound)]
            dropped = initial_count - len(df)
            return df, f"Removed {dropped} outliers from '{column}' (IQR method)."
        return df, f"⚠️ Column '{column}' is not numeric, cannot remove outliers."
