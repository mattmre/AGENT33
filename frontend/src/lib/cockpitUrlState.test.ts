import { describe, expect, it } from "vitest";

import {
  createCockpitUrl,
  isArtifactDrawerSectionId,
  readCockpitUrlState
} from "./cockpitUrlState";

describe("cockpit URL state", () => {
  it("reads valid cockpit deep-link params", () => {
    expect(
      readCockpitUrlState("?view=operations&workspace=shipyard&permission=pr-first&drawer=tests")
    ).toEqual({
      activeTab: "operations",
      workspaceId: "shipyard",
      permissionModeId: "pr-first",
      drawerSectionId: "tests"
    });
  });

  it("falls back safely for invalid deep-link params", () => {
    expect(
      readCockpitUrlState("?view=not-real&workspace=nope&permission=god-mode&drawer=terminal", {
        activeTab: "start",
        workspaceId: "test-review",
        permissionModeId: "workspace",
        drawerSectionId: "activity"
      })
    ).toEqual({
      activeTab: "start",
      workspaceId: "test-review",
      permissionModeId: "workspace",
      drawerSectionId: "activity"
    });
  });

  it("creates shareable cockpit URLs and only keeps drawer state for operations", () => {
    expect(
      createCockpitUrl("http://localhost:5173/?foo=bar#main", {
        activeTab: "operations",
        workspaceId: "research-build",
        permissionModeId: "ask",
        drawerSectionId: "commands"
      })
    ).toBe("/?foo=bar&view=operations&workspace=research-build&permission=ask&drawer=commands#main");

    expect(
      createCockpitUrl("http://localhost:5173/?drawer=logs", {
        activeTab: "guide",
        workspaceId: "solo-builder",
        permissionModeId: "observe",
        drawerSectionId: "logs"
      })
    ).toBe("/?view=guide&workspace=solo-builder&permission=observe");
  });

  it("validates artifact drawer section ids", () => {
    expect(isArtifactDrawerSectionId("outcome")).toBe(true);
    expect(isArtifactDrawerSectionId("terminal")).toBe(false);
    expect(isArtifactDrawerSectionId(null)).toBe(false);
  });
});
