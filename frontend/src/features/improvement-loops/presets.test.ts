import { describe, expect, it } from "vitest";

import {
  buildLoopWorkflow,
  buildScheduleInputs,
  formFromPreset,
  getPreset,
  normalizeCron
} from "./presets";

describe("improvement loop presets", () => {
  it("builds a governed competitive research workflow", () => {
    const preset = getPreset("competitive-research");
    const workflow = buildLoopWorkflow(preset, formFromPreset(preset));

    expect(workflow.name).toBe("weekly-competitive-agent-scan");
    expect(workflow.execution.mode).toBe("dependency-aware");
    expect(workflow.metadata.tags).toContain("improvement-cycle");
    expect(workflow.steps.map((step) => step.id)).toEqual(["scope", "research", "compare", "propose", "review"]);
    expect(workflow.steps.at(-1)?.action).toBe("validate");
  });

  it("normalizes operator-friendly cron input", () => {
    expect(normalizeCron("cron: 0 9 * * 1")).toBe("0 9 * * 1");
    expect(normalizeCron(" 0 10 * * 2 ")).toBe("0 10 * * 2");
  });

  it("passes loop inputs into scheduled runs", () => {
    const preset = getPreset("operator-ux-review");
    const inputs = buildScheduleInputs(preset, formFromPreset(preset));

    expect(inputs.goal).toContain("operator path");
    expect(inputs.focus_areas).toEqual(preset.focusAreas);
    expect(inputs.cadence).toBe(preset.cadenceLabel);
  });
});
