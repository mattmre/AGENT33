import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ShipyardLaneScaffold } from "./ShipyardLaneScaffold";
import { getWorkspaceSession } from "../data/workspaces";

describe("ShipyardLaneScaffold", () => {
  it("renders BridgeSpace-style role lanes for the selected workspace", () => {
    render(
      <ShipyardLaneScaffold
        workspace={getWorkspaceSession("shipyard")}
        onOpenWorkflows={vi.fn()}
        onOpenSafety={vi.fn()}
      />
    );

    expect(screen.getByRole("region", { name: "Shipyard lanes" })).toBeInTheDocument();
    expect(screen.getByText("Shipyard command lanes")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Coordinator" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Scout" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Builder" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Reviewer" })).toBeInTheDocument();
    expect(screen.getByText("Scout implementation risks")).toBeInTheDocument();
    expect(screen.getByText("Expected output: Implementation slice, validation commands, and changed artifacts.")).toBeInTheDocument();
  });

  it("keeps empty role lanes beginner-readable", () => {
    render(
      <ShipyardLaneScaffold
        workspace={getWorkspaceSession("solo-builder")}
        onOpenWorkflows={vi.fn()}
        onOpenSafety={vi.fn()}
      />
    );

    expect(screen.getByText("Scout lane")).toBeInTheDocument();
    expect(screen.getAllByText("No tasks assigned to this role yet.").length).toBeGreaterThan(0);
  });

  it("routes lane actions through existing cockpit surfaces", async () => {
    const user = userEvent.setup();
    const onOpenWorkflows = vi.fn();
    const onOpenSafety = vi.fn();

    render(
      <ShipyardLaneScaffold
        workspace={getWorkspaceSession("test-review")}
        onOpenWorkflows={onOpenWorkflows}
        onOpenSafety={onOpenSafety}
      />
    );

    await user.click(screen.getByRole("button", { name: "Launch workflow" }));
    await user.click(screen.getByRole("button", { name: "Check approvals" }));

    expect(onOpenWorkflows).toHaveBeenCalledTimes(1);
    expect(onOpenSafety).toHaveBeenCalledTimes(1);
  });
});
