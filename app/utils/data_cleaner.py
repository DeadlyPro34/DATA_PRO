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

import logging
import re

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

def clean_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str], dict]:
    """
    Clean *df* and return ``(cleaned_df, cleaning_log, stats)``.

    Parameters
    ----------
    df : pd.DataFrame
        Raw DataFrame returned by ``parse_file()``.

    Returns
    -------
    cleaned_df : pd.DataFrame
        Fully cleaned DataFrame ready for JSON serialisation and storage.
    cleaning_log : list[str]
        Human-readable list of every action taken (shown in the UI).
    stats : dict
        Per-column descriptive statistics safe for ``json.dumps()``.
    """
    log: list[str] = []
    df = df.copy()   # never mutate the caller's object

    logger.info(
        "clean_dataframe start: %d rows × %d cols", len(df), df.shape[1]
    )

    # ── Step 0: Flatten MultiIndex columns ───────────────────────────────────
    # The Excel parser already flattens for Excel files, but CSV / JSON with
    # multi-level column structures may still arrive here with a MultiIndex.
    df, changed = _flatten_multiindex(df)
    if changed:
        log.append("Flattened multi-level column headers.")

    # ── Step 1: Normalise column names ───────────────────────────────────────
    # Safety net for CSV / JSON files whose headers were not pre-cleaned by
    # the parser.  Also catches anything the parser missed.
    df, col_log = _normalise_columns(df)
    if col_log:
        log.append(col_log)

    # ── Step 2: Drop fully-empty rows ────────────────────────────────────────
    before = len(df)
    df.dropna(how='all', inplace=True)
    df.reset_index(drop=True, inplace=True)
    dropped = before - len(df)
    if dropped:
        log.append(f"Dropped {dropped} fully-empty row(s).")

    # ── Step 3: Drop fully-empty columns ─────────────────────────────────────
    before_cols = df.shape[1]
    df.dropna(axis=1, how='all', inplace=True)
    dropped_cols = before_cols - df.shape[1]
    if dropped_cols:
        log.append(f"Dropped {dropped_cols} fully-empty column(s).")

    # ── Step 4: Strip whitespace from string cells ───────────────────────────
    stripped = _strip_string_whitespace(df)
    if stripped:
        log.append(f"Stripped leading/trailing whitespace from {stripped} string column(s).")

    # ── Step 5: Type-coerce object columns to numeric where possible ─────────
    coerced = _coerce_numeric(df)
    if coerced:
        log.append(f"Auto-converted {coerced} column(s) to numeric type.")

    # ── Step 6: Remove exact duplicate rows ──────────────────────────────────
    before = len(df)
    df.drop_duplicates(inplace=True)
    df.reset_index(drop=True, inplace=True)
    dupes = before - len(df)
    if dupes:
        log.append(f"Removed {dupes} duplicate row(s).")

    # ── Step 7: Compute statistics ───────────────────────────────────────────
    stats = _compute_stats(df)

    # ── Final log entry ──────────────────────────────────────────────────────
    if not log:
        log.append("No cleaning actions were necessary — the data looked great!")

    logger.info(
        "clean_dataframe done: %d rows × %d cols | %d log entries",
        len(df), df.shape[1], len(log),
    )
    return df, log, stats


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
