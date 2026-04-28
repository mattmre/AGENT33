import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { PermissionModeControl } from "./PermissionModeControl";

describe("PermissionModeControl", () => {
  it("renders the current permission mode with review guidance", () => {
    render(
      <PermissionModeControl
        selectedModeId="ask"
        operatorMode="beginner"
        onSelectMode={vi.fn()}
        onOperatorModeChange={vi.fn()}
      />
    );

    expect(screen.getByRole("region", { name: "Permission mode" })).toBeInTheDocument();
    expect(screen.getByRole("combobox", { name: "Permission mode" })).toHaveValue("ask");
    expect(screen.getByText("Confirm before tools or changes run.")).toBeInTheDocument();
    expect(screen.getByText("User approval before commands, writes, or external changes")).toBeInTheDocument();
    expect(screen.getByText("Beginner guardrails")).toBeInTheDocument();
  });

  it("routes mode changes and control-plane compatibility changes through callbacks", async () => {
    const user = userEvent.setup();
    const onSelectMode = vi.fn();
    const onOperatorModeChange = vi.fn();

    render(
      <PermissionModeControl
        selectedModeId="ask"
        operatorMode="beginner"
        onSelectMode={onSelectMode}
        onOperatorModeChange={onOperatorModeChange}
      />
    );

    await user.selectOptions(screen.getByRole("combobox", { name: "Permission mode" }), "pr-first");
    await user.click(screen.getByRole("button", { name: "Unlock Pro controls" }));

    expect(onSelectMode).toHaveBeenCalledWith("pr-first");
    expect(onOperatorModeChange).toHaveBeenCalledWith("pro");
  });

  it("lets operators return to beginner guardrails from Pro controls", async () => {
    const user = userEvent.setup();
    const onOperatorModeChange = vi.fn();

    render(
      <PermissionModeControl
        selectedModeId="workspace"
        operatorMode="pro"
        onSelectMode={vi.fn()}
        onOperatorModeChange={onOperatorModeChange}
      />
    );

    await user.click(screen.getByRole("button", { name: "Return to Beginner guardrails" }));

    expect(screen.getByText("Pro controls unlocked")).toBeInTheDocument();
    expect(onOperatorModeChange).toHaveBeenCalledWith("beginner");
  });
});
