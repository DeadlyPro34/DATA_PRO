"""
data_cleaner.py — Production-grade DataFrame cleaning pipeline for DATA_PRO
============================================================================

Called by ``views.upload_file()`` immediately after ``parse_file()`` returns
a raw DataFrame.

Responsibility split with file_parser.py
-----------------------------------------
file_parser.py  handles:
    ✓ Reading files (CSV / Excel / JSON)
    ✓ Detecting the real header row in Excel
    ✓ Dropping fully-empty peripheral rows & columns (trim phase)
    ✓ Cleaning and deduplicating column names (for Excel sheets)
    ✓ Tagging rows with _sheet_name when multiple sheets are merged

data_cleaner.py handles:
    ✓ Re-applying column normalisation as a safety net (CSV / JSON
      may still have messy headers)
    ✓ Stripping whitespace from every string cell
    ✓ Dropping fully-empty rows that survived parsing
    ✓ Removing exact duplicate rows
    ✓ Type-coercing object columns to numeric where possible
    ✓ Computing per-column statistics (safe for JSON serialisation)
    ✓ Returning a human-readable cleaning log

Author: DATA_PRO
"""

import json
import logging
import re
from typing import Any, Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# Regex matching pandas-generated "Unnamed: N" labels
_UNNAMED_RE = re.compile(r'^unnamed[:\s_]\s*\d*', re.IGNORECASE)

# Columns that should be excluded from statistical analysis
_META_COLUMNS = {'_sheet_name'}


# ──────────────────────────────────────────────────────────────────────────────
# PUBLIC ENTRY POINT
# ──────────────────────────────────────────────────────────────────────────────

def clean_dataframe(
    df: pd.DataFrame,
    options: Optional[dict] = None,
) -> tuple[pd.DataFrame, dict]:
    """
    Clean *df* and return ``(cleaned_df, cleaning_result)``.

    Parameters
    ----------
    df : pd.DataFrame
        Raw DataFrame returned by ``parse_file()``.
    options : dict, optional
        Cleaning toggles. Keys (all bool, default True):
            remove_duplicates, normalize_headers, trim_whitespace,
            remove_empty_rows, remove_empty_columns, coerce_numeric.

    Returns
    -------
    cleaned_df : pd.DataFrame
        Fully cleaned DataFrame ready for JSON serialisation and storage.
    cleaning_result : dict
        Comprehensive cleaning result containing log, actions,
        health_report, quality_score, before_after, raw_snapshot,
        raw_columns, cell_annotations, and stats.
    """
    # Default options — all cleaning steps enabled
    opts: dict = {
        'remove_duplicates': True,
        'normalize_headers': True,
        'trim_whitespace': True,
        'remove_empty_rows': True,
        'remove_empty_columns': True,
        'coerce_numeric': True,
    }
    if options:
        opts.update(options)

    log: list[str] = []
    df = df.copy()   # never mutate the caller's object

    logger.info(
        "clean_dataframe start: %d rows × %d cols", len(df), df.shape[1]
    )

    # ── Step 0a: Compute health report on RAW data ───────────────────────────
    health_report = _compute_health_report(df)

    # ── Step 0b: Capture raw snapshot (first 200 rows) ───────────────────────
    raw_snapshot = _capture_raw_snapshot(df)
    raw_columns = [str(c) for c in df.columns.tolist()]

    # ── Step 0c: Identify duplicate row indices BEFORE cleaning ──────────────
    duplicate_mask = df.duplicated(keep='first')
    raw_duplicate_indices = [int(i) for i in duplicate_mask[duplicate_mask].index.tolist()[:200]]

    # Keep a copy of the raw data (first 200 rows) for annotation comparison
    raw_head = df.head(200).copy()

    # ── Step 1: Flatten MultiIndex columns ───────────────────────────────────
    # The Excel parser already flattens for Excel files, but CSV / JSON with
    # multi-level column structures may still arrive here with a MultiIndex.
    df, changed = _flatten_multiindex(df)
    if changed:
        log.append("Flattened multi-level column headers.")

    # ── Step 2: Normalise column names ───────────────────────────────────────
    # Safety net for CSV / JSON files whose headers were not pre-cleaned by
    # the parser.  Also catches anything the parser missed.
    if opts.get('normalize_headers', True):
        df, col_log = _normalise_columns(df)
        if col_log:
            log.append(col_log)

    # ── Step 3: Drop fully-empty rows ────────────────────────────────────────
    if opts.get('remove_empty_rows', True):
        before = len(df)
        df.dropna(how='all', inplace=True)
        df.reset_index(drop=True, inplace=True)
        dropped = before - len(df)
        if dropped:
            log.append(f"Dropped {dropped} fully-empty row(s).")

    # ── Step 4: Drop fully-empty columns ─────────────────────────────────────
    if opts.get('remove_empty_columns', True):
        before_cols = df.shape[1]
        df.dropna(axis=1, how='all', inplace=True)
        dropped_cols = before_cols - df.shape[1]
        if dropped_cols:
            log.append(f"Dropped {dropped_cols} fully-empty column(s).")

    # ── Step 5: Strip whitespace from string cells ───────────────────────────
    if opts.get('trim_whitespace', True):
        stripped = _strip_string_whitespace(df)
        if stripped:
            log.append(f"Stripped leading/trailing whitespace from {stripped} string column(s).")

    # ── Step 6: Type-coerce object columns to numeric where possible ─────────
    if opts.get('coerce_numeric', True):
        coerced = _coerce_numeric(df)
        if coerced:
            log.append(f"Auto-converted {coerced} column(s) to numeric type.")

    # ── Step 7: Remove exact duplicate rows ──────────────────────────────────
    if opts.get('remove_duplicates', True):
        before = len(df)
        df.drop_duplicates(inplace=True)
        df.reset_index(drop=True, inplace=True)
        dupes = before - len(df)
        if dupes:
            log.append(f"Removed {dupes} duplicate row(s).")

    # ── Step 8: Compute statistics ───────────────────────────────────────────
    stats = _compute_stats(df)

    # ── Final log entry ──────────────────────────────────────────────────────
    if not log:
        log.append("No cleaning actions were necessary — the data looked great!")

    logger.info(
        "clean_dataframe done: %d rows × %d cols | %d log entries",
        len(df), df.shape[1], len(log),
    )

    # ── Post-cleaning analysis ───────────────────────────────────────────────
    total_cells = health_report['row_count'] * health_report['column_count'] if health_report['column_count'] > 0 else 1
    quality_score = _compute_quality_score(health_report, total_cells)
    before_after = _compute_before_after(raw_head, df, health_report)
    cell_annotations = _generate_cell_annotations(raw_head, df, health_report, raw_duplicate_indices)
    structured_actions = _build_structured_actions(log)

    cleaning_result: dict = {
        'log': log,
        'actions': structured_actions,
        'health_report': health_report,
        'quality_score': quality_score,
        'before_after': before_after,
        'raw_snapshot': raw_snapshot,
        'raw_columns': raw_columns,
        'cell_annotations': cell_annotations,
        'stats': stats,
    }

    return df, cleaning_result


# ──────────────────────────────────────────────────────────────────────────────
# NEW ANALYSIS HELPERS
# ──────────────────────────────────────────────────────────────────────────────

def _capture_raw_snapshot(df: pd.DataFrame) -> list[dict]:
    """Capture the first 200 rows as a JSON-safe list of dicts."""
    if df.empty:
        return []
    try:
        return json.loads(df.head(200).to_json(orient='records', date_format='iso'))
    except Exception as exc:
        logger.warning("raw_snapshot capture failed: %s", exc)
        return []


def _compute_health_report(df: pd.DataFrame) -> dict:
    """
    Analyse the RAW dataframe BEFORE cleaning and return a comprehensive
    health report dict.
    """
    if df.empty:
        return {
            'row_count': 0,
            'column_count': 0,
            'missing_values': 0,
            'missing_by_column': {},
            'duplicate_rows': 0,
            'blank_headers': 0,
            'empty_columns': 0,
            'empty_rows': 0,
            'inconsistent_types': [],
            'numeric_columns': [],
            'categorical_columns': [],
            'date_columns': [],
            'memory_usage_kb': 0.0,
            'file_analysis': {
                'is_messy_excel': False,
                'multi_sheet': False,
                'header_offset': 0,
                'issues_detected': [],
            },
        }

    row_count = len(df)
    column_count = df.shape[1]

    # Missing values
    missing_series = df.isnull().sum()
    missing_values = int(missing_series.sum())
    missing_by_column = {
        str(col): int(count)
        for col, count in missing_series.items()
        if count > 0
    }

    # Duplicate rows
    duplicate_rows = int(df.duplicated().sum())

    # Blank headers
    blank_headers = 0
    for col in df.columns:
        col_str = str(col).strip()
        if not col_str or _UNNAMED_RE.match(col_str) or col_str.lower() == 'nan':
            blank_headers += 1

    # Empty columns (all NaN)
    empty_columns = int((df.isnull().all()).sum())

    # Empty rows (all NaN)
    empty_rows = int((df.isnull().all(axis=1)).sum())

    # Inconsistent types
    inconsistent_types = _detect_inconsistent_types(df)

    # Numeric columns
    numeric_columns = df.select_dtypes(include='number').columns.tolist()
    numeric_columns = [str(c) for c in numeric_columns]

    # Categorical columns
    categorical_columns = df.select_dtypes(include='object').columns.tolist()
    categorical_columns = [str(c) for c in categorical_columns]

    # Date columns
    date_columns = _detect_date_columns(df)

    # Memory usage
    try:
        memory_usage_kb = _to_json_safe(round(df.memory_usage(deep=True).sum() / 1024, 2))
    except Exception:
        memory_usage_kb = 0.0

    # File analysis for smart file detection
    issues_detected: list[str] = []
    if blank_headers > 0:
        issues_detected.append(f'{blank_headers} blank/unnamed header(s)')
    if empty_columns > 0:
        issues_detected.append(f'{empty_columns} fully-empty column(s)')
    if empty_rows > 0:
        issues_detected.append(f'{empty_rows} fully-empty row(s)')
    if duplicate_rows > 0:
        issues_detected.append(f'{duplicate_rows} duplicate row(s)')
    if missing_values > 0:
        issues_detected.append(f'{missing_values} missing value(s)')
    if inconsistent_types:
        issues_detected.append(f'{len(inconsistent_types)} column(s) with mixed types')

    has_sheet_col = '_sheet_name' in df.columns
    is_messy = blank_headers > 0 or empty_columns > 0 or empty_rows > 2

    file_analysis: dict = {
        'is_messy_excel': is_messy,
        'multi_sheet': has_sheet_col,
        'header_offset': 0,
        'issues_detected': issues_detected,
    }

    return {
        'row_count': _to_json_safe(row_count),
        'column_count': _to_json_safe(column_count),
        'missing_values': _to_json_safe(missing_values),
        'missing_by_column': missing_by_column,
        'duplicate_rows': _to_json_safe(duplicate_rows),
        'blank_headers': _to_json_safe(blank_headers),
        'empty_columns': _to_json_safe(empty_columns),
        'empty_rows': _to_json_safe(empty_rows),
        'inconsistent_types': inconsistent_types,
        'numeric_columns': numeric_columns,
        'categorical_columns': categorical_columns,
        'date_columns': date_columns,
        'memory_usage_kb': memory_usage_kb,
        'file_analysis': file_analysis,
    }


def _compute_quality_score(health_report: dict, total_cells: int) -> int:
    """
    Return a 0–100 quality score using a weighted deduction formula.

    Deductions:
        - missing_values / total_cells × 40 (max 40)
        - duplicate_rows / row_count × 25  (max 25)
        - blank_headers / column_count × 15 (max 15)
        - empty_columns / column_count × 10 (max 10)
        - len(inconsistent_types) / column_count × 10 (max 10)
    """
    score: float = 100.0
    row_count = health_report.get('row_count', 0)
    column_count = health_report.get('column_count', 0)

    if total_cells > 0:
        missing_pct = health_report.get('missing_values', 0) / total_cells
        score -= min(missing_pct * 40, 40)

    if row_count > 0:
        dup_pct = health_report.get('duplicate_rows', 0) / row_count
        score -= min(dup_pct * 25, 25)

    if column_count > 0:
        blank_pct = health_report.get('blank_headers', 0) / column_count
        score -= min(blank_pct * 15, 15)

        empty_col_pct = health_report.get('empty_columns', 0) / column_count
        score -= min(empty_col_pct * 10, 10)

        inconsistent_count = len(health_report.get('inconsistent_types', []))
        incon_pct = inconsistent_count / column_count
        score -= min(incon_pct * 10, 10)

    return max(0, min(100, int(round(score))))


def _detect_date_columns(df: pd.DataFrame) -> list[str]:
    """
    Check each object column — if >60% of non-null values parse as dates
    (after 1900), it's a date column.
    """
    date_cols: list[str] = []
    obj_cols = df.select_dtypes(include='object').columns.tolist()

    for col in obj_cols:
        series = df[col].dropna()
        if len(series) == 0:
            continue
        # Sample up to 200 values for performance
        sample = series.head(200)
        date_count = 0
        for val in sample:
            try:
                parsed = pd.to_datetime(str(val), format='mixed', dayfirst=False)
                if parsed.year >= 1900:
                    date_count += 1
            except (ValueError, TypeError, OverflowError):
                continue

        if len(sample) > 0 and (date_count / len(sample)) > 0.6:
            date_cols.append(str(col))

    return date_cols


def _detect_inconsistent_types(df: pd.DataFrame) -> list[str]:
    """
    For each object column, check if it has a mix of numeric-looking and
    non-numeric values. If 20–80% are numeric, it's inconsistent.
    """
    inconsistent: list[str] = []
    obj_cols = df.select_dtypes(include='object').columns.tolist()

    for col in obj_cols:
        series = df[col].dropna()
        if len(series) == 0:
            continue
        numeric_count = pd.to_numeric(series, errors='coerce').notna().sum()
        ratio = numeric_count / len(series)
        if 0.2 <= ratio <= 0.8:
            inconsistent.append(str(col))

    return inconsistent


def _compute_before_after(
    raw_df: pd.DataFrame,
    cleaned_df: pd.DataFrame,
    raw_health: dict,
) -> dict:
    """
    Return a before-vs-after comparison dict.
    """
    # "Before" comes from the raw health report and the full raw dataframe
    before: dict = {
        'rows': _to_json_safe(raw_health.get('row_count', 0)),
        'columns': _to_json_safe(raw_health.get('column_count', 0)),
        'duplicates': _to_json_safe(raw_health.get('duplicate_rows', 0)),
        'missing_values': _to_json_safe(raw_health.get('missing_values', 0)),
        'empty_columns': _to_json_safe(raw_health.get('empty_columns', 0)),
        'empty_rows': _to_json_safe(raw_health.get('empty_rows', 0)),
    }

    # "After" is computed from the cleaned dataframe
    after_missing = int(cleaned_df.isnull().sum().sum()) if not cleaned_df.empty else 0
    after_duplicates = int(cleaned_df.duplicated().sum()) if not cleaned_df.empty else 0
    after_empty_cols = int((cleaned_df.isnull().all()).sum()) if not cleaned_df.empty else 0
    after_empty_rows = int((cleaned_df.isnull().all(axis=1)).sum()) if not cleaned_df.empty else 0

    after: dict = {
        'rows': _to_json_safe(len(cleaned_df)),
        'columns': _to_json_safe(cleaned_df.shape[1]),
        'duplicates': _to_json_safe(after_duplicates),
        'missing_values': _to_json_safe(after_missing),
        'empty_columns': _to_json_safe(after_empty_cols),
        'empty_rows': _to_json_safe(after_empty_rows),
    }

    return {'before': before, 'after': after}


def _generate_cell_annotations(
    raw_df: pd.DataFrame,
    cleaned_df: pd.DataFrame,
    raw_health: dict,
    raw_duplicate_indices: list[int],
) -> dict:
    """
    Return cell-level annotations for the first 200 rows.

    Keys are string 'row,col' (integer indices). Values are issue types:
        'missing'   — cell was/is NaN
        'duplicate' — row was a duplicate
        'fixed'     — cell changed between raw and cleaned

    Returns
    -------
    dict with keys 'raw', 'cleaned', 'duplicate_row_indices'.
    """
    raw_annotations: dict[str, str] = {}
    cleaned_annotations: dict[str, str] = {}

    # Limit to first 200 rows
    raw_head = raw_df.head(200)
    cleaned_head = cleaned_df.head(200)

    # Annotate missing cells in raw data
    if not raw_head.empty:
        raw_null_mask = raw_head.isnull()
        for row_idx in range(len(raw_head)):
            for col_idx in range(raw_head.shape[1]):
                if raw_null_mask.iloc[row_idx, col_idx]:
                    raw_annotations[f'{row_idx},{col_idx}'] = 'missing'

    # Annotate duplicate rows in raw data
    dup_indices_in_range = [i for i in raw_duplicate_indices if i < 200]
    if not raw_head.empty:
        for row_idx in dup_indices_in_range:
            for col_idx in range(raw_head.shape[1]):
                key = f'{row_idx},{col_idx}'
                if key not in raw_annotations:
                    raw_annotations[key] = 'duplicate'

    # Annotate cleaned data — mark cells that were missing and are now filled,
    # or cells that changed between raw and cleaned
    if not cleaned_head.empty:
        cleaned_null_mask = cleaned_head.isnull()
        for row_idx in range(len(cleaned_head)):
            for col_idx in range(cleaned_head.shape[1]):
                if cleaned_null_mask.iloc[row_idx, col_idx]:
                    cleaned_annotations[f'{row_idx},{col_idx}'] = 'missing'

        # Detect 'fixed' cells — compare raw and cleaned where both exist
        min_rows = min(len(raw_head), len(cleaned_head))
        min_cols = min(raw_head.shape[1], cleaned_head.shape[1])
        for row_idx in range(min_rows):
            for col_idx in range(min_cols):
                raw_val = raw_head.iloc[row_idx, col_idx]
                cleaned_val = cleaned_head.iloc[row_idx, col_idx]
                raw_is_na = pd.isna(raw_val) if not isinstance(raw_val, str) else False
                cleaned_is_na = pd.isna(cleaned_val) if not isinstance(cleaned_val, str) else False

                if raw_is_na and not cleaned_is_na:
                    cleaned_annotations[f'{row_idx},{col_idx}'] = 'fixed'
                elif not raw_is_na and not cleaned_is_na:
                    try:
                        if str(raw_val) != str(cleaned_val):
                            cleaned_annotations[f'{row_idx},{col_idx}'] = 'fixed'
                    except Exception:
                        pass

    return {
        'raw': raw_annotations,
        'cleaned': cleaned_annotations,
        'duplicate_row_indices': dup_indices_in_range,
    }


def _build_structured_actions(log: list[str]) -> list[dict]:
    """
    Convert the simple string log into structured action dicts.

    Each action has: action, details, count, category, severity, icon.
    """
    actions: list[dict] = []

    for entry in log:
        action_dict = _parse_log_entry(entry)
        actions.append(action_dict)

    return actions


def _parse_log_entry(entry: str) -> dict:
    """Parse a single log string into a structured action dict."""
    entry_lower = entry.lower()

    # Try to extract a count from the entry
    count_match = re.search(r'(\d+)', entry)
    count = int(count_match.group(1)) if count_match else 0

    # Categorise and assign severity/icon based on content
    if 'duplicate' in entry_lower:
        return {
            'action': 'Removed duplicate rows',
            'details': entry,
            'count': count,
            'category': 'structure',
            'severity': 'warning',
            'icon': 'trash',
        }
    elif 'empty row' in entry_lower or 'fully-empty row' in entry_lower:
        return {
            'action': 'Removed empty rows',
            'details': entry,
            'count': count,
            'category': 'structure',
            'severity': 'info',
            'icon': 'trash',
        }
    elif 'empty column' in entry_lower or 'fully-empty column' in entry_lower:
        return {
            'action': 'Removed empty columns',
            'details': entry,
            'count': count,
            'category': 'structure',
            'severity': 'info',
            'icon': 'columns',
        }
    elif 'normali' in entry_lower or 'column header' in entry_lower:
        return {
            'action': 'Normalized column headers',
            'details': entry,
            'count': count,
            'category': 'structure',
            'severity': 'info',
            'icon': 'edit',
        }
    elif 'whitespace' in entry_lower or 'strip' in entry_lower:
        return {
            'action': 'Trimmed whitespace',
            'details': entry,
            'count': count,
            'category': 'content',
            'severity': 'info',
            'icon': 'scissors',
        }
    elif 'numeric' in entry_lower or 'coerce' in entry_lower or 'convert' in entry_lower:
        return {
            'action': 'Converted column types',
            'details': entry,
            'count': count,
            'category': 'types',
            'severity': 'info',
            'icon': 'type',
        }
    elif 'flatten' in entry_lower or 'multi-level' in entry_lower:
        return {
            'action': 'Flattened multi-level headers',
            'details': entry,
            'count': count,
            'category': 'structure',
            'severity': 'info',
            'icon': 'layers',
        }
    elif 'no cleaning' in entry_lower:
        return {
            'action': 'No issues found',
            'details': entry,
            'count': 0,
            'category': 'structure',
            'severity': 'info',
            'icon': 'check',
        }
    else:
        return {
            'action': entry[:60],
            'details': entry,
            'count': count,
            'category': 'content',
            'severity': 'info',
            'icon': 'info',
        }


# ──────────────────────────────────────────────────────────────────────────────
# PRIVATE STEP FUNCTIONS
# ──────────────────────────────────────────────────────────────────────────────

def _flatten_multiindex(df: pd.DataFrame) -> tuple[pd.DataFrame, bool]:
    """
    Collapse a MultiIndex column header into a single level.

    Joins non-empty, non-Unnamed level values with '_'.
    Example: ('Sales', 'Q1 2024') → 'sales_q1_2024'
    """
    if not isinstance(df.columns, pd.MultiIndex):
        return df, False

    new_cols = []
    for i, col_tuple in enumerate(df.columns):
        parts = [
            str(p).strip()
            for p in col_tuple
            if str(p).strip() and not _UNNAMED_RE.match(str(p).strip())
        ]
        new_cols.append('_'.join(parts) if parts else f'col_{i}')

    df.columns = new_cols
    return df, True


def _normalise_columns(df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    """
    Produce clean, unique column names:

    1. Stringify
    2. Strip whitespace
    3. Lowercase
    4. Replace non-alphanumeric runs with '_'
    5. Strip edge underscores
    6. Replace blank / Unnamed / 'nan' → ''
    7. Assign col_N to remaining blanks
    8. Append _1, _2 … for duplicates
    """
    original = list(df.columns)
    normalised: list[str] = []

    for col in original:
        s = str(col).strip().lower()
        s = re.sub(r'[^a-z0-9]+', '_', s)
        s = s.strip('_')
        if not s or _UNNAMED_RE.match(s) or s == 'nan':
            s = ''
        normalised.append(s)

    # Uniqueness pass
    seen: dict[str, int] = {}
    unique: list[str] = []
    for idx, name in enumerate(normalised):
        if name == '':
            name = f'col_{idx}'
        if name in seen:
            seen[name] += 1
            unique.append(f'{name}_{seen[name]}')
        else:
            seen[name] = 0
            unique.append(name)

    df.columns = unique

    if original != unique:
        return df, "Normalised column headers (lowercased, deduplicated, cleaned special characters)."
    return df, ''


def _strip_string_whitespace(df: pd.DataFrame) -> int:
    """
    Strip leading/trailing whitespace from every cell in object-dtype
    columns.  Returns the number of columns processed.

    Why: Excel exports often include invisible trailing spaces that make
    GROUP BY / unique-value detection unreliable.
    """
    str_cols = df.select_dtypes(include='object').columns.tolist()
    for col in str_cols:
        try:
            df[col] = df[col].apply(
                lambda x: x.strip() if isinstance(x, str) else x
            )
        except Exception as exc:
            logger.debug("Whitespace strip failed for col '%s': %s", col, exc)
    return len(str_cols)


def _coerce_numeric(df: pd.DataFrame) -> int:
    """
    Try to convert object-dtype columns to numeric.

    Uses ``pd.to_numeric(errors='ignore')`` — if any cell in the column
    cannot be converted the column is left as-is.  This handles the common
    case where ``read_excel(..., dtype=object)`` keeps number columns as
    strings.

    Returns the number of columns successfully coerced.

    Why: Statistics and chart Y-axis selection both rely on the column
    having a proper numeric dtype.
    """
    coerced = 0
    for col in df.select_dtypes(include='object').columns:
        if col in _META_COLUMNS:
            continue   # never coerce _sheet_name or similar meta cols
        try:
            converted = pd.to_numeric(df[col], errors='coerce')
            # Only adopt the conversion if at least 60 % of values survived
            non_null_ratio = converted.notna().sum() / max(len(converted), 1)
            if non_null_ratio >= 0.6:
                df[col] = converted
                coerced += 1
        except Exception:
            pass
    return coerced


def _compute_stats(df: pd.DataFrame) -> dict:
    """
    Compute per-column descriptive statistics and return a dict that is
    safe for ``json.dumps()`` (no numpy scalars, no NaN, no Infinity).

    Why: Django's JSON serialiser cannot handle numpy float64 / int64 types
    or JSON-invalid float values like NaN and Inf.  We convert everything
    to native Python types here once, avoiding runtime errors later.

    Structure
    ---------
    {
        "column_name": {
            "count": 42,
            "mean": 3.14,
            ...
        },
        ...
    }
    """
    stats: dict = {}
    analysis_cols = [c for c in df.columns if c not in _META_COLUMNS]

    if not analysis_cols:
        return stats

    try:
        desc = df[analysis_cols].describe(include='all')
    except Exception as exc:
        logger.warning("describe() failed: %s", exc)
        return stats

    for col in desc.columns:
        col_stats: dict = {}
        for stat_name, value in desc[col].items():
            safe = _to_json_safe(value)
            if safe is not None:           # skip NaN / None entries
                col_stats[stat_name] = safe
        if col_stats:
            stats[col] = col_stats

    return stats


def _to_json_safe(value):
    """
    Convert *value* to a JSON-serialisable Python scalar.

    Mapping
    -------
    - numpy integer  → int
    - numpy float    → float  (NaN / Inf → None so they are skipped)
    - numpy bool     → bool
    - pandas NA      → None
    - str / datetime → str
    - everything else → str  (fallback)
    """
    # Explicit None / pandas NA
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    # numpy integers
    if isinstance(value, (np.integer,)):
        return int(value)

    # numpy floats — guard against NaN and Inf which are invalid JSON
    if isinstance(value, (np.floating, float)):
        f = float(value)
        if not np.isfinite(f):
            return None
        return f

    # numpy bool
    if isinstance(value, np.bool_):
        return bool(value)

    # Native Python scalars — already safe
    if isinstance(value, (int, float, bool, str)):
        return value

    # Timestamps and everything else → string
    return str(value)
