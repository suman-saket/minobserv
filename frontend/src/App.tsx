import { useState } from "react";
import type { FormEvent } from "react";
import { fetchMetricsSnapshot } from "./api/metrics.ts";
import { formatMetricValue, formatTags, formatTimestamp } from "./format.ts";
import type { MetricsSnapshot } from "./types/index.ts";

type LoadState =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; snapshot: MetricsSnapshot };

export function App() {
  const apiUrl = import.meta.env.VITE_API_URL;
  if (typeof apiUrl !== "string" || apiUrl.length === 0) {
    return (
      <main className="page">
        <p className="error">
          Set VITE_API_URL. Copy frontend/.env.example to frontend/.env.
        </p>
      </main>
    );
  }
  return <MetricsPage apiUrl={apiUrl} />;
}

function MetricsPage({ apiUrl }: { apiUrl: string }) {
  const [service, setService] = useState("");
  const [metricName, setMetricName] = useState("");
  const [loadState, setLoadState] = useState<LoadState>({ status: "idle" });

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const serviceName = service.trim();
    const name = metricName.trim();
    if (serviceName.length === 0 || name.length === 0) {
      setLoadState({
        status: "error",
        message: "Service and metric name are required.",
      });
      return;
    }
    setLoadState({ status: "loading" });
    try {
      const snapshot = await fetchMetricsSnapshot(apiUrl, serviceName, name);
      setLoadState({ status: "ready", snapshot });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Could not load metrics.";
      setLoadState({ status: "error", message });
    }
  }

  return (
    <main className="page">
      <header className="header">
        <p className="eyebrow">Observability</p>
        <h1>Metrics</h1>
      </header>
      <form className="filters" onSubmit={handleSubmit}>
        <label>
          Service
          <input
            value={service}
            onChange={(event) => {
              setService(event.target.value);
            }}
          />
        </label>
        <label>
          Metric name
          <input
            value={metricName}
            onChange={(event) => {
              setMetricName(event.target.value);
            }}
          />
        </label>
        <button type="submit" disabled={loadState.status === "loading"}>
          {loadState.status === "loading" ? "Loading" : "Load"}
        </button>
      </form>
      {loadState.status === "error" ? <p className="error">{loadState.message}</p> : null}
      {loadState.status === "ready" ? <MetricsResult snapshot={loadState.snapshot} /> : null}
    </main>
  );
}

function MetricsResult({ snapshot }: { snapshot: MetricsSnapshot }) {
  if (snapshot.rollup.count === 0) {
    return <p className="empty">No points stored for that service and metric name.</p>;
  }
  return (
    <>
      <section className="rollup" aria-label="Rollup">
        <RollupStat label="Count" value={String(snapshot.rollup.count)} />
        <RollupStat label="Average" value={formatMetricValue(snapshot.rollup.avg)} />
        <RollupStat label="Min" value={formatMetricValue(snapshot.rollup.min)} />
        <RollupStat label="Max" value={formatMetricValue(snapshot.rollup.max)} />
      </section>
      <table>
        <thead>
          <tr>
            <th>Time</th>
            <th>Value</th>
            <th>Tags</th>
          </tr>
        </thead>
        <tbody>
          {snapshot.points.map((point) => (
            <tr key={point.id}>
              <td>{formatTimestamp(point.timestamp)}</td>
              <td>{formatMetricValue(point.value)}</td>
              <td>{formatTags(point.tags)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </>
  );
}

function RollupStat({ label, value }: { label: string; value: string }) {
  return (
    <article>
      <p>{label}</p>
      <strong>{value}</strong>
    </article>
  );
}
