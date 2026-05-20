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
import pandas as pd

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
