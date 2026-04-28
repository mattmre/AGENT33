import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { AppNavigation } from "./AppNavigation";

describe("AppNavigation", () => {
  it("renders grouped workspace navigation with the active page marked", () => {
    render(<AppNavigation activeTab="guide" onNavigate={vi.fn()} />);

    expect(screen.getByRole("navigation", { name: "Main navigation" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Guide \/ Intake/ })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("button", { name: /Sessions & Runs/ })).not.toHaveAttribute("aria-current");
    expect(screen.getByText("Tools & advanced surfaces")).toBeInTheDocument();
  });

  it("routes selected tabs through the shared navigation callback", async () => {
    const user = userEvent.setup();
    const onNavigate = vi.fn();

    render(<AppNavigation activeTab="guide" onNavigate={onNavigate} />);

    await user.click(screen.getByRole("button", { name: /Sessions & Runs/ }));

    expect(onNavigate).toHaveBeenCalledWith("operations");
  });

  it("keeps specialized tools reachable behind the tools section", async () => {
    const user = userEvent.setup();
    const onNavigate = vi.fn();

    render(<AppNavigation activeTab="fabric" onNavigate={onNavigate} />);

    expect(screen.getByText("Tools & advanced surfaces").closest("details")).toHaveAttribute("open");
    expect(screen.getByRole("button", { name: "Tool Fabric" })).toHaveAttribute("aria-current", "page");

    await user.click(screen.getByRole("button", { name: "MCP Health" }));

    expect(onNavigate).toHaveBeenCalledWith("mcp");
  });
});
