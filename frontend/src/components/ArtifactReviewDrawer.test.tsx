import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { ArtifactReviewDrawer } from "./ArtifactReviewDrawer";
import { getWorkspaceSession } from "../data/workspaces";

describe("ArtifactReviewDrawer", () => {
  it("renders a review drawer scaffold for the active workspace", () => {
    render(<ArtifactReviewDrawer workspace={getWorkspaceSession("solo-builder")} permissionModeId="ask" />);

    expect(screen.getByRole("complementary", { name: "Artifact and review drawer" })).toBeInTheDocument();
    expect(screen.getByRole("tablist", { name: "Artifact drawer sections" })).toBeInTheDocument();
    expect(screen.getByRole("tabpanel")).toHaveAttribute("aria-labelledby", "artifact-drawer-tab-plan");
    expect(screen.getByText("Solo Builder")).toBeInTheDocument();
    expect(screen.getByText("Ask before action: Plans, setup guidance, and queued actions")).toBeInTheDocument();
    expect(screen.getByText("Plan artifact")).toBeInTheDocument();
    expect(screen.getAllByText("Capture the build request")).toHaveLength(2);
    expect(screen.getByText("Review scope and assumptions")).toBeInTheDocument();
  });

  it("switches between artifact sections without leaving the cockpit", async () => {
    const user = userEvent.setup();
    render(<ArtifactReviewDrawer workspace={getWorkspaceSession("test-review")} permissionModeId="workspace" />);

    await user.click(screen.getByRole("tab", { name: "Command Blocks" }));
    expect(screen.getByText("Command blocks")).toBeInTheDocument();
    expect(screen.getByRole("tab", { name: "Command Blocks" })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByRole("tab", { name: "Command Blocks" })).toHaveAttribute("tabindex", "0");
    expect(screen.getByText(/source agent, status, duration, and redaction state/i)).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "Command block evidence" })).toBeInTheDocument();
    expect(screen.getByText("Builder lane: Run checks")).toBeInTheDocument();

    await user.keyboard("{End}");
    expect(screen.getByRole("tab", { name: "Outcome" })).toHaveAttribute("aria-selected", "true");
    expect(screen.getByText("Done state")).toBeInTheDocument();
    expect(screen.getByText("Blocked with required action")).toBeInTheDocument();

    await user.click(screen.getByRole("tab", { name: "Activity / Mailbox" }));
    expect(screen.getByText("Agent mailbox")).toBeInTheDocument();
    expect(screen.getByText("Quality Gate")).toBeInTheDocument();
    expect(screen.getByRole("region", { name: "Activity evidence" })).toBeInTheDocument();
    expect(screen.getByText("Run checks")).toBeInTheDocument();
  });
});
