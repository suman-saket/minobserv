import type { IngestResult, Level } from "./types/index.js";

const LEVELS: readonly Level[] = ["debug", "info", "warn", "error"];

export class IngestError extends Error {
  readonly url: string;
  readonly status: number | undefined;
  readonly body: string;

  constructor(url: string, status: number | undefined, body: string) {
    super(`Ingest failed for ${url}: status ${String(status)}; body ${body}`);
    this.name = "IngestError";
    this.url = url;
    this.status = status;
    this.body = body;
  }
}

export class Client {
  readonly baseUrl: string;
  readonly service: string;
  readonly timeoutSeconds: number;

  constructor(baseUrl: string, service: string, timeoutSeconds: number) {
    if (baseUrl.trim() === "") {
      throw new Error("baseUrl is required");
    }
    if (service.trim() === "") {
      throw new Error("service is required");
    }
    if (!(timeoutSeconds > 0)) {
      throw new Error("timeoutSeconds must be greater than 0");
    }
    this.baseUrl = baseUrl.replace(/\/$/, "");
    this.service = service;
    this.timeoutSeconds = timeoutSeconds;
  }

  async log(
    level: Level,
    message: string,
    requestId: string,
    label: Record<string, string>,
  ): Promise<IngestResult> {
    if (!isLevel(level)) {
      throw new Error(`level must be one of ${LEVELS.join(", ")}; got ${level}`);
    }
    requireText(message, "message");
    requireText(requestId, "requestId");
    requireStringMap(label, "label");
    const body = [
      {
        timestamp: new Date().toISOString(),
        service: this.service,
        level,
        message,
        request_id: requestId,
        label,
      },
    ];
    return postJson(`${this.baseUrl}/v1/ingest/logs`, body, this.timeoutSeconds);
  }

  async metric(name: string, value: number, tags: Record<string, string>): Promise<IngestResult> {
    requireText(name, "name");
    if (typeof value !== "number" || !Number.isFinite(value)) {
      throw new Error("value must be a number");
    }
    requireStringMap(tags, "tags");
    const body = [
      {
        timestamp: new Date().toISOString(),
        service: this.service,
        metric_name: name,
        value,
        tags,
      },
    ];
    return postJson(`${this.baseUrl}/v1/ingest/metrics`, body, this.timeoutSeconds);
  }
}

function isLevel(value: string): value is Level {
  return LEVELS.some((level) => level === value);
}

function requireText(value: string, field: string): void {
  if (value.trim() === "") {
    throw new Error(`${field} is required`);
  }
}

function requireStringMap(value: Record<string, string>, field: string): void {
  for (const item of Object.values(value)) {
    if (typeof item !== "string") {
      throw new Error(`${field} must be a map of strings`);
    }
  }
}

/**
 * Send one ingest batch and include the URL, status, and body when it fails.
 * Both log and metric use this so the JSON field names stay in one place.
 */
async function postJson(
  url: string,
  body: readonly object[],
  timeoutSeconds: number,
): Promise<IngestResult> {
  let response: Response;
  try {
    response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: AbortSignal.timeout(timeoutSeconds * 1000),
    });
  } catch (error) {
    const reason = error instanceof Error ? error.message : "unknown network error";
    throw new IngestError(url, undefined, reason);
  }
  const raw = await response.text();
  if (!response.ok) {
    throw new IngestError(url, response.status, raw);
  }
  return parseResult(url, response.status, raw);
}

function parseResult(url: string, status: number, raw: string): IngestResult {
  let parsed: unknown;
  try {
    parsed = JSON.parse(raw);
  } catch (error) {
    const reason = error instanceof Error ? error.message : "invalid JSON";
    throw new IngestError(url, status, `${raw}; ${reason}`);
  }
  if (!isRecord(parsed)) {
    throw new IngestError(url, status, raw);
  }
  const inserted = parsed.inserted;
  const ids = parsed.ids;
  if (typeof inserted !== "number" || !Number.isInteger(inserted) || !Array.isArray(ids)) {
    throw new IngestError(url, status, raw);
  }
  const stringIds: string[] = [];
  for (const item of ids) {
    if (typeof item !== "string") {
      throw new IngestError(url, status, raw);
    }
    stringIds.push(item);
  }
  return { inserted, ids: stringIds };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
