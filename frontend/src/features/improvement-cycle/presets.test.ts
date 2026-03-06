import { describe, expect, it } from "vitest";

import {
  buildWorkflowCreatePresetBody,
  buildWorkflowExecutePreset,
  getImprovementCyclePresetById,
  improvementCyclePresetBinding,
  improvementCycleWorkflowPresets
} from "./presets";

describe("improvementCycleWorkflowPresets", () => {
  it("projects the canonical improvement-cycle workflow names and source paths", () => {
    expect(improvementCycleWorkflowPresets.map((preset) => preset.workflowName)).toEqual([
      "improvement-cycle-retrospective",
      "improvement-cycle-metrics-review"
    ]);

    expect(improvementCycleWorkflowPresets.map((preset) => preset.sourcePath)).toEqual([
      "core/workflows/improvement-cycle/retrospective.workflow.yaml",
      "core/workflows/improvement-cycle/metrics-review.workflow.yaml"
    ]);

    expect(new Set(improvementCycleWorkflowPresets.map((preset) => preset.id)).size).toBe(
      improvementCycleWorkflowPresets.length
    );
  });

  it("builds create preset payloads that preserve the canonical workflow steps", () => {
    const retrospective = JSON.parse(buildWorkflowCreatePresetBody("retrospective"));
    expect(retrospective.name).toBe("improvement-cycle-retrospective");
    expect(retrospective.steps.map((step: { id: string }) => step.id)).toEqual([
      "validate",
      "collect",
      "summarize"
    ]);
    expect(retrospective.steps.map((step: { action: string }) => step.action)).toEqual([
      "validate",
      "transform",
      "transform"
    ]);

    const metrics = JSON.parse(buildWorkflowCreatePresetBody("metrics-review"));
    expect(metrics.name).toBe("improvement-cycle-metrics-review");
    expect(metrics.inputs.review_period.required).toBe(true);
    expect(metrics.execution.mode).toBe("dependency-aware");
  });

  it("builds execute presets with canonical workflow names and deterministic sample inputs", () => {
    const retrospective = buildWorkflowExecutePreset("retrospective");
    expect(retrospective.pathParams).toEqual({ name: "improvement-cycle-retrospective" });
    expect(retrospective.body.inputs).toMatchObject({
      session_id: "session-57",
      scope: "frontend"
    });
    expect(retrospective.executionMode).toBe("single");

    const metrics = buildWorkflowExecutePreset("metrics-review");
    expect(metrics.pathParams).toEqual({ name: "improvement-cycle-metrics-review" });
    expect(metrics.body.inputs).toMatchObject({
      review_period: "2026-03-01 to 2026-03-07"
    });
    expect(metrics.body).not.toHaveProperty("repeat_count");
  });

  it("exposes a shared operation binding and lookup helper", () => {
    expect(improvementCyclePresetBinding.group).toBe("improvement-cycle");
    expect(improvementCyclePresetBinding.presetIds).toEqual([
      "retrospective",
      "metrics-review"
    ]);
    expect(getImprovementCyclePresetById("metrics-review")?.label).toContain("Metrics review");
  });
});
