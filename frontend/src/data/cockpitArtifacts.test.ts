import { describe, expect, it } from "vitest";

import { ARTIFACT_DRAWER_SECTION_IDS } from "./artifactDrawerSections";
import {
  COCKPIT_ARTIFACT_KINDS,
  getCockpitArtifactsByKind,
  getCockpitArtifactsForWorkspace
} from "./cockpitArtifacts";
import { WORKSPACE_SESSIONS } from "./workspaces";

describe("cockpit artifact view models", () => {
  it("creates one artifact for every drawer-backed artifact kind", () => {
    for (const workspace of WORKSPACE_SESSIONS) {
      const artifacts = getCockpitArtifactsForWorkspace(workspace.id);

      expect(artifacts.map((artifact) => artifact.kind)).toEqual(COCKPIT_ARTIFACT_KINDS);
      expect(new Set(artifacts.map((artifact) => artifact.id)).size).toBe(artifacts.length);
      expect(artifacts.every((artifact) => artifact.workspaceId === workspace.id)).toBe(true);
      expect(artifacts.every((artifact) => ARTIFACT_DRAWER_SECTION_IDS.includes(artifact.sectionId))).toBe(true);
    }
  });

  it("keeps required review metadata on every artifact", () => {
    const artifacts = getCockpitArtifactsForWorkspace("shipyard");

    for (const artifact of artifacts) {
      expect(artifact.id).toMatch(/^shipyard-/);
      expect(artifact.title.length).toBeGreaterThan(0);
      expect(artifact.summary.length).toBeGreaterThan(0);
      expect(artifact.sourceLabel.length).toBeGreaterThan(0);
      expect(artifact.timestampLabel.length).toBeGreaterThan(0);
      expect(artifact.nextActionLabel.length).toBeGreaterThan(0);
    }
  });

  it("uses explicit empty artifacts instead of fake success states", () => {
    const artifactsByKind = getCockpitArtifactsByKind("solo-builder");

    expect(artifactsByKind.risk).toMatchObject({
      evidenceState: "empty",
      status: "not-available",
      reviewState: "not-required",
      title: "No active blocker is attached"
    });
    expect(artifactsByKind.outcome).toMatchObject({
      evidenceState: "empty",
      status: "not-available",
      reviewState: "not-started",
      title: "No PR or artifact package linked"
    });
  });

  it("maps blocked work into risk, approval, and outcome artifacts", () => {
    const artifactsByKind = getCockpitArtifactsByKind("test-review");

    expect(artifactsByKind.risk).toMatchObject({
      status: "blocked",
      reviewState: "blocked",
      relatedTaskIds: ["quality-merge"]
    });
    expect(artifactsByKind.approval).toMatchObject({
      status: "blocked",
      reviewState: "blocked",
      nextActionLabel: "Review the requested approval"
    });
    expect(artifactsByKind.outcome).toMatchObject({
      title: "Blocked with required action",
      status: "blocked",
      relatedTaskIds: ["quality-merge"]
    });
  });

  it("maps active work into command, log, activity, and validation artifacts", () => {
    const artifactsByKind = getCockpitArtifactsByKind("shipyard");

    expect(artifactsByKind.command).toMatchObject({
      status: "running",
      reviewState: "in-progress",
      relatedTaskIds: ["shipyard-scout"]
    });
    expect(artifactsByKind.log.relatedTaskIds).toEqual(["shipyard-scout", "shipyard-build"]);
    expect(artifactsByKind.activity.status).toBe("running");
    expect(artifactsByKind.test).toMatchObject({
      status: "needs-review",
      reviewState: "needs-review",
      ownerRole: "Reviewer"
    });
  });

  it("throws an actionable error for an unknown workspace id", () => {
    expect(() => getCockpitArtifactsForWorkspace("missing-workspace")).toThrow(
      /Cannot build cockpit artifacts for unknown workspaceId "missing-workspace"/
    );
  });
});
