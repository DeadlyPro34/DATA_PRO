"""
ai_insights.py — Heuristic-based data insight generator for DATA_PRO
=====================================================================

Analyses a cleaned DataFrame, its health report, and per-column stats
to produce a list of insight dicts suitable for the frontend.

Uses pandas and numpy only — no external AI / LLM APIs.

Author: DATA_PRO
"""

from __future__ import annotations

import logging
import math
from typing import Any

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


def _safe(value: Any) -> Any:
    """Convert numpy scalars to native Python types for JSON serialisation."""
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, (np.floating, float)):
        f = float(value)
        if not math.isfinite(f):
            return None
        return round(f, 6)
    if isinstance(value, np.bool_):
        return bool(value)
    if isinstance(value, (int, bool, str)):
        return value
    return str(value)


def generate_insights(
    df: pd.DataFrame,
    health_report: dict,
    stats: dict,
) -> list[dict]:
    """
    Return a list of insight dicts for the frontend.

    Each insight has the shape::

        {
            'type': 'info' | 'warning' | 'suggestion',
            'icon': str,
            'title': str,
            'description': str,
            'confidence': float,   # 0.0 – 1.0
        }

    Parameters
    ----------
    df : pd.DataFrame
        The **cleaned** DataFrame.
    health_report : dict
        Output of ``_compute_health_report()`` from ``data_cleaner.py``.
    stats : dict
        Per-column descriptive statistics.
    """
    insights: list[dict] = []

    if df.empty:
        insights.append({
            'type': 'info',
            'icon': '📊',
            'title': 'Empty dataset',
            'description': 'The dataset has no rows after cleaning.',
            'confidence': 1.0,
        })
        return insights

    try:
        insights.extend(_missing_data_insights(df, health_report))
    except Exception as exc:
        logger.debug("missing_data insights failed: %s", exc)

    try:
        insights.extend(_outlier_insights(df))
    except Exception as exc:
        logger.debug("outlier insights failed: %s", exc)

    try:
        insights.extend(_column_type_insights(df, health_report))
    except Exception as exc:
        logger.debug("column_type insights failed: %s", exc)

    try:
        insights.extend(_correlation_insights(df))
    except Exception as exc:
        logger.debug("correlation insights failed: %s", exc)

    try:
        insights.extend(_skew_insights(df))
    except Exception as exc:
        logger.debug("skew insights failed: %s", exc)

    try:
        insights.extend(_chart_recommendation_insights(df))
    except Exception as exc:
        logger.debug("chart_recommendation insights failed: %s", exc)

    try:
        insights.extend(_data_shape_insights(df, health_report))
    except Exception as exc:
        logger.debug("data_shape insights failed: %s", exc)

    try:
        insights.extend(_duplicate_insights(health_report))
    except Exception as exc:
        logger.debug("duplicate insights failed: %s", exc)

    try:
        insights.extend(_high_cardinality_insights(df))
    except Exception as exc:
        logger.debug("high_cardinality insights failed: %s", exc)

    try:
        insights.extend(_constant_column_insights(df))
    except Exception as exc:
        logger.debug("constant_column insights failed: %s", exc)

    try:
        insights.extend(_trend_insights(df, health_report))
    except Exception as exc:
        logger.debug("trend insights failed: %s", exc)

    try:
        insights.extend(_anomaly_insights(df))
    except Exception as exc:
        logger.debug("anomaly insights failed: %s", exc)

    try:
        insights.extend(_summary_insight(df, health_report, stats))
    except Exception as exc:
        logger.debug("summary insight failed: %s", exc)

    return insights


# ──────────────────────────────────────────────────────────────────────────────
# INDIVIDUAL INSIGHT GENERATORS
# ──────────────────────────────────────────────────────────────────────────────

def _missing_data_insights(df: pd.DataFrame, health_report: dict) -> list[dict]:
    """For each column with >5 % missing, generate a warning."""
    results: list[dict] = []
    total_rows = len(df)
    if total_rows == 0:
        return results

    missing_by_col: dict = health_report.get('missing_by_column', {})
    for col, count in missing_by_col.items():
        pct = count / total_rows * 100
        if pct > 5:
            results.append({
                'type': 'warning',
                'icon': '⚠️',
                'title': f'High missing data in "{col}"',
                'description': (
                    f'Column "{col}" has {_safe(count)} missing values '
                    f'({_safe(round(pct, 1))}% of rows). Consider imputation '
                    f'or removal depending on your analysis goals.'
                ),
                'confidence': _safe(min(0.5 + pct / 100, 1.0)),
            })
    return results


def _outlier_insights(df: pd.DataFrame) -> list[dict]:
    """For each numeric column, use IQR method to detect outliers."""
    results: list[dict] = []
    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    for col in numeric_cols:
        series = df[col].dropna()
        if len(series) < 4:
            continue
        q1 = float(series.quantile(0.25))
        q3 = float(series.quantile(0.75))
        iqr = q3 - q1
        if iqr == 0:
            continue
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outlier_count = int(((series < lower) | (series > upper)).sum())
        if outlier_count > 0:
            pct = outlier_count / len(series) * 100
            results.append({
                'type': 'warning' if pct > 5 else 'info',
                'icon': '🔍',
                'title': f'Outliers detected in "{col}"',
                'description': (
                    f'{_safe(outlier_count)} outlier(s) detected in "{col}" '
                    f'({_safe(round(pct, 1))}% of values) using the IQR method '
                    f'(range: {_safe(round(lower, 2))} – {_safe(round(upper, 2))}).'
                ),
                'confidence': _safe(min(0.6 + pct / 200, 1.0)),
            })
    return results


def _column_type_insights(df: pd.DataFrame, health_report: dict) -> list[dict]:
    """Report detected date columns and pure numeric columns."""
    results: list[dict] = []
    date_cols = health_report.get('date_columns', [])
    numeric_cols = health_report.get('numeric_columns', [])

    if date_cols:
        results.append({
            'type': 'info',
            'icon': '📅',
            'title': 'Date columns detected',
            'description': (
                f'Detected {len(date_cols)} date-like column(s): '
                f'{", ".join(date_cols[:10])}.'
            ),
            'confidence': 0.8,
        })
    if numeric_cols:
        results.append({
            'type': 'info',
            'icon': '📊',
            'title': 'Numeric columns detected',
            'description': (
                f'Found {len(numeric_cols)} numeric column(s): '
                f'{", ".join(numeric_cols[:10])}. '
                f'These are suitable for statistical analysis and charting.'
            ),
            'confidence': 1.0,
        })
    return results


def _correlation_insights(df: pd.DataFrame) -> list[dict]:
    """For pairs of numeric columns, report |correlation| > 0.7."""
    results: list[dict] = []
    numeric_df = df.select_dtypes(include='number')
    if numeric_df.shape[1] < 2:
        return results

    # Limit to first 20 numeric columns to avoid O(n²) explosion
    cols = numeric_df.columns.tolist()[:20]
    try:
        corr_matrix = numeric_df[cols].corr(method='pearson')
    except Exception:
        return results

    seen: set[tuple[str, str]] = set()
    for i, c1 in enumerate(cols):
        for j, c2 in enumerate(cols):
            if i >= j:
                continue
            pair = (c1, c2)
            if pair in seen:
                continue
            seen.add(pair)
            val = corr_matrix.loc[c1, c2]
            try:
                if pd.isna(val):
                    continue
            except (TypeError, ValueError):
                continue
            abs_val = abs(float(val))
            if abs_val > 0.7:
                direction = 'positively' if val > 0 else 'negatively'
                results.append({
                    'type': 'suggestion',
                    'icon': '🔗',
                    'title': f'Strong correlation: {c1} ↔ {c2}',
                    'description': (
                        f'"{c1}" and "{c2}" are strongly {direction} correlated '
                        f'(r = {_safe(round(float(val), 3))}). '
                        f'Consider a scatter plot to visualise this relationship.'
                    ),
                    'confidence': _safe(round(abs_val, 3)),
                })
    return results


def _skew_insights(df: pd.DataFrame) -> list[dict]:
    """For numeric columns, report if |skewness| > 1.5."""
    results: list[dict] = []
    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    for col in numeric_cols:
        series = df[col].dropna()
        if len(series) < 3:
            continue
        try:
            skew_val = float(series.skew())
        except Exception:
            continue
        if not math.isfinite(skew_val):
            continue
        if abs(skew_val) > 1.5:
            direction = 'right-skewed (positive)' if skew_val > 0 else 'left-skewed (negative)'
            results.append({
                'type': 'info',
                'icon': '📊',
                'title': f'Skewed distribution in "{col}"',
                'description': (
                    f'Column "{col}" is {direction} with a skewness of '
                    f'{_safe(round(skew_val, 3))}. Consider log or square-root '
                    f'transformation if using in regression models.'
                ),
                'confidence': _safe(round(min(abs(skew_val) / 5, 1.0), 3)),
            })
    return results


def _chart_recommendation_insights(df: pd.DataFrame) -> list[dict]:
    """Based on column types, suggest appropriate chart types."""
    results: list[dict] = []
    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    categorical_cols = df.select_dtypes(include='object').columns.tolist()

    suggestions: list[str] = []

    if len(numeric_cols) >= 2:
        suggestions.append(
            f'Scatter plot: compare any two numeric columns '
            f'(e.g. "{numeric_cols[0]}" vs "{numeric_cols[1]}").'
        )
    if len(numeric_cols) >= 1:
        suggestions.append(
            f'Histogram: view distribution of "{numeric_cols[0]}" or other numeric columns.'
        )
    if categorical_cols and numeric_cols:
        suggestions.append(
            f'Bar chart: group "{numeric_cols[0]}" by '
            f'"{categorical_cols[0]}" for aggregated comparison.'
        )
    if len(numeric_cols) >= 3:
        suggestions.append('Correlation heatmap: visualise relationships across all numeric columns.')

    if suggestions:
        results.append({
            'type': 'suggestion',
            'icon': '💡',
            'title': 'Chart recommendations',
            'description': ' • '.join(suggestions),
            'confidence': 0.7,
        })
    return results


def _data_shape_insights(df: pd.DataFrame, health_report: dict) -> list[dict]:
    """Report dataset dimensions and column type breakdown."""
    results: list[dict] = []
    rows = len(df)
    cols = len(df.columns)
    n_numeric = len(health_report.get('numeric_columns', []))
    n_categorical = len(health_report.get('categorical_columns', []))
    n_date = len(health_report.get('date_columns', []))

    description = (
        f'Dataset has {_safe(rows)} rows and {_safe(cols)} columns: '
        f'{_safe(n_numeric)} numeric, {_safe(n_categorical)} categorical'
    )
    if n_date:
        description += f', {_safe(n_date)} date-like'
    description += '.'

    results.append({
        'type': 'info',
        'icon': '📊',
        'title': 'Dataset overview',
        'description': description,
        'confidence': 1.0,
    })
    return results


def _duplicate_insights(health_report: dict) -> list[dict]:
    """If duplicates were found, report them."""
    results: list[dict] = []
    dup_count = health_report.get('duplicate_rows', 0)
    if dup_count and dup_count > 0:
        results.append({
            'type': 'warning',
            'icon': '⚠️',
            'title': 'Duplicate rows detected',
            'description': (
                f'{_safe(dup_count)} exact duplicate row(s) were found in the '
                f'original data. These have been removed during cleaning.'
            ),
            'confidence': 1.0,
        })
    return results


def _high_cardinality_insights(df: pd.DataFrame) -> list[dict]:
    """If a categorical column has >50 unique values, note it."""
    results: list[dict] = []
    cat_cols = df.select_dtypes(include='object').columns.tolist()
    for col in cat_cols:
        nunique = int(df[col].nunique())
        if nunique > 50:
            results.append({
                'type': 'info',
                'icon': '🔍',
                'title': f'High cardinality in "{col}"',
                'description': (
                    f'Column "{col}" has {_safe(nunique)} unique values. '
                    f'This may not be ideal for grouping or bar charts. '
                    f'Consider filtering or binning.'
                ),
                'confidence': 0.8,
            })
    return results


def _constant_column_insights(df: pd.DataFrame) -> list[dict]:
    """If a column has only 1 unique value, note it."""
    results: list[dict] = []
    for col in df.columns:
        nunique = int(df[col].nunique(dropna=True))
        if nunique <= 1 and len(df) > 0:
            results.append({
                'type': 'warning',
                'icon': '⚠️',
                'title': f'Constant column: "{col}"',
                'description': (
                    f'Column "{col}" has only {_safe(nunique)} unique value(s). '
                    f'It provides no variation and may be removed without data loss.'
                ),
                'confidence': 1.0,
            })
    return results

def _trend_insights(df: pd.DataFrame, health_report: dict) -> list[dict]:
    import scipy.stats as stats
    results: list[dict] = []
    date_cols = health_report.get('date_columns', [])
    numeric_cols = health_report.get('numeric_columns', [])
    if not date_cols or not numeric_cols:
        return results

    date_col = date_cols[0]
    for num_col in numeric_cols:
        sub = df[[date_col, num_col]].dropna()
        if len(sub) < 5:
            continue
        try:
            x = pd.to_datetime(sub[date_col], format='mixed').astype('int64') // 10**9
            y = sub[num_col]
            slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
            if p_value < 0.05:
                trend = 'upward' if slope > 0 else 'downward'
                results.append({
                    'type': 'info',
                    'icon': '📈' if slope > 0 else '📉',
                    'title': f'Trend detected: {num_col}',
                    'description': f'"{num_col}" is trending {trend} over time.',
                    'confidence': _safe(1 - p_value)
                })
        except Exception:
            pass
    return results

def _anomaly_insights(df: pd.DataFrame) -> list[dict]:
    results: list[dict] = []
    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    for col in numeric_cols:
        series = df[col].dropna()
        if len(series) < 3:
            continue
        mean = series.mean()
        std = series.std()
        if std == 0:
            continue
        z_scores = (series - mean) / std
        anomalies = int((z_scores.abs() > 3).sum())
        if anomalies > 0:
            results.append({
                'type': 'warning',
                'icon': '🚨',
                'title': f'Anomalies in "{col}"',
                'description': f'Found {_safe(anomalies)} values more than 3 standard deviations from the mean in "{col}".',
                'confidence': 0.95
            })
    return results

def _summary_insight(df: pd.DataFrame, health_report: dict, stats: dict) -> list[dict]:
    results: list[dict] = []
    numeric_cols = health_report.get('numeric_columns', [])
    for col in numeric_cols:
        series = df[col].dropna()
        if len(series) < 4:
            continue
        
        # calculate outliers
        q1 = float(series.quantile(0.25))
        q3 = float(series.quantile(0.75))
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outliers = int(((series < lower) | (series > upper)).sum())
        
        # simple check for trend via sorted dates if any
        trend_str = ""
        date_cols = health_report.get('date_columns', [])
        if date_cols:
            date_col = date_cols[0]
            sub = df[[date_col, col]].dropna()
            try:
                import scipy.stats
                x = pd.to_datetime(sub[date_col], format='mixed').astype('int64') // 10**9
                slope, _, _, p_value, _ = scipy.stats.linregress(x, sub[col])
                if p_value < 0.05:
                    trend_str = " and is trending upward" if slope > 0 else " and is trending downward"
            except Exception:
                pass
                
        results.append({
            'type': 'info',
            'icon': '📝',
            'title': f'{col} Summary',
            'description': f'{col} has {_safe(outliers)} outliers{trend_str}.',
            'confidence': 1.0
        })
    return results
