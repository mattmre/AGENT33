export type ConnectStatus = "ready" | "attention" | "unknown";

export type ConnectTarget = "models" | "setup" | "mcp" | "tools" | "safety" | "advanced";

export interface ConnectCard {
  id: string;
  title: string;
  plainLabel: string;
  status: ConnectStatus;
  detail: string;
  impact: string;
  actionLabel: string;
  target: ConnectTarget;
}
