import type {
  OperationPresetBinding,
  WorkflowExecutePresetProjection,
  WorkflowPresetDefinition
} from "../../types";

const retrospectiveWorkflowDefinition = {
  name: "improvement-cycle-retrospective",
  version: "1.0.0",
  description: "Deterministic retrospective scaffold for session or milestone improvement reviews.",
  triggers: {
    manual: true,
    on_event: ["session-end"]
  },
  inputs: {
    session_id: {
      type: "string",
      description: "Session or milestone identifier being reviewed.",
      required: true
    },
    scope: {
      type: "string",
      description: "Area or stream being reviewed.",
      default: "full-delivery"
    },
    participants: {
      type: "array",
      description: "Participants or roles included in the retrospective.",
      default: ["facilitator", "reviewer", "implementer"]
    },
    evidence_sources: {
      type: "array",
      description: "Evidence sources reviewed during the retrospective.",
      default: ["merged PRs", "test runs", "review notes"]
    },
    wins: {
      type: "array",
      description: "Concrete wins captured from the session.",
      default: []
    },
    improvement_areas: {
      type: "array",
      description: "Concrete issues to address next.",
      default: []
    }
  },
  outputs: {
    result: {
      type: "object",
      description: "Prepared retrospective scaffold with summary, prompts, and markdown output."
    }
  },
  steps: [
    {
      id: "validate",
      name: "Validate required retrospective input",
      action: "validate",
      inputs: {
        data: "session_id",
        expression: "'data'"
      }
    },
    {
      id: "collect",
      name: "Normalize retrospective context",
      action: "transform",
      depends_on: ["validate"],
      inputs: {
        data: {
          session_id: "session_id",
          scope: "scope",
          participants: "participants",
          evidence_sources: "evidence_sources",
          wins: "wins",
          improvement_areas: "improvement_areas"
        }
      }
    },
    {
      id: "summarize",
      name: "Produce retrospective scaffold outputs",
      action: "transform",
      depends_on: ["collect"],
      inputs: {
        data: {
          status: "'ready'",
          summary: "'Retrospective scaffold prepared for ' ~ collect.result.session_id",
          action_items: [
            "'Assign an owner for the top improvement area.'",
            "'Carry one process change into the next session plan.'"
          ],
          report_markdown: `## Retrospective: {{ collect.result.session_id }}

### Scope
- {{ collect.result.scope or 'full-delivery' }}

### Participants
{% for participant in collect.result.participants or ['facilitator', 'reviewer', 'implementer'] %}
- {{ participant }}
{% endfor %}

### Wins
{% for item in collect.result.wins or ['Document one concrete success from the session.'] %}
- {{ item }}
{% endfor %}

### Improvement Areas
{% for item in collect.result.improvement_areas or ['Document one concrete improvement area for the next session.'] %}
- {{ item }}
{% endfor %}

### Evidence Reviewed
{% for item in collect.result.evidence_sources or ['merged PRs', 'test runs', 'review notes'] %}
- {{ item }}
{% endfor %}

### Next Actions
1. Assign an owner for the top improvement area.
2. Carry one process change into the next session plan.`
        }
      }
    }
  ],
  execution: {
    mode: "dependency-aware",
    fail_fast: true
  },
  metadata: {
    author: "implementer",
    created: "2026-03-06",
    updated: "2026-03-06",
    tags: ["improvement-cycle", "retrospective", "template"]
  }
};

const metricsReviewWorkflowDefinition = {
  name: "improvement-cycle-metrics-review",
  version: "1.0.0",
  description: "Deterministic metrics review scaffold for recurring improvement checkpoints.",
  triggers: {
    manual: true,
    schedule: "weekly"
  },
  inputs: {
    review_period: {
      type: "string",
      description: "Time range being reviewed.",
      required: true
    },
    baseline_period: {
      type: "string",
      description: "Optional comparison period.",
      default: "previous comparable period"
    },
    focus_areas: {
      type: "array",
      description: "Metric categories to prioritize.",
      default: ["build-health", "test-coverage", "api-alignment"]
    },
    metrics_snapshot: {
      type: "object",
      description: "Optional structured metric values already collected for the review.",
      default: {}
    },
    regression_threshold_percent: {
      type: "integer",
      description: "Threshold for flagging regressions.",
      default: 10
    }
  },
  outputs: {
    result: {
      type: "object",
      description: "Prepared metrics review scaffold with summary, prompts, and markdown output."
    }
  },
  steps: [
    {
      id: "validate",
      name: "Validate required review period input",
      action: "validate",
      inputs: {
        data: "review_period",
        expression: "'data'"
      }
    },
    {
      id: "collect",
      name: "Normalize metrics review context",
      action: "transform",
      depends_on: ["validate"],
      inputs: {
        data: {
          review_period: "review_period",
          baseline_period: "baseline_period",
          focus_areas: "focus_areas",
          metrics_snapshot: "metrics_snapshot",
          regression_threshold_percent: "regression_threshold_percent"
        }
      }
    },
    {
      id: "summarize",
      name: "Produce metrics review scaffold outputs",
      action: "transform",
      depends_on: ["collect"],
      inputs: {
        data: {
          status: "'ready'",
          summary: "'Metrics review scaffold prepared for ' ~ collect.result.review_period",
          recommendation_prompts: [
            "'Investigate regressions above the agreed threshold.'",
            "'Record one concrete recommendation for the next review.'"
          ],
          report_markdown: `## Metrics Review: {{ collect.result.review_period }}

### Baseline
- {{ collect.result.baseline_period or 'previous comparable period' }}

### Focus Areas
{% for area in collect.result.focus_areas or ['build-health', 'test-coverage', 'api-alignment'] %}
- {{ area }}
{% endfor %}

### Metrics Snapshot
{% if collect.result.metrics_snapshot %}
{% for key, value in collect.result.metrics_snapshot.items() %}
- **{{ key }}**: {{ value }}
{% endfor %}
{% else %}
- Add collected metric values for this review period.
{% endif %}

### Review Prompts
1. Flag regressions greater than {{ collect.result.regression_threshold_percent or 10 }}%.
2. Record one concrete recommendation for each focus area.`
        }
      }
    }
  ],
  execution: {
    mode: "dependency-aware",
    fail_fast: true
  },
  metadata: {
    author: "implementer",
    created: "2026-03-06",
    updated: "2026-03-06",
    tags: ["improvement-cycle", "metrics", "template"]
  }
};

export const improvementCycleWorkflowPresets: readonly WorkflowPresetDefinition[] = [
  {
    id: "retrospective",
    workflowName: retrospectiveWorkflowDefinition.name,
    label: "Retrospective improvement cycle",
    description: "Create or run a deterministic retrospective scaffold for a completed session.",
    sourcePath: "core/workflows/improvement-cycle/retrospective.workflow.yaml",
    workflowDefinition: retrospectiveWorkflowDefinition,
    executePreset: {
      pathParams: { name: retrospectiveWorkflowDefinition.name },
      body: {
        inputs: {
          session_id: "session-57",
          scope: "frontend",
          participants: ["implementer", "reviewer"],
          wins: ["Live workflow graph refresh shipped."],
          improvement_areas: ["Tighten template drift checks."]
        }
      },
      executionMode: "single"
    }
  },
  {
    id: "metrics-review",
    workflowName: metricsReviewWorkflowDefinition.name,
    label: "Metrics review improvement cycle",
    description: "Create or run a deterministic metrics review scaffold for a review period.",
    sourcePath: "core/workflows/improvement-cycle/metrics-review.workflow.yaml",
    workflowDefinition: metricsReviewWorkflowDefinition,
    executePreset: {
      pathParams: { name: metricsReviewWorkflowDefinition.name },
      body: {
        inputs: {
          review_period: "2026-03-01 to 2026-03-07",
          baseline_period: "2026-02-23 to 2026-02-29",
          focus_areas: ["build-health", "api-alignment"],
          metrics_snapshot: {
            build_pass_rate: "98%",
            api_mismatches: 0
          }
        }
      },
      executionMode: "single"
    }
  }
];

export const improvementCyclePresetBinding: OperationPresetBinding = {
  group: "improvement-cycle",
  presetIds: improvementCycleWorkflowPresets.map((preset) => preset.id),
  helpText:
    "Apply a canonical improvement-cycle template from core/workflows/improvement-cycle/*.workflow.yaml."
};

export function getImprovementCyclePresetById(
  presetId: string
): WorkflowPresetDefinition | undefined {
  return improvementCycleWorkflowPresets.find((preset) => preset.id === presetId);
}

export function buildWorkflowCreatePresetBody(presetId: string): string {
  const preset = getImprovementCyclePresetById(presetId);
  if (!preset) {
    throw new Error(`Unknown workflow preset: ${presetId}`);
  }
  return JSON.stringify(preset.workflowDefinition, null, 2);
}

export function buildWorkflowExecutePreset(presetId: string): WorkflowExecutePresetProjection {
  const preset = getImprovementCyclePresetById(presetId);
  if (!preset) {
    throw new Error(`Unknown workflow preset: ${presetId}`);
  }
  return preset.executePreset;
}
