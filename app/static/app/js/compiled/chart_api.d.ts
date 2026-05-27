import { ChartDataPoint, AdvancedStatsResult, AiInsight } from './api_types.js';
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
export declare function fetchChartData(fileId: number, x: string, y: string, agg?: 'sum' | 'count' | 'mean' | 'min' | 'max'): Promise<ChartDataPoint[]>;
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
export declare function fetchAdvancedStats(fileId: number, col: string, type: 'histogram' | 'boxplot' | 'violin' | 'correlation', extra?: Record<string, string>): Promise<AdvancedStatsResult>;
/**
 * Fetch auto-generated chart suggestions for a dataset.
 *
 * @param fileId  - Primary key of the UploadedFile / CleanedDataset
 * @returns       Array of chart suggestion objects (shape varies per suggestion engine)
 *
 * @example
 * const suggestions = await fetchChartSuggestions(3);
 */
export declare function fetchChartSuggestions(fileId: number): Promise<AiInsight[]>;
