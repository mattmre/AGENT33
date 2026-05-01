import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { DesignKitSurfacesPanel } from "./DesignKitSurfacesPanel";

function getCard(title: string): HTMLElement {
  const heading = screen.getByRole("heading", { name: title });
  const card = heading.closest("article");
  expect(card).not.toBeNull();
  return card as HTMLElement;
}

describe("DesignKitSurfacesPanel", () => {
  it("offers quick runtime jumps and live surface routing", async () => {
    const user = userEvent.setup();
    const onNavigate = vi.fn();

    render(<DesignKitSurfacesPanel onNavigate={onNavigate} />);

    expect(screen.getByRole("heading", { name: "Design Kit Surfaces" })).toBeInTheDocument();
    expect(screen.getAllByRole("button", { name: "Open Sessions & Runs" }).length).toBeGreaterThan(0);

    const healthCard = getCard("HealthPanel / HealthPanelFull");
    await user.click(within(healthCard).getByRole("button", { name: "Open Control Plane" }));

    expect(onNavigate).toHaveBeenCalledWith("advanced");
  });

  it("marks legacy references as unwired", () => {
    render(<DesignKitSurfacesPanel onNavigate={vi.fn()} />);

    const legacyCard = getCard("OperationsHub / ControlPanel / ProcessList");
    expect(within(legacyCard).getByText("No live route wired.")).toBeInTheDocument();
  });
});
