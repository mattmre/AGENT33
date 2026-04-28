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
        onOpenRuns={vi.fn()}
        onOpenWorkflows={vi.fn()}
        onOpenSafety={vi.fn()}
      />
    );

    expect(screen.getByRole("region", { name: "Project cockpit dashboard" })).toBeInTheDocument();
    expect(screen.getByText("Multi-Agent Shipyard")).toBeInTheDocument();
    expect(screen.getByText("PR-first implementation")).toBeInTheDocument();
    expect(screen.getByText("3 tasks need attention")).toBeInTheDocument();
    expect(screen.getByText("No PR or package linked")).toBeInTheDocument();
  });

  it("routes dashboard actions through the existing cockpit surfaces", async () => {
    const user = userEvent.setup();
    const onOpenRuns = vi.fn();
    const onOpenWorkflows = vi.fn();
    const onOpenSafety = vi.fn();

    render(
      <CockpitProjectDashboard
        workspace={getWorkspaceSession("solo-builder")}
        permissionModeId="ask"
        onOpenRuns={onOpenRuns}
        onOpenWorkflows={onOpenWorkflows}
        onOpenSafety={onOpenSafety}
      />
    );

    await user.click(screen.getByRole("button", { name: "Open Sessions & Runs" }));
    await user.click(screen.getByRole("button", { name: "Choose workflow" }));
    await user.click(screen.getByRole("button", { name: "Review approvals" }));

    expect(onOpenRuns).toHaveBeenCalledTimes(1);
    expect(onOpenWorkflows).toHaveBeenCalledTimes(1);
    expect(onOpenSafety).toHaveBeenCalledTimes(1);
  });
});
