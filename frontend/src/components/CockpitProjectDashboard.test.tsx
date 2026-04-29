import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { CockpitProjectDashboard } from "./CockpitProjectDashboard";
import { getWorkspaceSession } from "../data/workspaces";

describe("CockpitProjectDashboard", () => {
  it("summarizes the active workspace, permission mode, and next action", () => {
    render(
      <CockpitProjectDashboard
        workspace={getWorkspaceSession("shipyard")}
        permissionModeId="pr-first"
        onReviewCurrentWork={vi.fn()}
        onOpenWorkflows={vi.fn()}
        onOpenSafety={vi.fn()}
      />
    );

    expect(screen.getByRole("region", { name: "Project cockpit dashboard" })).toBeInTheDocument();
    expect(screen.getByText("Multi-Agent Shipyard")).toBeInTheDocument();
    expect(screen.getAllByText("PR-first implementation")).toHaveLength(2);
    expect(screen.getByText("3 tasks need attention")).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "Artifact timeline" })).toBeInTheDocument();
    expect(screen.getByText("Review timeline")).toBeInTheDocument();
    expect(screen.getByText("Artifact package ready")).toBeInTheDocument();
    expect(screen.getAllByText("Workspace template adapter").length).toBeGreaterThan(1);
    expect(screen.getByRole("region", { name: "Safety and coordination signals" })).toBeInTheDocument();
    expect(screen.getByText("1 cockpit item needs review.")).toBeInTheDocument();
  });

  it("routes dashboard actions through the existing cockpit surfaces", async () => {
    const user = userEvent.setup();
    const onReviewCurrentWork = vi.fn();
    const onOpenWorkflows = vi.fn();
    const onOpenSafety = vi.fn();

    render(
      <CockpitProjectDashboard
        workspace={getWorkspaceSession("solo-builder")}
        permissionModeId="ask"
        onReviewCurrentWork={onReviewCurrentWork}
        onOpenWorkflows={onOpenWorkflows}
        onOpenSafety={onOpenSafety}
      />
    );

    await user.click(screen.getByRole("button", { name: "Review task board" }));
    await user.click(screen.getByRole("button", { name: "Choose workflow" }));
    await user.click(screen.getByRole("button", { name: "Review approvals" }));

    expect(onReviewCurrentWork).toHaveBeenCalledTimes(1);
    expect(onOpenWorkflows).toHaveBeenCalledTimes(1);
    expect(onOpenSafety).toHaveBeenCalledTimes(1);
  });
});
