import { describe, expect, it } from "vitest";

import { WORKSPACE_SESSION_IDS, type WorkspaceSessionId } from "./workspaces";
import { getWorkspaceBoard } from "./workspaceBoard";
import {
  buildWorkspaceTemplateStarterDraft,
  getPrimaryWorkspaceTemplateStarter,
  getWorkspaceTemplateStarters,
  validateWorkspaceTemplateStarters
} from "./workspaceTemplateStarters";

describe("workspace template starters", () => {
  it("provides reachable starter configurations for every workspace template", () => {
    expect(validateWorkspaceTemplateStarters()).toEqual([]);

    for (const workspaceId of WORKSPACE_SESSION_IDS) {
      const starters = getWorkspaceTemplateStarters(workspaceId);
      const board = getWorkspaceBoard(workspaceId);

      expect(starters.length).toBeGreaterThan(0);
      for (const starter of starters) {
        const beginsWithTask = board.tasks.find((task) => task.id === starter.beginsWithTaskId);

        expect(starter.workspaceId).toBe(workspaceId);
        expect(beginsWithTask?.ownerRole).toBe(starter.assignedRole);
        expect(starter.description.length).toBeGreaterThan(0);
        expect(starter.nextActionLabel.length).toBeGreaterThan(0);
      }
    }
  });

  it("builds workflow starter drafts from template starters", () => {
    const starter = getPrimaryWorkspaceTemplateStarter("shipyard" satisfies WorkspaceSessionId);

    expect(starter).toBeDefined();
    expect(buildWorkspaceTemplateStarterDraft(starter!)).toMatchObject({
      id: "shipyard-slice-orchestration",
      name: "Multi-agent slice orchestration",
      kind: "automation-loop",
      author: "coordinator",
      sourceLabel: "Workspace template: Multi-agent slice orchestration"
    });
  });
});
