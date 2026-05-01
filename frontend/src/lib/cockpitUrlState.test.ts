import { describe, expect, it } from "vitest";

import {
  createCockpitUrl,
  isArtifactDrawerSectionId,
  readCockpitUrlState
} from "./cockpitUrlState";

describe("cockpit URL state", () => {
  it("reads valid cockpit deep-link params", () => {
    expect(
      readCockpitUrlState("?view=operations&workspace=shipyard&permission=pr-first&drawer=tests&operatorMode=beginner")
    ).toEqual({
      activeTab: "operations",
      workspaceId: "shipyard",
      permissionModeId: "pr-first",
      drawerSectionId: "tests",
      operatorMode: "beginner"
    });
  });

  it("falls back safely for invalid deep-link params", () => {
    expect(
      readCockpitUrlState("?view=not-real&workspace=nope&permission=god-mode&drawer=terminal", {
        activeTab: "start",
        workspaceId: "test-review",
        permissionModeId: "workspace",
        drawerSectionId: "activity",
        operatorMode: "pro"
      })
    ).toEqual({
      activeTab: "start",
      workspaceId: "test-review",
      permissionModeId: "workspace",
      drawerSectionId: "activity",
      operatorMode: "pro"
    });
  });

  it("creates shareable cockpit URLs and only keeps drawer state for operations", () => {
    expect(
      createCockpitUrl("http://localhost:5173/?foo=bar#main", {
        activeTab: "operations",
        workspaceId: "research-build",
        permissionModeId: "ask",
        drawerSectionId: "commands",
        operatorMode: "beginner"
      })
    ).toBe("/?foo=bar&view=operations&workspace=research-build&permission=ask&operatorMode=beginner&drawer=commands#main");

    expect(
      createCockpitUrl("http://localhost:5173/?drawer=logs", {
        activeTab: "guide",
        workspaceId: "solo-builder",
        permissionModeId: "observe",
        drawerSectionId: "logs",
        operatorMode: "pro"
      })
    ).toBe("/?view=guide&workspace=solo-builder&permission=observe&operatorMode=pro");
  });

  it("validates artifact drawer section ids", () => {
    expect(isArtifactDrawerSectionId("outcome")).toBe(true);
    expect(isArtifactDrawerSectionId("terminal")).toBe(false);
    expect(isArtifactDrawerSectionId(null)).toBe(false);
  });
});
