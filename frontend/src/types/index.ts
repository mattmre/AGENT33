export type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
export type OperationUxHint = "workflow-execute" | "workflow-schedule" | "agent-iterative" | "workflow-graph" | "health" | "health-channels" | "explanation-html";
export type WorkflowExecutionMode = "single" | "repeat" | "autonomous";

export interface WorkflowExecutePresetProjection {
  pathParams: Record<string, string>;
  body: Record<string, unknown>;
  executionMode?: WorkflowExecutionMode;
}

export interface WorkflowPresetDefinition {
  id: string;
  workflowName: string;
  label: string;
  description: string;
  sourcePath: string;
  workflowDefinition: Record<string, unknown>;
  executePreset: WorkflowExecutePresetProjection;
}

export interface OperationPresetBinding {
  group: "improvement-cycle";
  presetIds: string[];
  helpText?: string;
  applyLabel?: string;
}

export interface SchemaParameter {
  name: string;
  type: string;
  description: string;
  required: boolean;
}

export interface SchemaInfo {
  parameters?: SchemaParameter[];
  body?: {
    description: string;
    example: string;
  };
}

export interface OperationConfig {
  id: string;
  title: string;
  method: HttpMethod;
  path: string;
  description: string;
  instructionalText?: string;
  schemaInfo?: SchemaInfo;
  defaultPathParams?: Record<string, string>;
  defaultQuery?: Record<string, string>;
  defaultBody?: string;
  uxHint?: OperationUxHint;
  presetBinding?: OperationPresetBinding;
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

export interface WorkflowLiveEvent {
  type: string;
  run_id: string;
  workflow_name: string;
  timestamp: number;
  event_id?: string;
  step_id?: string;
  data?: Record<string, unknown>;
}

export interface WorkflowLiveTransportConnection {
  close: () => void;
}
