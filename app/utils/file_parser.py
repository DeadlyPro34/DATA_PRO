"""
file_parser.py — Industry-level smart file parser for DATA_PRO
==============================================================

Handles CSV, JSON, and Excel files.

For Excel, implements a multi-stage smart parsing pipeline:
    1. detect_header_row()   — Find the real header row in messy sheets
    2. clean_column_names()  — Normalize, deduplicate, fix blank headers
    3. is_valid_sheet()      — Skip useless sheets (notes, empty, tiny)
    4. parse_excel_smart()   — Orchestrate all sheets into one clean DataFrame
    5. parse_file()          — Public entry point called by views.py

Author: DATA_PRO
"""

import os
import re
import logging

import numpy as np
import pandas as pd

# Module-level logger — output appears in Django's runserver console
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ──────────────────────────────────────────────────────────────────────────────

# Maximum number of rows to scan when searching for the real header row.
HEADER_SCAN_ROWS = 10

# A sheet is considered valid only if it has at least this many columns
# and rows (after the header is identified).
MIN_VALID_COLS = 2
MIN_VALID_ROWS = 3

# If the proportion of non-null cells in the detected header row is below
# this threshold the sheet is likely a notes/instructions page.
MIN_HEADER_FILL_RATIO = 0.4

# Regex that matches pandas auto-generated "Unnamed: N" column labels.
_UNNAMED_RE = re.compile(r'^unnamed[:\s_]\s*\d*', re.IGNORECASE)


# ──────────────────────────────────────────────────────────────────────────────
# STEP 1 — detect_header_row()
# ──────────────────────────────────────────────────────────────────────────────

def detect_header_row(raw_df: pd.DataFrame) -> int:
    """
    Inspect the first ``HEADER_SCAN_ROWS`` rows of a raw DataFrame (read
    with ``header=None``) and return the index of the row that is most
    likely the column-header row.

    Decision logic
    --------------
    We score every candidate row by the number of cells that look like
    meaningful column labels:
        - Non-null
        - Non-numeric  (real headers are almost always strings)
        - Not too long (labels > 80 chars are probably sentence-level notes)

    The first row that scores ≥ ``MIN_HEADER_FILL_RATIO`` of all columns
    is chosen.  If no row qualifies we fall back to row 0, which matches
    the default pandas behaviour.

    Why this matters
    ----------------
    Real-world Excel files often start with a company logo area, a report
    title, filter-parameter cells, or instruction text before the actual
    column headers.  Using row 0 blindly turns all of that into broken
    column names.

    Parameters
    ----------
    raw_df : pd.DataFrame
        DataFrame read with ``header=None`` so every row is a data row.

    Returns
    -------
    int
        Zero-based row index of the best header candidate.
    """
    n_cols = raw_df.shape[1]
    if n_cols == 0:
        return 0

    scan_limit = min(HEADER_SCAN_ROWS, len(raw_df))

    for row_idx in range(scan_limit):
        row = raw_df.iloc[row_idx]

        # Count cells that look like genuine column labels
        label_count = sum(
            1 for cell in row
            if _is_good_label(cell)
        )

        fill_ratio = label_count / n_cols
        logger.debug(
            "Header scan row=%d  labels=%d/%d  ratio=%.2f",
            row_idx, label_count, n_cols, fill_ratio,
        )

        if fill_ratio >= MIN_HEADER_FILL_RATIO:
            logger.info("Header row detected at index %d for sheet.", row_idx)
            return row_idx

    # Fallback — use row 0 (standard pandas default)
    logger.warning("Could not detect header row; falling back to row 0.")
    return 0


def _is_good_label(cell) -> bool:
    """
    Return True when *cell* looks like a column-header label rather than
    a data value, note, or empty placeholder.
    """
    if cell is None or (isinstance(cell, float) and np.isnan(cell)):
        return False                         # NaN / empty

    cell_str = str(cell).strip()
    if not cell_str:
        return False                         # whitespace-only

    if len(cell_str) > 80:
        return False                         # probably a sentence / note

    # Cells that are purely numeric are data values, not header labels
    try:
        float(cell_str)
        return False
    except ValueError:
        pass

    return True


# ──────────────────────────────────────────────────────────────────────────────
# STEP 2 — clean_column_names()
# ──────────────────────────────────────────────────────────────────────────────

def clean_column_names(columns) -> list:
    """
    Return a cleaned, unique list of column names derived from *columns*.

    Pipeline (applied in order)
    ---------------------------
    1. Flatten MultiIndex tuples → join non-empty, non-Unnamed levels with '_'
    2. Stringify every element
    3. Strip leading/trailing whitespace
    4. Lowercase
    5. Replace any run of non-alphanumeric characters with '_'
    6. Strip leading/trailing underscores
    7. Replace blank / Unnamed / 'nan' placeholders with ''  (handled next)
    8. Assign generic ``col_N`` names to any still-empty labels
    9. Append ``_1``, ``_2`` … suffixes to make names unique

    Why this matters
    ----------------
    pandas generates labels like "Unnamed: 3_level_0" for merged header
    cells and blank columns.  These survive into JSON and break
    ``to_json(orient='records')`` when duplicated.

    Parameters
    ----------
    columns : Index or list
        Raw column index from a pandas DataFrame.

    Returns
    -------
    list[str]
        Cleaned, unique column name strings.
    """
    raw: list[str] = []

    for col in columns:
        # ── 1. Flatten MultiIndex tuples ───────────────────────────────────
        if isinstance(col, tuple):
            parts = [
                str(p).strip()
                for p in col
                if str(p).strip() and not _UNNAMED_RE.match(str(p).strip())
            ]
            col = '_'.join(parts) if parts else ''
        else:
            col = str(col)

        # ── 2-6. Normalise ─────────────────────────────────────────────────
        col = col.strip().lower()
        col = re.sub(r'[^a-z0-9]+', '_', col)   # non-alphanum → underscore
        col = col.strip('_')                      # trim edge underscores

        # ── 7. Replace placeholder labels ──────────────────────────────────
        if not col or _UNNAMED_RE.match(col) or col == 'nan':
            col = ''

        raw.append(col)

    # ── 8 & 9. Generic names + uniqueness ──────────────────────────────────
    seen: dict[str, int] = {}
    result: list[str] = []

    for idx, name in enumerate(raw):
        if name == '':
            name = f'col_{idx}'                  # generic fallback

        if name in seen:
            seen[name] += 1
            result.append(f'{name}_{seen[name]}')
        else:
            seen[name] = 0
            result.append(name)

    return result


# ──────────────────────────────────────────────────────────────────────────────
# STEP 3 — is_valid_sheet()
# ──────────────────────────────────────────────────────────────────────────────

def is_valid_sheet(df: pd.DataFrame, sheet_name: str) -> tuple[bool, str]:
    """
    Decide whether a sheet contains a usable dataset.

    Returns a ``(is_valid, reason)`` tuple so callers can log skip reasons.

    Rules (all must pass)
    ----------------------
    1. DataFrame must not be completely empty.
    2. Must have at least ``MIN_VALID_COLS`` columns after dropping
       fully-empty columns.
    3. Must have at least ``MIN_VALID_ROWS`` non-empty rows (excluding the
       header).
    4. The header row must have a fill-ratio ≥ ``MIN_HEADER_FILL_RATIO``
       (i.e. the sheet is not just a block of notes with one or two labels
       at the top).

    Why this matters
    ----------------
    Workbooks routinely contain a "README", "Instructions", "Change Log",
    or "Cover Page" sheet.  Concatenating these with real data sheets
    produces garbled results.

    Parameters
    ----------
    df : pd.DataFrame
        Sheet read with the real header already applied.
    sheet_name : str
        Name used only for logging.

    Returns
    -------
    tuple[bool, str]
    """
    # Rule 1 — not empty
    if df.empty:
        return False, "sheet is completely empty"

    # Rule 2 — enough columns (ignore fully-empty columns)
    non_empty_cols = df.dropna(axis=1, how='all').shape[1]
    if non_empty_cols < MIN_VALID_COLS:
        return False, f"only {non_empty_cols} non-empty column(s) (need ≥ {MIN_VALID_COLS})"

    # Rule 3 — enough data rows (ignore fully-empty rows)
    non_empty_rows = df.dropna(how='all').shape[0]
    if non_empty_rows < MIN_VALID_ROWS:
        return False, f"only {non_empty_rows} non-empty data row(s) (need ≥ {MIN_VALID_ROWS})"

    # Rule 4 — header looks like real column labels (not notes)
    header_fill = sum(
        1 for c in df.columns if _is_good_label(c)
    ) / max(len(df.columns), 1)

    if header_fill < MIN_HEADER_FILL_RATIO:
        return False, (
            f"header fill ratio {header_fill:.1%} is below "
            f"{MIN_HEADER_FILL_RATIO:.0%} — looks like a notes/cover sheet"
        )

    return True, "ok"


# ──────────────────────────────────────────────────────────────────────────────
# STEP 4 — parse_excel_smart()
# ──────────────────────────────────────────────────────────────────────────────

def parse_excel_smart(file_path: str) -> pd.DataFrame:
    """
    Industry-level smart Excel parser.

    Full pipeline per sheet
    -----------------------
    1.  Read the sheet raw (``header=None``) to get the unmodified grid.
    2.  Drop fully-empty rows and columns from the raw grid (trim the
        white-space padding that surrounds many real tables).
    3.  Detect the real header row with ``detect_header_row()``.
    4.  Re-read the sheet using the detected header row so pandas does the
        right thing with dtypes and merging.
    5.  Drop fully-empty rows and columns again (data body may have gaps).
    6.  Apply ``is_valid_sheet()`` — skip if the sheet is not a dataset.
    7.  Apply ``clean_column_names()`` to produce safe, unique column names.
    8.  Tag each row with ``_sheet_name`` when multiple valid sheets exist.
    9.  Concatenate all valid sheet DataFrames with ``ignore_index=True``.

    Why reading twice?
    ------------------
    The first read (``header=None``) gives us the raw grid for scanning.
    The second read (``header=detected_row``) lets pandas infer dtypes
    correctly for the actual data rows, which is not possible when every
    row is treated as ``object`` in the header=None read.

    Parameters
    ----------
    file_path : str
        Absolute path to the Excel file.

    Returns
    -------
    pd.DataFrame
        A single cleaned DataFrame combining all valid sheets.

    Raises
    ------
    ValueError
        When no valid data sheet is found in the workbook.
    """
    # ── Phase 1: raw read of ALL sheets ────────────────────────────────────
    try:
        raw_sheets: dict[str, pd.DataFrame] = pd.read_excel(
            file_path,
            sheet_name=None,   # read every sheet
            header=None,       # keep raw grid — we detect headers ourselves
            dtype=object,      # treat everything as object for scanning
        )
    except Exception as exc:
        raise ValueError(f"Cannot open Excel file: {exc}") from exc

    if not raw_sheets:
        raise ValueError("The Excel workbook contains no sheets.")

    valid_frames: list[pd.DataFrame] = []
    skipped: list[str] = []

    # ── Phase 2: per-sheet smart processing ────────────────────────────────
    for sheet_name, raw_df in raw_sheets.items():

        logger.info("Processing sheet: '%s'", sheet_name)

        # ── 2a. Quick skip if completely empty ─────────────────────────────
        if raw_df.empty or raw_df.shape[0] < 2:
            skipped.append(f"'{sheet_name}' (completely empty or single row)")
            logger.info("Skipping sheet '%s': empty or single row.", sheet_name)
            continue

        # ── 2b. Trim all-empty peripheral rows and columns ─────────────────
        #        Many workbooks have blank rows at the top and blank columns
        #        at the left (decorative spacing around logos/titles).
        raw_df = raw_df.dropna(how='all')        # drop empty rows
        raw_df = raw_df.dropna(axis=1, how='all') # drop empty cols
        raw_df = raw_df.reset_index(drop=True)

        if raw_df.empty:
            skipped.append(f"'{sheet_name}' (all cells empty after trimming)")
            continue

        # ── 2c. Detect the real header row ─────────────────────────────────
        header_row_idx = detect_header_row(raw_df)

        # ── 2d. Re-read the sheet with the correct header row ───────────────
        #        We use the header row index relative to the file, which may
        #        differ from raw_df if pandas trimmed leading rows during
        #        the first read.  We re-read directly from the file to get
        #        correct dtype inference for the data body.
        try:
            df: pd.DataFrame = pd.read_excel(
                file_path,
                sheet_name=sheet_name,
                header=header_row_idx,
                dtype=object,      # keep as object; cleaner will type-cast
            )
        except Exception as exc:
            skipped.append(f"'{sheet_name}' (re-read failed: {exc})")
            logger.warning("Re-read of sheet '%s' failed: %s", sheet_name, exc)
            continue

        # ── 2e. Drop empty rows / cols from the data body ──────────────────
        df = df.dropna(how='all').dropna(axis=1, how='all').reset_index(drop=True)

        # ── 2f. Convert numeric-looking object columns ──────────────────────
        #        read_excel with dtype=object keeps everything as strings;
        #        we coerce columns that look numeric so stats work correctly.
        #
        #        NOTE: pd.to_numeric(errors='ignore') was removed in pandas 2.0.
        #        We replicate its behaviour manually: coerce to numeric, then
        #        only apply if no new NaN values were introduced (i.e. the whole
        #        column was genuinely numeric).
        for col in df.columns:
            try:
                converted = pd.to_numeric(df[col], errors='coerce')
                original_nulls = df[col].isna().sum()
                new_nulls = converted.isna().sum()
                if new_nulls == original_nulls:
                    # Every value converted cleanly — safe to adopt
                    df[col] = converted
            except Exception:
                pass  # leave the column as-is if anything goes wrong

        # ── 2g. Validate the sheet ─────────────────────────────────────────
        valid, reason = is_valid_sheet(df, sheet_name)
        if not valid:
            skipped.append(f"'{sheet_name}' ({reason})")
            logger.info("Skipping sheet '%s': %s", sheet_name, reason)
            continue

        # ── 2h. Clean column names ─────────────────────────────────────────
        df.columns = clean_column_names(df.columns)

        # ── 2i. Tag with sheet name ────────────────────────────────────────
        df.insert(0, '_sheet_name', sheet_name)

        valid_frames.append(df)
        logger.info(
            "Sheet '%s' accepted: %d rows × %d cols.",
            sheet_name, len(df), df.shape[1],
        )

    # ── Phase 3: log and validate results ──────────────────────────────────
    if skipped:
        logger.info("Skipped sheets: %s", "; ".join(skipped))

    if not valid_frames:
        detail = "; ".join(skipped) if skipped else "no sheets found"
        raise ValueError(
            f"No usable data sheets found in the workbook. "
            f"Skipped: {detail}"
        )

    # ── Phase 4: merge ─────────────────────────────────────────────────────
    if len(valid_frames) == 1:
        # Single valid sheet — drop the _sheet_name column (no ambiguity)
        combined = valid_frames[0].drop(columns=['_sheet_name'], errors='ignore')
    else:
        # Multiple valid sheets — keep _sheet_name so users can filter
        combined = pd.concat(valid_frames, ignore_index=True, sort=False)

    logger.info(
        "Excel parse complete: %d valid sheet(s), %d rows × %d cols.",
        len(valid_frames), len(combined), combined.shape[1],
    )
    return combined


# ──────────────────────────────────────────────────────────────────────────────
# STEP 5 — parse_file()   (public entry point)
# ──────────────────────────────────────────────────────────────────────────────

def parse_file(file_path: str) -> pd.DataFrame:
    """
    Public entry point called by ``views.upload_file()``.

    Dispatches to the correct reader based on file extension and returns
    a pandas DataFrame ready for ``clean_dataframe()``.

    Supported formats
    -----------------
    * ``.csv``             — UTF-8, falls back to latin-1 on decode error
    * ``.xls`` / ``.xlsx`` — Smart multi-sheet Excel parser
    * ``.json``            — ``pd.read_json()``

    Parameters
    ----------
    file_path : str
        Absolute path to the uploaded file (as returned by
        ``UploadedFile.file.path``).

    Returns
    -------
    pd.DataFrame

    Raises
    ------
    ValueError
        With a human-readable message on any parse failure.
    """
    ext = os.path.splitext(file_path)[1].lower()
    logger.info("parse_file called: ext='%s'  path='%s'", ext, file_path)

    try:
        # ── CSV ────────────────────────────────────────────────────────────
        if ext == '.csv':
            return _parse_csv(file_path)

        # ── Excel ──────────────────────────────────────────────────────────
        elif ext in ('.xls', '.xlsx', '.xlsm', '.xlsb'):
            return parse_excel_smart(file_path)

        # ── JSON ───────────────────────────────────────────────────────────
        elif ext == '.json':
            return _parse_json(file_path)

        # ── Unknown ────────────────────────────────────────────────────────
        else:
            raise ValueError(
                f"Unsupported file type '{ext}'. "
                "Please upload a .csv, .xlsx, .xls, or .json file."
            )

    except ValueError:
        raise   # already human-readable — pass through unchanged
    except Exception as exc:
        # Catch-all: wrap unexpected errors into a clean ValueError
        logger.exception("Unexpected error in parse_file: %s", exc)
        raise ValueError(f"Failed to parse file: {exc}") from exc


# ──────────────────────────────────────────────────────────────────────────────
# PRIVATE HELPERS
# ──────────────────────────────────────────────────────────────────────────────

def _parse_csv(file_path: str) -> pd.DataFrame:
    """
    Read a CSV file, trying UTF-8 first and falling back to latin-1.

    latin-1 (ISO-8859-1) is the most common Windows codepage for CSV
    exports from Excel on non-English systems.
    """
    encodings = ('utf-8', 'utf-8-sig', 'latin-1', 'cp1252')
    last_exc: Exception | None = None

    for enc in encodings:
        try:
            df = pd.read_csv(file_path, encoding=enc)
            logger.info("CSV read OK with encoding '%s'.", enc)
            return df
        except UnicodeDecodeError as exc:
            last_exc = exc
            logger.debug("Encoding '%s' failed for CSV, trying next.", enc)
        except Exception as exc:
            raise ValueError(f"Error reading CSV: {exc}") from exc

    raise ValueError(
        f"Cannot decode the CSV file. "
        f"Tried encodings: {', '.join(encodings)}. Last error: {last_exc}"
    )


def _parse_json(file_path: str) -> pd.DataFrame:
    """
    Read a JSON file.  Tries several common orientations when the default
    fails so the user does not have to think about 'records' vs 'split'
    etc.
    """
    orientations = (None, 'records', 'split', 'index', 'columns', 'values')

    for orient in orientations:
        try:
            df = pd.read_json(file_path, orient=orient)
            if not df.empty:
                logger.info("JSON read OK with orient=%s.", orient)
                return df
        except Exception:
            continue

    raise ValueError(
        "Cannot parse the JSON file. "
        "Make sure it contains a flat array of objects or a standard "
        "pandas JSON structure."
    )
