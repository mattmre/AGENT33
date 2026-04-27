export type StarterKind = "research" | "improvement-loop" | "automation-loop";

export interface WorkflowStarterDraft {
  id: string;
  name: string;
  goal: string;
  kind: StarterKind;
  output: string;
  schedule?: string;
  author?: string;
  sourceLabel?: string;
}

export interface WorkflowStarterRequest {
  name: string;
  version: string;
  description: string;
  triggers: {
    manual: boolean;
    schedule: string | null;
  };
  inputs: Record<string, { type: string; description: string; required: boolean; default?: string }>;
  outputs: Record<string, { type: string; description: string; required: boolean }>;
  steps: Array<{
    id: string;
    name: string;
    action: "invoke-agent" | "validate";
    agent?: string;
    inputs: Record<string, unknown>;
    depends_on: string[];
  }>;
  execution: {
    mode: "dependency-aware";
    continue_on_error: boolean;
    fail_fast: boolean;
    dry_run: boolean;
  };
  metadata: {
    author: string;
    tags: string[];
  };
}

export interface WorkflowCreateResponse {
  name: string;
  version: string;
  step_count: number;
  created: boolean;
}

export interface WorkflowResolutionMatch {
  name: string;
  description: string;
  score: number;
  source: string;
  version: string;
  tags: string[];
  source_path: string;
  pack: string | null;
}

export interface WorkflowResolutionResponse {
  query: string;
  matches: WorkflowResolutionMatch[];
}

export interface SkillDiscoveryMatch {
  name: string;
  description: string;
  score: number;
  version: string;
  tags: string[];
  pack: string | null;
}

export interface SkillDiscoveryResponse {
  query: string;
  matches: SkillDiscoveryMatch[];
}
