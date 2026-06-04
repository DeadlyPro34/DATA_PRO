"""
views.py — REST API endpoints for DataPro.

Endpoints
---------
POST   /api/auth/register/          — Create account
POST   /api/auth/login/             — JWT token pair
POST   /api/auth/refresh/           — Refresh access token
GET    /api/auth/me/                — Current user info

GET    /api/datasets/               — List user's datasets
POST   /api/datasets/upload/        — Upload file (triggers Celery task)
GET    /api/datasets/<id>/          — Dataset metadata + status
DELETE /api/datasets/<id>/delete/   — Delete dataset + rows
GET    /api/datasets/<id>/rows/     — Paginated rows (for virtual scroll)
"""

import os
import logging
from django.contrib.auth.models import User
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .models import Dataset, DataRow
from .serializers import (
    RegisterSerializer, UserSerializer,
    DatasetSerializer, DatasetUploadSerializer, DataRowSerializer
)
from .tasks import process_dataset

logger = logging.getLogger(__name__)


# ── Auth ──────────────────────────────────────────────────────────────────────

class RegisterView(generics.CreateAPIView):
    queryset         = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {'message': 'Account created!', 'user': UserSerializer(user).data},
            status=status.HTTP_201_CREATED
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me_view(request):
    return Response(UserSerializer(request.user).data)


# ── Datasets ──────────────────────────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dataset_list(request):
    """List all datasets owned by the authenticated user."""
    datasets = Dataset.objects.filter(owner=request.user)
    serializer = DatasetSerializer(datasets, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def dataset_upload(request):
    """
    Upload a file, save it, create Dataset record,
    and dispatch the Celery parsing task.
    """
    serializer = DatasetUploadSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    f        = serializer.validated_data['file']
    ext      = f.name.rsplit('.', 1)[-1].lower()
    name     = serializer.validated_data.get('name') or f.name

    dataset = Dataset.objects.create(
        owner         = request.user,
        name          = name,
        original_name = f.name,
        file          = f,
        file_type     = ext,
        status        = Dataset.STATUS_PENDING,
    )

    # Dispatch background task
    process_dataset.delay(dataset.id)
    logger.info("Dispatched process_dataset for dataset %s", dataset.id)

    return Response(
        DatasetSerializer(dataset).data,
        status=status.HTTP_201_CREATED
    )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dataset_detail(request, pk):
    """Return dataset metadata + current processing status."""
    try:
        dataset = Dataset.objects.get(pk=pk, owner=request.user)
    except Dataset.DoesNotExist:
        return Response({'error': 'Dataset not found.'}, status=404)

    return Response(DatasetSerializer(dataset).data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def dataset_delete(request, pk):
    """Delete dataset, all its rows, and the uploaded file."""
    try:
        dataset = Dataset.objects.get(pk=pk, owner=request.user)
    except Dataset.DoesNotExist:
        return Response({'error': 'Dataset not found.'}, status=404)

    # Delete physical file
    try:
        if dataset.file and os.path.exists(dataset.file.path):
            os.remove(dataset.file.path)
    except Exception as e:
        logger.warning("Could not delete file for dataset %s: %s", pk, e)

    dataset.delete()   # CASCADE deletes DataRows automatically
    return Response({'message': 'Dataset deleted.'}, status=204)


# ── Rows (virtual scrolling) ──────────────────────────────────────────────────

class RowPagination(PageNumberPagination):
    page_size            = 100
    page_size_query_param = 'size'
    max_page_size        = 500


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dataset_rows(request, pk):
    """
    Return paginated rows for virtual scrolling.

    Query params
    ------------
    page : int   — page number (default 1)
    size : int   — rows per page (default 100, max 500)
    """
    try:
        dataset = Dataset.objects.get(pk=pk, owner=request.user)
    except Dataset.DoesNotExist:
        return Response({'error': 'Dataset not found.'}, status=404)

    if dataset.status != Dataset.STATUS_READY:
        return Response(
            {'error': f'Dataset is not ready yet (status: {dataset.status}).'},
            status=400
        )

    rows_qs    = DataRow.objects.filter(dataset=dataset).values('row_index', 'data')
    paginator  = RowPagination()
    page       = paginator.paginate_queryset(rows_qs, request)

    # Flatten: return list of dicts (data field only, row_index implicit)
    result = [r['data'] for r in page]
    return paginator.get_paginated_response(result)

# ══════════════════════════════════════════════════════════════════════════════
# NEW ENDPOINTS — In views.py ke BILKUL NEECHE paste karo (existing code ke baad)
# ══════════════════════════════════════════════════════════════════════════════

import numpy as np
import pandas as pd


# ── Helper: dataset → DataFrame ───────────────────────────────────────────────
def _to_df(dataset):
    rows = DataRow.objects.filter(dataset=dataset).order_by('row_index')
    data = [r.data for r in rows]
    return pd.DataFrame(data, columns=dataset.columns), list(rows)


# ── Helper: DataFrame → save back to DB ───────────────────────────────────────
def _save_df(df, dataset):
    DataRow.objects.filter(dataset=dataset).delete()
    df = df.fillna("")
    dataset.columns = list(df.columns)
    dataset.row_count = len(df)
    dataset.col_count = len(df.columns)
    dataset.save()
    DataRow.objects.bulk_create([
        DataRow(dataset=dataset, row_index=i, data=row.to_dict())
        for i, (_, row) in enumerate(df.iterrows())
    ])


# ════════════════════════════════════════════════════════════════════════════
# 1. UPDATE SINGLE CELL
# ════════════════════════════════════════════════════════════════════════════
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_cell(request, pk):
    """Body: { "row_index": 2, "column": "Salary", "value": 95000 }"""
    try:
        dataset = Dataset.objects.get(pk=pk, owner=request.user)
    except Dataset.DoesNotExist:
        return Response({'error': 'Dataset not found.'}, status=404)

    row_index = request.data.get('row_index')
    column    = request.data.get('column')
    value     = request.data.get('value', '')

    if row_index is None or not column:
        return Response({'error': 'row_index and column required.'}, status=400)
    if column not in dataset.columns:
        return Response({'error': f"Column '{column}' not found."}, status=400)

    try:
        row = DataRow.objects.get(dataset=dataset, row_index=row_index)
        row.data[column] = value
        row.save()
        return Response({'success': True, 'row_index': row_index, 'column': column, 'value': value})
    except DataRow.DoesNotExist:
        return Response({'error': f'Row {row_index} not found.'}, status=404)


# ════════════════════════════════════════════════════════════════════════════
# 2. ADD ROW
# ════════════════════════════════════════════════════════════════════════════
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_row(request, pk):
    """Body (optional): { "data": {"Name": "Rahul", "Salary": 50000} }"""
    try:
        dataset = Dataset.objects.get(pk=pk, owner=request.user)
    except Dataset.DoesNotExist:
        return Response({'error': 'Dataset not found.'}, status=404)

    provided  = request.data.get('data', {})
    full_row  = {col: provided.get(col, '') for col in dataset.columns}
    new_index = DataRow.objects.filter(dataset=dataset).count()

    new_row = DataRow.objects.create(dataset=dataset, row_index=new_index, data=full_row)
    dataset.row_count = new_index + 1
    dataset.save()

    return Response({'success': True, 'row_index': new_row.row_index, 'data': new_row.data}, status=201)


# ════════════════════════════════════════════════════════════════════════════
# 3. DELETE ROW
# ════════════════════════════════════════════════════════════════════════════
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_row(request, pk, row_index):
    try:
        dataset = Dataset.objects.get(pk=pk, owner=request.user)
    except Dataset.DoesNotExist:
        return Response({'error': 'Dataset not found.'}, status=404)

    try:
        DataRow.objects.get(dataset=dataset, row_index=row_index).delete()
        for i, row in enumerate(DataRow.objects.filter(dataset=dataset).order_by('row_index')):
            if row.row_index != i:
                row.row_index = i
                row.save()
        dataset.row_count = DataRow.objects.filter(dataset=dataset).count()
        dataset.save()
        return Response({'success': True})
    except DataRow.DoesNotExist:
        return Response({'error': f'Row {row_index} not found.'}, status=404)


# ════════════════════════════════════════════════════════════════════════════
# 4. ADD COLUMN
# ════════════════════════════════════════════════════════════════════════════
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_column(request, pk):
    """Body: { "column_name": "Bonus", "default_value": "" }"""
    try:
        dataset = Dataset.objects.get(pk=pk, owner=request.user)
    except Dataset.DoesNotExist:
        return Response({'error': 'Dataset not found.'}, status=404)

    col_name    = request.data.get('column_name', f'Column_{len(dataset.columns)+1}')
    default_val = request.data.get('default_value', '')

    if col_name in dataset.columns:
        return Response({'error': f"Column '{col_name}' already exists."}, status=400)

    for row in DataRow.objects.filter(dataset=dataset):
        row.data[col_name] = default_val
        row.save()

    dataset.columns.append(col_name)
    dataset.col_count = len(dataset.columns)
    dataset.save()
    return Response({'success': True, 'columns': dataset.columns})


# ════════════════════════════════════════════════════════════════════════════
# 5. EXCEL FUNCTIONS  (SUM / AVG / MAX / MIN / COUNT / MEDIAN / STDEV)
# ════════════════════════════════════════════════════════════════════════════
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def apply_function(request, pk):
    """
    Body: {
        "function": "SUM",
        "column": "Salary",
        "result_column": "Total_Salary"   <- optional, saves result in new column
    }
    """
    try:
        dataset = Dataset.objects.get(pk=pk, owner=request.user)
    except Dataset.DoesNotExist:
        return Response({'error': 'Dataset not found.'}, status=404)

    fn            = request.data.get('function', '').upper()
    column        = request.data.get('column')
    result_column = request.data.get('result_column')

    SUPPORTED = {'SUM', 'AVG', 'AVERAGE', 'MAX', 'MIN', 'COUNT', 'MEDIAN', 'STDEV', 'VARIANCE'}
    if fn not in SUPPORTED:
        return Response({'error': f"Supported: {', '.join(SUPPORTED)}"}, status=400)

    if not column or column not in dataset.columns:
        return Response({'error': f"Column '{column}' not found."}, status=400)

    rows   = DataRow.objects.filter(dataset=dataset).order_by('row_index')
    values = []
    for row in rows:
        try:
            v = str(row.data.get(column, '')).replace(',', '').replace('$', '').strip()
            values.append(float(v))
        except (ValueError, TypeError):
            pass

    if not values:
        return Response({'error': f"No numeric values in '{column}'."}, status=400)

    arr    = np.array(values)
    result = {
        'SUM':      round(float(np.sum(arr)), 4),
        'AVG':      round(float(np.mean(arr)), 4),
        'AVERAGE':  round(float(np.mean(arr)), 4),
        'MAX':      round(float(np.max(arr)), 4),
        'MIN':      round(float(np.min(arr)), 4),
        'COUNT':    int(len(arr)),
        'MEDIAN':   round(float(np.median(arr)), 4),
        'STDEV':    round(float(np.std(arr)), 4),
        'VARIANCE': round(float(np.var(arr)), 4),
    }[fn]

    if result_column:
        if result_column not in dataset.columns:
            for row in rows:
                row.data[result_column] = ''
                row.save()
            dataset.columns.append(result_column)
            dataset.col_count = len(dataset.columns)
            dataset.save()
        last_row = rows.last()
        if last_row:
            last_row.data[result_column] = result
            last_row.save()

    return Response({'success': True, 'function': fn, 'column': column,
                     'result': result, 'saved_to': result_column})


# ════════════════════════════════════════════════════════════════════════════
# 6. AI PANDAS — Groq AI generated code runs on DataFrame
# ════════════════════════════════════════════════════════════════════════════
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ai_pandas(request, pk):
    """Body: { "code": "df['Bonus'] = df['Salary'].astype(float) * 0.10" }"""
    try:
        dataset = Dataset.objects.get(pk=pk, owner=request.user)
    except Dataset.DoesNotExist:
        return Response({'error': 'Dataset not found.'}, status=404)

    code = request.data.get('code', '').strip()
    if not code:
        return Response({'error': 'No code provided.'}, status=400)

    BLOCKED = ['import os', 'import sys', 'subprocess', 'open(',
               '__import__', 'shutil', 'rmdir', 'unlink', 'socket']
    for b in BLOCKED:
        if b in code:
            return Response({'error': f"Blocked operation: '{b}'"}, status=400)

    try:
        df, _ = _to_df(dataset)
        local_vars = {'df': df, 'pd': pd, 'np': np}
        exec(code, {'pd': pd, 'np': np, '__builtins__': {}}, local_vars)
        df = local_vars.get('df', df)
        _save_df(df, dataset)
        return Response({
            'success':   True,
            'columns':   list(df.columns),
            'row_count': len(df),
            'col_count': len(df.columns),
            'preview':   df.head(5).to_dict(orient='records'),
        })
    except Exception as e:
        return Response({'error': f'Execution failed: {str(e)}'}, status=500)


# ════════════════════════════════════════════════════════════════════════════
# 7. AUTO DASHBOARD — Pure Pandas Analysis (No AI API required)
# ════════════════════════════════════════════════════════════════════════════
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def auto_dashboard(request, pk):
    """
    Automatically analyse a dataset with Pandas and return structured JSON
    for the frontend to render KPI cards, bar chart, line chart, pie chart,
    and a top-performers table.

    Response shape
    --------------
    {
      "meta": { name, rows, cols, numeric_cols, categorical_cols, date_cols, null_pct },
      "kpis": [ { column, sum, mean, min, max, std } ],
      "bar_chart":  { x_col, y_col, labels, values },
      "line_chart": { x_col, y_col, labels, series:[{name, data}] },
      "pie_chart":  { column, labels, values },
      "top_performers": [ {...row dict...} ]
    }
    """
    try:
        dataset = Dataset.objects.get(pk=pk, owner=request.user)
    except Dataset.DoesNotExist:
        return Response({'error': 'Dataset not found.'}, status=404)

    if dataset.status != Dataset.STATUS_READY:
        return Response({'error': f'Dataset not ready (status: {dataset.status}).'}, status=400)

    if dataset.row_count == 0:
        return Response({'error': 'Dataset is empty.'}, status=400)

    # ── Build DataFrame ────────────────────────────────────────────────────
    try:
        rows_qs = DataRow.objects.filter(dataset=dataset).order_by('row_index').values_list('data', flat=True)
        df = pd.DataFrame(list(rows_qs), columns=dataset.columns)
    except Exception as exc:
        return Response({'error': f'Could not build DataFrame: {exc}'}, status=500)

    # ── Column type detection ──────────────────────────────────────────────
    numeric_cols      = []
    categorical_cols  = []
    date_cols         = []

    for col in df.columns:
        series = df[col].dropna()
        if series.empty:
            continue

        # Try numeric conversion first
        converted = pd.to_numeric(series, errors='coerce')
        if converted.notna().sum() / max(len(series), 1) >= 0.7:
            numeric_cols.append(col)
            df[col] = pd.to_numeric(df[col], errors='coerce')
            continue

        # Try date parsing on string cols
        if series.dtype == object:
            try:
                parsed = pd.to_datetime(series, infer_datetime_format=True, errors='coerce')
                if parsed.notna().sum() / max(len(series), 1) >= 0.6:
                    date_cols.append(col)
                    df[col] = parsed
                    continue
            except Exception:
                pass

        # Otherwise categorical
        n_unique = series.nunique()
        if n_unique <= max(50, len(series) * 0.3):
            categorical_cols.append(col)

    # ── Null percentage ────────────────────────────────────────────────────
    total_cells = df.shape[0] * df.shape[1] if df.shape[1] else 1
    null_pct    = round(df.isnull().sum().sum() / total_cells * 100, 2)

    # ── Meta ───────────────────────────────────────────────────────────────
    meta = {
        'name':             dataset.name,
        'rows':             dataset.row_count,
        'cols':             dataset.col_count,
        'numeric_cols':     numeric_cols,
        'categorical_cols': categorical_cols,
        'date_cols':        date_cols,
        'null_pct':         null_pct,
    }

    # ── KPIs (first 3 numeric columns to keep cards manageable) ───────────
    kpis = []
    for col in numeric_cols[:3]:
        s = df[col].dropna()
        if s.empty:
            continue
        kpis.append({
            'column': col,
            'sum':    _safe_scalar(s.sum()),
            'mean':   _safe_scalar(s.mean()),
            'min':    _safe_scalar(s.min()),
            'max':    _safe_scalar(s.max()),
            'std':    _safe_scalar(s.std()),
        })

    # ── Bar chart: first categorical vs first numeric ───────────────────────
    bar_chart = None
    if categorical_cols and numeric_cols:
        x_col = categorical_cols[0]
        y_col = numeric_cols[0]
        grouped = (df[[x_col, y_col]]
                   .dropna()
                   .groupby(x_col, sort=False)[y_col]
                   .sum()
                   .sort_values(ascending=False)
                   .head(15))
        if not grouped.empty:
            bar_chart = {
                'x_col':  x_col,
                'y_col':  y_col,
                'labels': [str(k) for k in grouped.index.tolist()],
                'values': [_safe_scalar(v) for v in grouped.values.tolist()],
            }

    # ── Line chart: date col vs numeric col (trend) ────────────────────────
    line_chart = None
    if date_cols and numeric_cols:
        d_col = date_cols[0]
        y_col = numeric_cols[0]
        tmp   = df[[d_col, y_col]].dropna().copy()
        tmp   = tmp.sort_values(d_col)

        # Group by appropriate frequency
        n = len(tmp)
        if n > 500:
            freq = 'ME'   # monthly
        elif n > 120:
            freq = 'W'    # weekly
        else:
            freq = 'D'    # daily

        try:
            tmp = tmp.set_index(d_col).resample(freq)[y_col].sum().reset_index()
            tmp.columns = [d_col, y_col]
            tmp = tmp.tail(60)  # limit to last 60 periods

            labels = [str(d)[:10] for d in tmp[d_col].tolist()]
            values = [_safe_scalar(v) for v in tmp[y_col].tolist()]

            # Build a rolling-average trend line as second series
            s_arr = tmp[y_col].rolling(window=max(3, len(tmp)//10), min_periods=1).mean()
            trend_vals = [_safe_scalar(v) for v in s_arr.tolist()]

            line_chart = {
                'x_col':  d_col,
                'y_col':  y_col,
                'labels': labels,
                'series': [
                    {'name': y_col,         'data': values},
                    {'name': f'{y_col} Trend', 'data': trend_vals},
                ],
            }
        except Exception:
            pass  # non-critical — just skip the line chart

    # ── Pie chart: first categorical column ───────────────────────────────
    pie_chart = None
    if categorical_cols:
        p_col   = categorical_cols[0]
        counts  = df[p_col].dropna().astype(str).value_counts().head(10)
        if not counts.empty:
            top_labels = counts.index.tolist()
            top_values = counts.values.tolist()
            # Merge tiny slices into "Other"
            total = sum(top_values)
            if len(top_values) > 7:
                threshold = total * 0.02
                filtered  = [(l, v) for l, v in zip(top_labels, top_values) if v >= threshold]
                other_sum = total - sum(v for _, v in filtered)
                if other_sum > 0:
                    filtered.append(('Other', int(other_sum)))
                top_labels = [f[0] for f in filtered]
                top_values = [f[1] for f in filtered]
            pie_chart = {
                'column': p_col,
                'labels': top_labels,
                'values': [int(v) for v in top_values],
            }

    # ── Top 5 performers (sorted by first numeric col descending) ──────────
    top_performers = []
    if numeric_cols:
        sort_col   = numeric_cols[0]
        display_cols = (
            (categorical_cols[:2] if categorical_cols else []) +
            numeric_cols[:3]
        )
        display_cols = display_cols or list(df.columns[:5])

        tmp = df[display_cols].copy()
        tmp[sort_col] = pd.to_numeric(tmp[sort_col], errors='coerce')
        top5 = tmp.sort_values(sort_col, ascending=False).head(5)
        top5 = top5.fillna('')

        for _, row in top5.iterrows():
            entry = {}
            for c in display_cols:
                v = row[c]
                entry[c] = _safe_scalar(v) if isinstance(v, (int, float, np.integer, np.floating)) else str(v)
            top_performers.append(entry)

    return Response({
        'meta':           meta,
        'kpis':           kpis,
        'bar_chart':      bar_chart,
        'line_chart':     line_chart,
        'pie_chart':      pie_chart,
        'top_performers': top_performers,
    })


def _safe_scalar(val):
    """Convert numpy / pandas scalars to plain Python types for JSON serialisation."""
    if val is None:
        return None
    if isinstance(val, (np.integer,)):
        return int(val)
    if isinstance(val, (np.floating,)):
        f = float(val)
        return None if (np.isnan(f) or np.isinf(f)) else round(f, 4)
    if isinstance(val, float):
        return None if (np.isnan(val) or np.isinf(val)) else round(val, 4)
    return val
