"""
file_parser.py — Excel and JSON file parser for DataPro Full-Stack backend.
Supports: .xlsx, .xls, .xlsm (via openpyxl/xlrd), .json
Returns: list of dicts (rows) + list of column names
"""

import os
import re
import json
import logging
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

HEADER_SCAN_ROWS     = 10
MIN_VALID_COLS       = 2
MIN_VALID_ROWS       = 1
MIN_HEADER_FILL      = 0.35
_UNNAMED = re.compile(r'^unnamed[:\s_]\s*\d*', re.IGNORECASE)


# ── Public entry point ────────────────────────────────────────────────────────

def parse_file(file_path: str) -> tuple[list[str], list[dict]]:
    """
    Parse an uploaded file.

    Returns
    -------
    (columns, rows)
        columns : list[str]   — header names
        rows    : list[dict]  — each dict maps column → value
    """
    ext = os.path.splitext(file_path)[1].lower()
    logger.info("parse_file: ext=%s  path=%s", ext, file_path)

    try:
        if ext in ('.xlsx', '.xls', '.xlsm', '.xlsb'):
            df = _parse_excel(file_path)
        elif ext == '.json':
            df = _parse_json(file_path)
        else:
            raise ValueError(
                f"Unsupported file type '{ext}'. "
                "Please upload .xlsx, .xls, .xlsm, or .json"
            )
    except ValueError:
        raise
    except Exception as exc:
        logger.exception("Unexpected error in parse_file: %s", exc)
        raise ValueError(f"Failed to parse file: {exc}") from exc

    # Sanitise column names
    df.columns = _clean_columns(df.columns)

    columns = list(df.columns)
    
    # Use pandas to_json to handle Timestamp/NaN/inf properly, then parse back to list of dicts
    rows_json = df.to_json(orient='records', date_format='iso')
    rows = json.loads(rows_json)
    
    return columns, rows


# ── Excel ─────────────────────────────────────────────────────────────────────

def _parse_excel(file_path: str) -> pd.DataFrame:
    try:
        raw_sheets: dict = pd.read_excel(
            file_path, sheet_name=None, header=None, dtype=object
        )
    except Exception as exc:
        raise ValueError(f"Cannot open Excel file: {exc}") from exc

    if not raw_sheets:
        raise ValueError("Excel workbook contains no sheets.")

    valid_frames = []

    for sheet_name, raw_df in raw_sheets.items():
        if raw_df.empty or raw_df.shape[0] < 2:
            continue

        raw_df = (raw_df
                  .dropna(how='all')
                  .dropna(axis=1, how='all')
                  .reset_index(drop=True))

        if raw_df.empty:
            continue

        header_row = _detect_header(raw_df)

        try:
            df: pd.DataFrame = pd.read_excel(
                file_path, sheet_name=sheet_name, header=header_row, dtype=object
            )
        except Exception:
            continue

        df = df.dropna(how='all').dropna(axis=1, how='all').reset_index(drop=True)

        # Coerce numeric columns
        for col in df.columns:
            try:
                converted   = pd.to_numeric(df[col], errors='coerce')
                orig_nulls  = df[col].isna().sum()
                new_nulls   = converted.isna().sum()
                if new_nulls == orig_nulls:
                    df[col] = converted
            except Exception:
                pass

        if not _is_valid_sheet(df):
            continue

        if len(raw_sheets) > 1:
            df.insert(0, '_sheet', sheet_name)

        valid_frames.append(df)

    if not valid_frames:
        raise ValueError("No usable data sheets found in the workbook.")

    if len(valid_frames) == 1:
        return valid_frames[0].drop(columns=['_sheet'], errors='ignore')

    return pd.concat(valid_frames, ignore_index=True, sort=False)


def _detect_header(raw_df: pd.DataFrame) -> int:
    n_cols = raw_df.shape[1]
    for i in range(min(HEADER_SCAN_ROWS, len(raw_df))):
        row = raw_df.iloc[i]
        good = sum(1 for c in row if _is_label(c))
        if good / n_cols >= MIN_HEADER_FILL:
            return i
    return 0


def _is_label(cell) -> bool:
    if cell is None or (isinstance(cell, float) and np.isnan(cell)):
        return False
    s = str(cell).strip()
    if not s or len(s) > 80:
        return False
    try:
        float(s)
        return False
    except ValueError:
        return True


def _is_valid_sheet(df: pd.DataFrame) -> bool:
    if df.empty:
        return False
    if df.dropna(axis=1, how='all').shape[1] < MIN_VALID_COLS:
        return False
    if df.dropna(how='all').shape[0] < MIN_VALID_ROWS:
        return False
    return True


# ── JSON ──────────────────────────────────────────────────────────────────────

def _parse_json(file_path: str) -> pd.DataFrame:
    with open(file_path, 'r', encoding='utf-8') as f:
        raw = json.load(f)

    if isinstance(raw, list) and raw:
        df = pd.DataFrame(raw)
    elif isinstance(raw, dict):
        # Try common orientations
        for orient in ('records', 'split', 'index', 'columns', 'values'):
            try:
                df = pd.read_json(file_path, orient=orient)
                if not df.empty:
                    return df
            except Exception:
                continue
        raise ValueError("Cannot parse JSON structure.")
    else:
        raise ValueError("JSON must be a non-empty array of objects or a pandas-compatible dict.")

    if df.empty:
        raise ValueError("JSON file produced an empty table.")

    return df


# ── Column name cleaning ──────────────────────────────────────────────────────

def _clean_columns(columns) -> list:
    raw = []
    for col in columns:
        if isinstance(col, tuple):
            parts = [str(p).strip() for p in col
                     if str(p).strip() and not _UNNAMED.match(str(p).strip())]
            col = '_'.join(parts) if parts else ''
        else:
            col = str(col)

        col = col.strip().lower()
        col = re.sub(r'[^a-z0-9]+', '_', col).strip('_')
        if not col or _UNNAMED.match(col) or col == 'nan':
            col = ''
        raw.append(col)

    seen: dict = {}
    result = []
    for idx, name in enumerate(raw):
        if not name:
            name = f'col_{idx}'
        if name in seen:
            seen[name] += 1
            result.append(f'{name}_{seen[name]}')
        else:
            seen[name] = 0
            result.append(name)

    return result
