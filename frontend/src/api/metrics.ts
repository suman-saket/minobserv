import type { MetricPoint, MetricRollup, MetricsSnapshot } from "../types/index.ts";

const METRICS_PATH = "/v1/query/metrics";
const ROLLUP_PATH = "/v1/query/metrics/rollup";

/** Load the point list and the rollup for one service and metric name. */
export async function fetchMetricsSnapshot(
  apiUrl: string,
  service: string,
  metricName: string,
): Promise<MetricsSnapshot> {
  const query = new URLSearchParams({
    service,
    name: metricName,
  }).toString();
  const [points, rollup] = await Promise.all([
    getJson(`${apiUrl}${METRICS_PATH}?${query}`, parseMetricPoints),
    getJson(`${apiUrl}${ROLLUP_PATH}?${query}`, parseMetricRollup),
  ]);
  return { points, rollup };
}

/**
 * Read a JSON body and reject it unless it matches the expected shape.
 * A wrong payload should fail here, before the page renders bad numbers.
 */
async function getJson<T>(url: string, parse: (value: unknown) => T): Promise<T> {
  let response: Response;
  try {
    response = await fetch(url);
  } catch (error) {
    const reason = error instanceof Error ? error.message : "unknown network error";
    throw new Error(`Request failed for ${url}: ${reason}`);
  }
  const body = await response.text();
  if (!response.ok) {
    throw new Error(
      `Request failed for ${url}: status ${String(response.status)} ${response.statusText}; body ${body}`,
    );
  }
  let parsed: unknown;
  try {
    parsed = JSON.parse(body);
  } catch (error) {
    const reason = error instanceof Error ? error.message : "invalid JSON";
    throw new Error(`Request failed for ${url}: status ${String(response.status)}; body ${body}; ${reason}`);
  }
  return parse(parsed);
}

function parseMetricPoints(value: unknown): MetricPoint[] {
  if (!Array.isArray(value)) {
    throw new Error("Metrics response is not a list");
  }
  return value.map(parseMetricPoint);
}

function parseMetricPoint(value: unknown): MetricPoint {
  const record = expectRecord(value, "Metric point");
  const metricValue = record.value;
  if (typeof metricValue !== "number") {
    throw new Error("Metric point value must be a number");
  }
  return {
    id: readString(record, "id"),
    timestamp: readString(record, "timestamp"),
    service: readString(record, "service"),
    metric_name: readString(record, "metric_name"),
    value: metricValue,
    tags: readStringRecord(record.tags, "tags"),
  };
}

function parseMetricRollup(value: unknown): MetricRollup {
  const record = expectRecord(value, "Metric rollup");
  const count = record.count;
  if (typeof count !== "number") {
    throw new Error("Metric rollup count must be a number");
  }
  return {
    count,
    avg: readNullableNumber(record, "avg"),
    min: readNullableNumber(record, "min"),
    max: readNullableNumber(record, "max"),
  };
}

function expectRecord(value: unknown, label: string): Record<string, unknown> {
  if (!isRecord(value)) {
    throw new Error(`${label} is not an object`);
  }
  return value;
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function readString(record: Record<string, unknown>, key: string): string {
  const value = record[key];
  if (typeof value !== "string" || value.length === 0) {
    throw new Error(`Expected a non-empty string for ${key}`);
  }
  return value;
}

function readNullableNumber(record: Record<string, unknown>, key: string): number | null {
  const value = record[key];
  if (value === null) {
    return null;
  }
  if (typeof value !== "number") {
    throw new Error(`Expected a number or null for ${key}`);
  }
  return value;
}

function readStringRecord(value: unknown, key: string): Record<string, string> {
  if (typeof value !== "object" || value === null || Array.isArray(value)) {
    throw new Error(`Expected an object of strings for ${key}`);
  }
  const tags: Record<string, string> = {};
  for (const [tagKey, tagValue] of Object.entries(value)) {
    if (typeof tagValue !== "string") {
      throw new Error(`Expected string tag ${tagKey}`);
    }
    tags[tagKey] = tagValue;
  }
  return tags;
}
