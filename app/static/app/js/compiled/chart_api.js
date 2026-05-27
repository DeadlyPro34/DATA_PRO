// ─────────────────────────────────────────────────────────────────────────────
// chart_api.ts — Typed async API client for DATA_PRO endpoints
// No classes — exported async functions only
// ─────────────────────────────────────────────────────────────────────────────
var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
// ──────────────────────────────────────────────────────────────────────────────
// Helpers
// ──────────────────────────────────────────────────────────────────────────────
/** Read the CSRF token Django embeds in every page cookie. */
function getCsrfToken() {
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? match[1] : '';
}
/** Shared fetch wrapper — throws on non-OK responses with the server's error message. */
function apiFetch(url) {
    return __awaiter(this, void 0, void 0, function* () {
        const response = yield fetch(url, {
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
                const body = yield response.json();
                if (body.error)
                    message = body.error;
            }
            catch (_a) {
                // ignore parse errors on error responses
            }
            throw new Error(message);
        }
        return response.json();
    });
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
export function fetchChartData(fileId_1, x_1, y_1) {
    return __awaiter(this, arguments, void 0, function* (fileId, x, y, agg = 'sum') {
        const params = new URLSearchParams({ x, y, agg });
        return apiFetch(`/dataset/${fileId}/chart-data/?${params}`);
    });
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
export function fetchAdvancedStats(fileId_1, col_1, type_1) {
    return __awaiter(this, arguments, void 0, function* (fileId, col, type, extra = {}) {
        const params = new URLSearchParams(Object.assign({ col, type }, extra));
        return apiFetch(`/dataset/${fileId}/advanced-stats/?${params}`);
    });
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
export function fetchChartSuggestions(fileId) {
    return __awaiter(this, void 0, void 0, function* () {
        return apiFetch(`/dataset/${fileId}/chart-suggestions/`);
    });
}
//# sourceMappingURL=chart_api.js.map