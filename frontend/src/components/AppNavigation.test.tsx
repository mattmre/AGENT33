import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { AppNavigation } from "./AppNavigation";

describe("AppNavigation", () => {
  it("renders grouped workspace navigation with the active page marked", () => {
    render(<AppNavigation activeTab="cockpit" onNavigate={vi.fn()} />);

    expect(screen.getByRole("navigation", { name: "Main navigation" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /Operations Cockpit/ })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("button", { name: /Sessions & Runs/ })).not.toHaveAttribute("aria-current");
    expect(screen.getByText("System surfaces")).toBeInTheDocument();
  });

  it("routes selected tabs through the shared navigation callback", async () => {
    const user = userEvent.setup();
    const onNavigate = vi.fn();

    render(<AppNavigation activeTab="cockpit" onNavigate={onNavigate} />);

    await user.click(screen.getByRole("button", { name: /Sessions & Runs/ }));

    expect(onNavigate).toHaveBeenCalledWith("operations");
  });

  it("keeps specialized tools reachable behind the tools section", async () => {
    const user = userEvent.setup();
    const onNavigate = vi.fn();

    render(<AppNavigation activeTab="fabric" onNavigate={onNavigate} />);

    expect(screen.getByText("System surfaces").closest("details")).toHaveAttribute("open");
    expect(screen.getByRole("button", { name: "Tool Fabric" })).toHaveAttribute("aria-current", "page");

    await user.click(screen.getByRole("button", { name: "MCP Health" }));

    expect(onNavigate).toHaveBeenCalledWith("mcp");
  });

  it("routes the design kit surfaces page through the shared navigation callback", async () => {
    const user = userEvent.setup();
    const onNavigate = vi.fn();

    render(<AppNavigation activeTab="fabric" onNavigate={onNavigate} />);

    await user.click(screen.getByRole("button", { name: "Design Kit Surfaces" }));

    expect(onNavigate).toHaveBeenCalledWith("design-kit");
  });

  it("keeps the tools disclosure name concise while showing detail only in expanded content", () => {
    render(<AppNavigation activeTab="cockpit" onNavigate={vi.fn()} />);

    expect(screen.getByText("System surfaces").closest("summary")).not.toHaveAttribute("aria-describedby");
    expect(screen.getByText("Build, inspect, and governance panels that support the main cockpit flow.")).toBeInTheDocument();
  });
});
