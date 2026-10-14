export interface MetricPoint {
  id: string;
  timestamp: string;
  service: string;
  metric_name: string;
  value: number;
  tags: Record<string, string>;
}

export interface MetricRollup {
  count: number;
  avg: number | null;
  min: number | null;
  max: number | null;
}

export interface MetricsSnapshot {
  points: MetricPoint[];
  rollup: MetricRollup;
}
