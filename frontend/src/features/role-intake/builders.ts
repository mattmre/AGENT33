import type { WorkflowStarterDraft } from "../workflow-starter/types";
import { getRoleProfile } from "./data";
import type { ProductBrief } from "./types";

function slugifyTitle(title: string): string {
  return title
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "")
    .slice(0, 64);
}

export function buildWorkflowDraftFromBrief(brief: ProductBrief): WorkflowStarterDraft {
  const roleProfile = getRoleProfile(brief.roleId);
  const name = slugifyTitle(brief.title) || `guided-brief-${brief.id}`;

  return {
    id: `guided-${brief.id}`,
    name,
    goal: [
      `Role path: ${roleProfile?.title ?? brief.roleId}`,
      `Idea: ${brief.idea}`,
      `Primary users: ${brief.audience}`,
      `Starting point: ${brief.startingPoint}`,
      `Desired output: ${brief.desiredOutput}`,
      `Safety and scope: ${brief.safetyScope}`
    ].join("\n"),
    kind: roleProfile?.starterKind ?? "automation-loop",
    output:
      "Plain-language product brief, required inputs, scoped workflow plan, safety gates, first deliverables, and validation checklist.",
    schedule: "",
    author: "role-intake",
    sourceLabel: `Guided intake: ${brief.title}`
  };
}
