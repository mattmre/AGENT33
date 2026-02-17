export type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
export type OperationUxHint = "workflow-execute" | "workflow-schedule" | "agent-iterative" | "workflow-graph";

export interface OperationConfig {
  id: string;
  title: string;
  method: HttpMethod;
  path: string;
  description: string;
  defaultPathParams?: Record<string, string>;
  defaultQuery?: Record<string, string>;
  defaultBody?: string;
  uxHint?: OperationUxHint;
}

export interface DomainConfig {
  id: string;
  title: string;
  description: string;
  operations: OperationConfig[];
}

export interface ApiResult {
  status: number;
  durationMs: number;
  url: string;
  data: unknown;
  ok: boolean;
}

export interface RuntimeConfig {
  API_BASE_URL: string;
}
