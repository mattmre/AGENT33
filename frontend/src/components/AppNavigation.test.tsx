import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { AppNavigation } from "./AppNavigation";

describe("AppNavigation", () => {
  it("renders grouped workspace navigation with the active page marked", () => {
    render(<AppNavigation activeTab="guide" onNavigate={vi.fn()} />);

    expect(screen.getByRole("navigation", { name: "Workspace navigation" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Guide Me" })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("button", { name: "Operations Hub" })).not.toHaveAttribute("aria-current");
  });

  it("routes selected tabs through the shared navigation callback", async () => {
    const user = userEvent.setup();
    const onNavigate = vi.fn();

    render(<AppNavigation activeTab="guide" onNavigate={onNavigate} />);

    await user.click(screen.getByRole("button", { name: "Operations Hub" }));

    expect(onNavigate).toHaveBeenCalledWith("operations");
  });
});
