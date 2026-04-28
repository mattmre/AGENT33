import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { UnifiedConnectCenterPanel } from "./UnifiedConnectCenterPanel";

describe("UnifiedConnectCenterPanel", () => {
  it("renders a unified setup checklist without credentials", () => {
    render(
      <UnifiedConnectCenterPanel token="" apiKey="" onNavigate={vi.fn()} onResult={vi.fn()} />
    );

    expect(screen.getByRole("heading", { name: "Connect the pieces AGENT-33 needs to work" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Can AGENT-33 call a model?" })).toBeInTheDocument();
    expect(screen.getByText("Add access to scan live status")).toBeInTheDocument();
  });

  it("routes setup actions through the app navigation callback", async () => {
    const user = userEvent.setup();
    const onNavigate = vi.fn();
    render(
      <UnifiedConnectCenterPanel token="" apiKey="" onNavigate={onNavigate} onResult={vi.fn()} />
    );

    await user.click(screen.getByRole("button", { name: "Open model setup" }));

    expect(onNavigate).toHaveBeenCalledWith("models");
  });
});
