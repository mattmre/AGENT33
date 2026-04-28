import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { WorkspaceSessionSelector } from "./WorkspaceSessionSelector";

describe("WorkspaceSessionSelector", () => {
  it("renders the active workspace with beginner-readable context", () => {
    render(
      <WorkspaceSessionSelector
        selectedWorkspaceId="solo-builder"
        onSelectWorkspace={vi.fn()}
        onOpenRuns={vi.fn()}
        onOpenWorkflows={vi.fn()}
      />
    );

    expect(screen.getByRole("region", { name: "Workspace session" })).toBeInTheDocument();
    expect(screen.getByText("Local Shipyard")).toBeInTheDocument();
    expect(screen.getByText("Turn a plain-language idea into a guided build plan.")).toBeInTheDocument();
    expect(screen.getByRole("combobox", { name: "Active project template" })).toHaveValue("solo-builder");
  });

  it("routes workspace changes and quick actions through callbacks", async () => {
    const user = userEvent.setup();
    const onSelectWorkspace = vi.fn();
    const onOpenRuns = vi.fn();
    const onOpenWorkflows = vi.fn();

    render(
      <WorkspaceSessionSelector
        selectedWorkspaceId="solo-builder"
        onSelectWorkspace={onSelectWorkspace}
        onOpenRuns={onOpenRuns}
        onOpenWorkflows={onOpenWorkflows}
      />
    );

    await user.selectOptions(screen.getByRole("combobox", { name: "Active project template" }), "shipyard");
    await user.click(screen.getByRole("button", { name: "Open workflows" }));
    await user.click(screen.getByRole("button", { name: "View runs" }));

    expect(onSelectWorkspace).toHaveBeenCalledWith("shipyard");
    expect(onOpenWorkflows).toHaveBeenCalledTimes(1);
    expect(onOpenRuns).toHaveBeenCalledTimes(1);
  });
});
