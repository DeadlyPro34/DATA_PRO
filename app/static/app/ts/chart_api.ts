// ─────────────────────────────────────────────────────────────────────────────
// chart_api.ts — Typed async API client for DATA_PRO endpoints
// No classes — exported async functions only
// ─────────────────────────────────────────────────────────────────────────────

import {
  ChartDataPoint,
  AdvancedStatsResult,
  AiInsight,
} from './api_types.js';

// ──────────────────────────────────────────────────────────────────────────────
// Helpers
// ──────────────────────────────────────────────────────────────────────────────

/** Read the CSRF token Django embeds in every page cookie. */
function getCsrfToken(): string {
  const match = document.cookie.match(/csrftoken=([^;]+)/);
  return match ? match[1] : '';
}

/** Shared fetch wrapper — throws on non-OK responses with the server's error message. */
async function apiFetch<T>(url: string): Promise<T> {
  const response = await fetch(url, {
    method: 'GET',
    headers: {
      'Accept': 'application/json',
      'X-CSRFToken': getCsrfToken(),
    },
    credentials: 'same-origin',
  });

  if (!response.ok) {
    let message = `HTTP ${response.status}`;
    try {
      const body = await response.json() as { error?: string };
      if (body.error) message = body.error;
    } catch {
      // ignore parse errors on error responses
    }
    throw new Error(message);
  }

  return response.json() as Promise<T>;
}

// ──────────────────────────────────────────────────────────────────────────────
// Public API functions
// ──────────────────────────────────────────────────────────────────────────────

/**
 * Fetch aggregated chart data.
 *
 * @param fileId  - Primary key of the UploadedFile / CleanedDataset
 * @param x       - Column name for the X-axis (grouping column)
 * @param y       - Column name for the Y-axis (value / label column)
 * @param agg     - Aggregation mode: 'sum' | 'count' | 'mean' | 'min' | 'max'
 * @returns       Array of ChartDataPoint objects
 *
 * @example
 * const data = await fetchChartData(3, 'Department', 'Salary', 'mean');
 */
export async function fetchChartData(
  fileId: number,
  x: string,
  y: string,
  agg: 'sum' | 'count' | 'mean' | 'min' | 'max' = 'sum',
): Promise<ChartDataPoint[]> {
  const params = new URLSearchParams({ x, y, agg });
  return apiFetch<ChartDataPoint[]>(`/dataset/${fileId}/chart-data/?${params}`);
}

/**
 * Fetch advanced statistical analysis for a column.
 *
 * @param fileId  - Primary key of the UploadedFile / CleanedDataset
 * @param col     - Column to analyse
 * @param type    - Analysis type: 'histogram' | 'boxplot' | 'violin' | 'correlation'
 * @param extra   - Optional extra params (bins, group, cols)
 * @returns       AdvancedStatsResult — shape depends on `type`
 *
 * @example
 * const hist = await fetchAdvancedStats(3, 'Age', 'histogram', { bins: '30' });
 * const corr = await fetchAdvancedStats(3, '', 'correlation', { cols: 'Age,Salary' });
 */
export async function fetchAdvancedStats(
  fileId: number,
  col: string,
  type: 'histogram' | 'boxplot' | 'violin' | 'correlation',
  extra: Record<string, string> = {},
): Promise<AdvancedStatsResult> {
  const params = new URLSearchParams({ col, type, ...extra });
  return apiFetch<AdvancedStatsResult>(`/dataset/${fileId}/advanced-stats/?${params}`);
}

/**
 * Fetch auto-generated chart suggestions for a dataset.
 *
 * @param fileId  - Primary key of the UploadedFile / CleanedDataset
 * @returns       Array of chart suggestion objects (shape varies per suggestion engine)
 *
 * @example
 * const suggestions = await fetchChartSuggestions(3);
 */
export async function fetchChartSuggestions(fileId: number): Promise<AiInsight[]> {
  return apiFetch<AiInsight[]>(`/dataset/${fileId}/chart-suggestions/`);
}
