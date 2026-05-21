from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from django.http import JsonResponse
from .models import UploadedFile, CleanedDataset
from .utils.file_parser import parse_file
from .utils.data_cleaner import clean_dataframe
import json
import os
import math
import pandas as pd
import numpy as np

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})

@login_required
def dashboard(request):
    files = UploadedFile.objects.filter(user=request.user).order_by('-uploaded_at')
    return render(request, 'dashboard.html', {'files': files})

@login_required
def upload_file(request):
    if request.method == 'POST':
        if 'file' not in request.FILES:
            messages.error(request, 'No file uploaded.')
            return redirect('upload_file')
            
        file = request.FILES['file']
        custom_name = request.POST.get('custom_name', '')
        
        # Create UploadedFile
        uploaded_file = UploadedFile.objects.create(
            user=request.user,
            original_filename=file.name,
            file_type=file.name.split('.')[-1].lower(),
            custom_name=custom_name,
            file=file
        )
        
        # Process file synchronously as requested
        try:
            df = parse_file(uploaded_file.file.path)
            cleaned_df, cleaning_log, stats = clean_dataframe(df)
            
            uploaded_file.row_count = len(cleaned_df)
            uploaded_file.column_count = len(cleaned_df.columns)
            uploaded_file.save()
            
            
            # Serialize safely via pandas to avoid NaN/Infinity JSON serialization errors in SQLite
            safe_rows = json.loads(cleaned_df.to_json(orient='records', date_format='iso'))
            # Some stats might have np floats
            safe_stats = json.loads(pd.Series(stats).to_json()) if stats else {}

            # Create Dataset
            CleanedDataset.objects.create(
                uploaded_file=uploaded_file,
                columns=list(cleaned_df.columns),
                rows=safe_rows,
                cleaning_log=cleaning_log,
                stats=safe_stats
            )
            
            messages.success(request, 'File uploaded and cleaned successfully!')
            return redirect('dataset_view', file_id=uploaded_file.id)
            
        except Exception as e:
            uploaded_file.delete()
            messages.error(request, f'Error processing file: {str(e)}')
            return redirect('upload_file')
            
    return render(request, 'upload.html')

@login_required
def dataset_view(request, file_id):
    uploaded_file = get_object_or_404(UploadedFile, id=file_id, user=request.user)
    dataset = get_object_or_404(CleanedDataset, uploaded_file=uploaded_file)

    context = {
        'file': uploaded_file,
        'dataset': dataset,
        'file_id': file_id,
        # Safely dump lists to JSON strings for frontend JS
        'columns_json': json.dumps(dataset.columns),
        'rows_json': json.dumps(dataset.rows),
    }
    return render(request, 'dataset.html', context)


@login_required
def delete_dataset(request, file_id):
    if request.method == 'POST':
        uploaded_file = get_object_or_404(UploadedFile, id=file_id, user=request.user)
        try:
            if uploaded_file.file and os.path.exists(uploaded_file.file.path):
                os.remove(uploaded_file.file.path)
        except Exception:
            pass
        uploaded_file.delete()
        messages.success(request, 'Dataset deleted successfully.')
    return redirect('dashboard')


@login_required
def chart_data(request, file_id):
    """
    JSON API — returns aggregated chart data for a given dataset.

    Query parameters
    ----------------
    x   : str   — X-axis column name (the grouping column)
    y   : str   — Y-axis column name (the value / label column)
    agg : str   — Aggregation mode: sum | count | mean | min | max
                  Default: sum

    Response (JSON array)
    ----------------------
    Sum / Mean / Min / Max mode:
        [{"x_col": "value", "result": 42.0}, ...]

    Count mode:
        [{"x_col": 81, "count": 3, "members": "Ali, Ahmed, Sara"}, ...]

    Why this matters
    ----------------
    The previous frontend code always SUM-aggregated Y values.
    When X = marks and Y = student_name, all students with the same
    mark had their mark values SUMMED (81+81+81 = 243) instead of
    COUNTED (3 students).  This endpoint allows the frontend to request
    the correct aggregation per use-case.
    """
    uploaded_file = get_object_or_404(UploadedFile, id=file_id, user=request.user)
    dataset       = get_object_or_404(CleanedDataset, uploaded_file=uploaded_file)

    x_col   = request.GET.get('x', '').strip()
    y_col   = request.GET.get('y', '').strip()
    agg_mode = request.GET.get('agg', 'sum').strip().lower()

    # ── Validate inputs ────────────────────────────────────────────────────
    valid_cols = dataset.columns
    if not x_col or x_col not in valid_cols:
        return JsonResponse({'error': f"Invalid or missing 'x' column: '{x_col}'"}, status=400)
    if not y_col or y_col not in valid_cols:
        return JsonResponse({'error': f"Invalid or missing 'y' column: '{y_col}'"}, status=400)
    if agg_mode not in ('sum', 'count', 'mean', 'min', 'max'):
        return JsonResponse({'error': f"Invalid agg mode: '{agg_mode}'. Use: sum|count|mean|min|max"}, status=400)

    # ── Rebuild DataFrame from stored rows ─────────────────────────────────
    df = pd.DataFrame(dataset.rows)
    if df.empty:
        return JsonResponse([], safe=False)

    # ── Apply aggregation ──────────────────────────────────────────────────
    try:
        if agg_mode == 'count':
            result = _agg_count(df, x_col, y_col)
        else:
            result = _agg_numeric(df, x_col, y_col, agg_mode)
    except Exception as exc:
        return JsonResponse({'error': str(exc)}, status=500)

    return JsonResponse(result, safe=False)


# ──────────────────────────────────────────────────────────────────────────────
# AGGREGATION HELPERS
# ──────────────────────────────────────────────────────────────────────────────

def _agg_count(df: pd.DataFrame, x_col: str, y_col: str) -> list:
    """
    Group rows by *x_col*, count occurrences, and intelligently collect 
    labels (e.g., student names) for the tooltip.
    """
    label_col = y_col

    # If the user grouped by the same column (e.g. x_col=marks, y_col=marks),
    # or if we just want to be smart about picking the "Name" column:
    if x_col == y_col or pd.api.types.is_numeric_dtype(df[y_col]):
        candidates = ['student_name', 'student', 'name', 'student_id', 'roll_no', 'rollnumber', 'id', 'email']
        # Try to find a matching column (case-insensitive)
        for cand in candidates:
            matches = [c for c in df.columns if c.lower() == cand and c != x_col]
            if matches:
                label_col = matches[0]
                break
        else:
            # Fallback: pick the first non-numeric column that isn't x_col
            non_numeric = df.select_dtypes(exclude='number').columns
            if len(non_numeric) > 0 and non_numeric[0] != x_col:
                label_col = non_numeric[0]
            else:
                # Absolute fallback: pick any column that isn't x_col
                for col in df.columns:
                    if col != x_col:
                        label_col = col
                        break

    grouped = (
        df.groupby(x_col, dropna=False)[label_col]
        .agg(
            count='count',
            members=lambda s: s.dropna().astype(str).tolist()
        )
        .reset_index()
    )

    return [
        {
            x_col:      row[x_col],
            'count':    int(row['count']),
            'students': row['members'],  # Always return under 'students' for the frontend
            'label_col': label_col       # Tell the frontend what column we used
        }
        for _, row in grouped.iterrows()
    ]


def _agg_numeric(df: pd.DataFrame, x_col: str, y_col: str, mode: str) -> list:
    """
    Group rows by *x_col* and apply a numeric aggregation (sum/mean/min/max)
    on *y_col*.

    Coerces *y_col* to numeric first.  Rows where *y_col* cannot be
    converted are dropped.
    """
    df = df.copy()
    df[y_col] = pd.to_numeric(df[y_col], errors='coerce')
    df = df.dropna(subset=[y_col])

    if df.empty:
        raise ValueError(
            f"Column '{y_col}' has no numeric values — "
            f"cannot apply '{mode}' aggregation."
        )

    agg_fn_map = {'sum': 'sum', 'mean': 'mean', 'min': 'min', 'max': 'max'}
    grouped = df.groupby(x_col, dropna=False)[y_col].agg(agg_fn_map[mode]).reset_index()
    grouped.columns = [x_col, 'result']

    return [
        {
            x_col:    row[x_col],
            'result': round(float(row['result']), 4),
        }
        for _, row in grouped.iterrows()
    ]


# ──────────────────────────────────────────────────────────────────────────────
# ADVANCED STATS ENDPOINT
# ──────────────────────────────────────────────────────────────────────────────

@login_required
def advanced_stats(request, file_id):
    """
    JSON API — returns advanced statistical data for charting.

    Query parameters
    ----------------
    col    : str   — Column name to analyse (required)
    type   : str   — Analysis type:
                     histogram | boxplot | violin | correlation
    bins   : int   — Number of histogram bins (default 20, max 100)
    group  : str   — Optional grouping column (for grouped boxplot/violin)
    cols   : str   — Comma-separated list for correlation matrix

    Response shapes
    ---------------
    histogram:
        { bins: [{x0, x1, count, density}], stats: {mean, std, min, max} }

    boxplot:
        { groups: [{name, q1, q2, q3, min, max, mean, outliers:[]}] }

    violin:
        { groups: [{name, kde: [{x, density}], q1, q2, q3, min, max}] }

    correlation:
        { columns: [...], matrix: [[...]] }
    """
    uploaded_file = get_object_or_404(UploadedFile, id=file_id, user=request.user)
    dataset = get_object_or_404(CleanedDataset, uploaded_file=uploaded_file)

    col = request.GET.get('col', '').strip()
    analysis_type = request.GET.get('type', 'histogram').strip().lower()
    bins_param = min(int(request.GET.get('bins', 20)), 100)
    group_col = request.GET.get('group', '').strip()
    cols_param = request.GET.get('cols', '').strip()

    valid_cols = dataset.columns

    # Rebuild DataFrame
    df = pd.DataFrame(dataset.rows)
    if df.empty:
        return JsonResponse({'error': 'Dataset is empty'}, status=400)

    try:
        if analysis_type == 'histogram':
            if not col or col not in valid_cols:
                return JsonResponse({'error': f"Invalid column: '{col}'"}, status=400)
            result = _compute_histogram(df, col, bins_param)

        elif analysis_type == 'boxplot':
            if not col or col not in valid_cols:
                return JsonResponse({'error': f"Invalid column: '{col}'"}, status=400)
            grp = group_col if group_col and group_col in valid_cols else None
            result = _compute_boxplot(df, col, grp)

        elif analysis_type == 'violin':
            if not col or col not in valid_cols:
                return JsonResponse({'error': f"Invalid column: '{col}'"}, status=400)
            grp = group_col if group_col and group_col in valid_cols else None
            result = _compute_violin(df, col, grp)

        elif analysis_type == 'correlation':
            if cols_param:
                corr_cols = [c.strip() for c in cols_param.split(',') if c.strip() in valid_cols]
            else:
                corr_cols = [c for c in valid_cols if c in df.columns and pd.api.types.is_numeric_dtype(df[c])]
            if len(corr_cols) < 2:
                return JsonResponse({'error': 'Need at least 2 numeric columns for correlation'}, status=400)
            result = _compute_correlation(df, corr_cols)

        else:
            return JsonResponse({'error': f"Unknown analysis type: '{analysis_type}'"}, status=400)

    except Exception as exc:
        return JsonResponse({'error': str(exc)}, status=500)

    return JsonResponse(result, safe=False)


def _safe_float(v):
    """Convert numpy/pandas scalar to Python float, handling NaN/Inf."""
    try:
        f = float(v)
        if math.isnan(f) or math.isinf(f):
            return None
        return round(f, 6)
    except (TypeError, ValueError):
        return None


def _compute_histogram(df: pd.DataFrame, col: str, bins: int) -> dict:
    """Compute histogram bins with count and density."""
    series = pd.to_numeric(df[col], errors='coerce').dropna()
    if series.empty:
        raise ValueError(f"Column '{col}' has no numeric values")

    counts, edges = np.histogram(series.values, bins=bins)
    total = len(series)
    result_bins = []
    for i in range(len(counts)):
        width = edges[i + 1] - edges[i]
        result_bins.append({
            'x0': _safe_float(edges[i]),
            'x1': _safe_float(edges[i + 1]),
            'count': int(counts[i]),
            'density': _safe_float(counts[i] / (total * width)) if total > 0 and width > 0 else 0,
        })

    return {
        'bins': result_bins,
        'stats': {
            'mean': _safe_float(series.mean()),
            'std': _safe_float(series.std()),
            'min': _safe_float(series.min()),
            'max': _safe_float(series.max()),
            'count': total,
        }
    }


def _compute_boxplot(df: pd.DataFrame, col: str, group_col: str | None) -> dict:
    """Compute box plot quartiles, whiskers, and outliers (per group)."""
    df = df.copy()
    df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna(subset=[col])
    if df.empty:
        raise ValueError(f"Column '{col}' has no numeric values")

    def _box_stats(series, name):
        vals = np.sort(series.values)
        q1 = float(np.percentile(vals, 25))
        q2 = float(np.percentile(vals, 50))
        q3 = float(np.percentile(vals, 75))
        iqr = q3 - q1
        lower_fence = q1 - 1.5 * iqr
        upper_fence = q3 + 1.5 * iqr
        whisker_low = float(vals[vals >= lower_fence].min()) if any(vals >= lower_fence) else q1
        whisker_high = float(vals[vals <= upper_fence].max()) if any(vals <= upper_fence) else q3
        outliers = [_safe_float(v) for v in vals if v < lower_fence or v > upper_fence]
        return {
            'name': str(name),
            'q1': _safe_float(q1), 'q2': _safe_float(q2), 'q3': _safe_float(q3),
            'min': _safe_float(whisker_low), 'max': _safe_float(whisker_high),
            'mean': _safe_float(series.mean()),
            'outliers': outliers[:50],  # cap at 50 outliers for transfer size
        }

    if group_col:
        groups = []
        for name, grp_df in df.groupby(group_col, dropna=False):
            if len(grp_df) > 0:
                groups.append(_box_stats(grp_df[col], name))
        return {'groups': groups}
    else:
        return {'groups': [_box_stats(df[col], col)]}


def _compute_violin(df: pd.DataFrame, col: str, group_col: str | None) -> dict:
    """Compute KDE density for violin plots (per group)."""
    df = df.copy()
    df[col] = pd.to_numeric(df[col], errors='coerce')
    df = df.dropna(subset=[col])
    if df.empty:
        raise ValueError(f"Column '{col}' has no numeric values")

    def _kde_points(series, name):
        vals = series.values
        if len(vals) < 2:
            return {'name': str(name), 'kde': [], 'q1': None, 'q2': None, 'q3': None, 'min': None, 'max': None}

        # Scott's bandwidth
        std = np.std(vals)
        h = 1.06 * std * (len(vals) ** -0.2) if std > 0 else 1.0
        vmin, vmax = vals.min(), vals.max()
        x_pts = np.linspace(vmin - 3 * h, vmax + 3 * h, 80)
        # Gaussian KDE
        kde = np.array([np.mean(np.exp(-0.5 * ((x - vals) / h) ** 2) / (h * np.sqrt(2 * np.pi))) for x in x_pts])

        return {
            'name': str(name),
            'kde': [{'x': _safe_float(x), 'density': _safe_float(d)} for x, d in zip(x_pts, kde)],
            'q1': _safe_float(np.percentile(vals, 25)),
            'q2': _safe_float(np.percentile(vals, 50)),
            'q3': _safe_float(np.percentile(vals, 75)),
            'min': _safe_float(vals.min()),
            'max': _safe_float(vals.max()),
        }

    if group_col:
        groups = []
        for name, grp_df in df.groupby(group_col, dropna=False):
            if len(grp_df) > 0:
                groups.append(_kde_points(grp_df[col], name))
        return {'groups': groups}
    else:
        return {'groups': [_kde_points(df[col], col)]}


def _compute_correlation(df: pd.DataFrame, cols: list) -> dict:
    """Compute Pearson correlation matrix for given columns."""
    sub = df[cols].apply(pd.to_numeric, errors='coerce').dropna()
    if sub.shape[0] < 2:
        raise ValueError("Not enough rows with numeric values to compute correlation")
    corr = sub.corr(method='pearson')
    matrix = [[_safe_float(corr.iloc[i][j]) for j in range(len(cols))] for i in range(len(cols))]
    return {'columns': cols, 'matrix': matrix}
