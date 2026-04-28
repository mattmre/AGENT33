import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { getWorkspaceSession } from "../data/workspaces";
import { WorkspaceTaskBoard } from "./WorkspaceTaskBoard";

describe("WorkspaceTaskBoard", () => {
  it("renders task lanes and agent roster for the selected workspace", () => {
    render(
      <WorkspaceTaskBoard
        workspace={getWorkspaceSession("shipyard")}
        onOpenSafety={vi.fn()}
        onOpenWorkflows={vi.fn()}
      />
    );

    expect(screen.getByRole("region", { name: "Multi-Agent Shipyard task board" })).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "Running tasks" })).toBeInTheDocument();
    expect(screen.getByText("Build the next slice")).toBeInTheDocument();
    expect(screen.getByRole("complementary", { name: "Workspace agent roster" })).toBeInTheDocument();
    expect(screen.getByText("Sequences work and prevents PR drift.")).toBeInTheDocument();
  });

  it("routes board actions through callbacks", async () => {
    const user = userEvent.setup();
    const onOpenSafety = vi.fn();
    const onOpenWorkflows = vi.fn();

    render(
      <WorkspaceTaskBoard
        workspace={getWorkspaceSession("solo-builder")}
        onOpenSafety={onOpenSafety}
        onOpenWorkflows={onOpenWorkflows}
      />
    );

    await user.click(screen.getByRole("button", { name: "Choose workflow" }));
    await user.click(screen.getByRole("button", { name: "Review approvals" }));

    expect(onOpenWorkflows).toHaveBeenCalledTimes(1);
    expect(onOpenSafety).toHaveBeenCalledTimes(1);
  });
});
