export type Level = "debug" | "info" | "warn" | "error";

export interface IngestResult {
  inserted: number;
  ids: string[];
}
