import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { ComponentProps } from "react";
import { describe, expect, it, vi } from "vitest";

import { RoleIntakePanel } from "./RoleIntakePanel";

function renderPanel(overrides: Partial<ComponentProps<typeof RoleIntakePanel>> = {}) {
  return render(
    <RoleIntakePanel
      selectedRole={overrides.selectedRole ?? null}
      onSelectRole={overrides.onSelectRole ?? vi.fn()}
      onOpenDemo={overrides.onOpenDemo ?? vi.fn()}
      onOpenModels={overrides.onOpenModels ?? vi.fn()}
      onOpenWorkflowCatalog={overrides.onOpenWorkflowCatalog ?? vi.fn()}
      onOpenWorkflowStarter={overrides.onOpenWorkflowStarter ?? vi.fn()}
    />
  );
}

describe("RoleIntakePanel", () => {
  it("renders all role paths with beginner-readable labels", () => {
    renderPanel();

    expect(screen.getByRole("heading", { name: "Tell AGENT-33 who you are before choosing tools" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Founder/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Developer/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Agency/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Enterprise/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Operator/ })).toBeInTheDocument();
  });

  it("notifies the app when a user chooses a role", async () => {
    const user = userEvent.setup();
    const onSelectRole = vi.fn();
    renderPanel({ onSelectRole });

    await user.click(screen.getByRole("button", { name: /Developer/ }));

    expect(onSelectRole).toHaveBeenCalledWith("developer");
  });

  it("turns guided intake answers into a workflow starter draft", async () => {
    const user = userEvent.setup();
    const onOpenWorkflowStarter = vi.fn();
    const onSelectRole = vi.fn();
    renderPanel({ selectedRole: "founder", onSelectRole, onOpenWorkflowStarter });

    await user.type(screen.getByPlaceholderText("Example: Client portal MVP"), "Client portal MVP");
    await user.type(
      screen.getByPlaceholderText("Example: A portal where clients fill out intake forms and see project status."),
      "A client portal for intake forms and project status."
    );
    await user.type(
      screen.getByPlaceholderText("Example: business owner, client, project assistant"),
      "Business owner and client"
    );
    await user.type(
      screen.getByPlaceholderText("Example: product brief, screen list, first implementation tasks"),
      "Product brief and first build tasks"
    );
    await user.click(screen.getByRole("button", { name: "Create guided workflow draft" }));

    expect(onSelectRole).toHaveBeenCalledWith("founder");
    expect(onOpenWorkflowStarter).toHaveBeenCalledWith(
      expect.objectContaining({
        name: "client-portal-mvp",
        sourceLabel: "Guided intake: Client portal MVP"
      })
    );
  });
});
