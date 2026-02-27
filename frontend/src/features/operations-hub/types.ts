export interface OperationsHubProcessSummary {
  id: string;
  type: string;
  status: string;
  started_at: string;
  name: string;
  metadata?: Record<string, unknown>;
}

export interface OperationsHubResponse {
  timestamp: string;
  active_count: number;
  processes: OperationsHubProcessSummary[];
}

export interface OperationsHubProcessAction {
  step_id: string;
  action_count: number;
  completed_at: string | null;
}

export interface OperationsHubProcessDetail extends OperationsHubProcessSummary {
  actions?: OperationsHubProcessAction[];
}

export type OperationsHubControlAction = "pause" | "resume" | "cancel";
