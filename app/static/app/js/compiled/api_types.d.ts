/** The X-axis group value — can be any serialisable primitive */
export type XValue = string | number | boolean | null;
/** Returned when agg=sum|mean|min|max */
export interface ChartDataPointNumeric {
    /** The X-axis column value for this group */
    x_value: XValue;
    /** The name of the X-axis column (dynamic — e.g. "Department") */
    x_col: string;
    result: number;
}
/** Returned when agg=count */
export interface ChartDataPointCount {
    /** The X-axis column value for this group */
    x_value: XValue;
    /** The name of the X-axis column (dynamic — e.g. "Marks") */
    x_col: string;
    count: number;
    /** Array of member label values (e.g. student names) */
    students: string[];
    /** Which column was used to collect member labels */
    label_col: string;
}
/** Union type covering both aggregation shapes */
export type ChartDataPoint = ChartDataPointNumeric | ChartDataPointCount;
export interface HistogramBin {
    x0: number | null;
    x1: number | null;
    count: number;
    density: number | null;
}
export interface HistogramStats {
    mean: number | null;
    std: number | null;
    min: number | null;
    max: number | null;
}
/** Returned when type=histogram */
export interface HistogramResult {
    bins: HistogramBin[];
    stats: HistogramStats;
}
export interface BoxplotGroup {
    name: string;
    q1: number | null;
    q2: number | null;
    q3: number | null;
    min: number | null;
    max: number | null;
    mean: number | null;
    outliers: number[];
}
/** Returned when type=boxplot */
export interface BoxplotResult {
    groups: BoxplotGroup[];
}
export interface KdePoint {
    x: number;
    density: number;
}
export interface ViolinGroup {
    name: string;
    kde: KdePoint[];
    q1: number | null;
    q2: number | null;
    q3: number | null;
    min: number | null;
    max: number | null;
}
/** Returned when type=violin */
export interface ViolinResult {
    groups: ViolinGroup[];
}
/** Returned when type=correlation */
export interface CorrelationResult {
    columns: string[];
    matrix: (number | null)[][];
}
/** Union of all advanced-stats response shapes */
export type AdvancedStatsResult = HistogramResult | BoxplotResult | ViolinResult | CorrelationResult;
export type InsightType = 'info' | 'warning' | 'error' | 'success';
export type InsightSeverity = 'low' | 'medium' | 'high' | 'critical';
export interface AiInsight {
    type: InsightType;
    icon: string;
    title: string;
    description: string;
    confidence: number;
    severity?: InsightSeverity;
    column?: string;
    value?: number | string;
}
