export function formatTimestamp(iso: string): string {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) {
    return iso;
  }
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "medium",
  }).format(date);
}

export function formatMetricValue(value: number | null): string {
  if (value === null) {
    return "—";
  }
  return new Intl.NumberFormat(undefined, {
    maximumFractionDigits: 2,
  }).format(value);
}

export function formatTags(tags: Record<string, string>): string {
  const entries = Object.entries(tags);
  if (entries.length === 0) {
    return "—";
  }
  return entries.map(([key, value]) => `${key}=${value}`).join(", ");
}
