import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import type { DomainConfig } from "../../types";
import { AdvancedControlPlanePanel, type OperatorMode } from "./AdvancedControlPlanePanel";

vi.mock("../../components/HealthPanel", () => ({
  HealthPanel: () => <div data-testid="health-panel">Health</div>
}));

vi.mock("../../components/ObservationStream", () => ({
  ObservationStream: () => <div data-testid="observation-stream">Observations</div>
}));

vi.mock("../../components/DomainPanel", () => ({
  DomainPanel: ({
    domain,
    externalFilter
  }: {
    domain: DomainConfig;
    externalFilter?: string;
  }) => (
    <div data-testid="domain-panel">
      {domain.title}:{externalFilter}
    </div>
  )
}));

const domains: DomainConfig[] = [
  {
    id: "auth",
    title: "Authentication",
    description: "Token and API key control",
    operations: [
      {
        id: "auth-token",
        title: "Create Token",
        method: "POST",
        path: "/v1/auth/token",
        description: "Create a token"
      }
    ]
  },
  {
    id: "memory",
    title: "Memory",
    description: "Memory store operations",
    operations: [
      {
        id: "memory-delete",
        title: "Delete Memory",
        method: "DELETE",
        path: "/v1/memory/{id}",
        description: "Delete a memory item"
      }
    ]
  }
];

function renderPanel(overrides: Partial<{ operatorMode: OperatorMode; selectedDomainId: string }> = {}) {
  return render(
    <AdvancedControlPlanePanel
      domains={domains}
      selectedDomainId={overrides.selectedDomainId ?? "auth"}
      token="jwt"
      apiKey=""
      activity={[]}
      operatorMode={overrides.operatorMode ?? "beginner"}
      onOperatorModeChange={vi.fn()}
      onSelectedDomainChange={vi.fn()}
      onOpenModels={vi.fn()}
      onOpenWorkflowCatalog={vi.fn()}
      onOpenOperations={vi.fn()}
      onOpenSafety={vi.fn()}
      onOpenSetup={vi.fn()}
      onResult={vi.fn()}
    />
  );
}

describe("AdvancedControlPlanePanel", () => {
  it("quarantines raw controls in beginner mode and exposes safer routes", async () => {
    const user = userEvent.setup();
    const onOperatorModeChange = vi.fn();
    const onOpenModels = vi.fn();

    render(
      <AdvancedControlPlanePanel
        domains={domains}
        selectedDomainId="auth"
        token="jwt"
        apiKey=""
        activity={[]}
        operatorMode="beginner"
        onOperatorModeChange={onOperatorModeChange}
        onSelectedDomainChange={vi.fn()}
        onOpenModels={onOpenModels}
        onOpenWorkflowCatalog={vi.fn()}
        onOpenOperations={vi.fn()}
        onOpenSafety={vi.fn()}
        onOpenSetup={vi.fn()}
        onResult={vi.fn()}
      />
    );

    expect(screen.getByText("Advanced controls are quarantined by default.")).toBeInTheDocument();
    expect(screen.queryByText("Raw control plane")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Open Models" }));
    expect(onOpenModels).toHaveBeenCalled();

    await user.click(screen.getByRole("button", { name: "Unlock Pro control plane" }));
    expect(onOperatorModeChange).toHaveBeenCalledWith("pro");
  });

  it("filters domain previews and unlocks pro mode for the selected domain", async () => {
    const user = userEvent.setup();
    const onOperatorModeChange = vi.fn();
    const onSelectedDomainChange = vi.fn();

    render(
      <AdvancedControlPlanePanel
        domains={domains}
        selectedDomainId="auth"
        token="jwt"
        apiKey=""
        activity={[]}
        operatorMode="beginner"
        onOperatorModeChange={onOperatorModeChange}
        onSelectedDomainChange={onSelectedDomainChange}
        onOpenModels={vi.fn()}
        onOpenWorkflowCatalog={vi.fn()}
        onOpenOperations={vi.fn()}
        onOpenSafety={vi.fn()}
        onOpenSetup={vi.fn()}
        onResult={vi.fn()}
      />
    );

    await user.type(screen.getByPlaceholderText(/Search endpoints/), "memory");

    expect(screen.getByText("Memory")).toBeInTheDocument();
    expect(screen.queryByText("Authentication")).not.toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Inspect in Pro mode" }));
    expect(onSelectedDomainChange).toHaveBeenCalledWith("memory");
    expect(onOperatorModeChange).toHaveBeenCalledWith("pro");
  });

  it("renders pro mode with global search, activity, and beginner return", async () => {
    const user = userEvent.setup();
    const onOperatorModeChange = vi.fn();

    render(
      <AdvancedControlPlanePanel
        domains={domains}
        selectedDomainId="auth"
        token="jwt"
        apiKey=""
        activity={[
          {
            id: "call-1",
            at: "10:00",
            label: "Create Token",
            status: 200,
            durationMs: 12,
            url: "/v1/auth/token"
          }
        ]}
        operatorMode="pro"
        onOperatorModeChange={onOperatorModeChange}
        onSelectedDomainChange={vi.fn()}
        onOpenModels={vi.fn()}
        onOpenWorkflowCatalog={vi.fn()}
        onOpenOperations={vi.fn()}
        onOpenSafety={vi.fn()}
        onOpenSetup={vi.fn()}
        onResult={vi.fn()}
      />
    );

    expect(screen.getByText("Raw control plane")).toBeInTheDocument();
    expect(screen.getByTestId("health-panel")).toBeInTheDocument();
    expect(screen.getByTestId("domain-panel")).toHaveTextContent("Authentication:");
    expect(screen.getByText("Create Token")).toBeInTheDocument();

    await user.type(screen.getByPlaceholderText("Filter domains and operation cards"), "token");
    expect(screen.getByTestId("domain-panel")).toHaveTextContent("Authentication:token");

    await user.click(screen.getByRole("button", { name: "Return to Beginner mode" }));
    expect(onOperatorModeChange).toHaveBeenCalledWith("beginner");
  });

  it("shows an empty state when no technical domains are registered", () => {
    renderPanel({ operatorMode: "beginner", selectedDomainId: "missing" }).unmount();
    render(
      <AdvancedControlPlanePanel
        domains={[]}
        selectedDomainId="missing"
        token="jwt"
        apiKey=""
        activity={[]}
        operatorMode="beginner"
        onOperatorModeChange={vi.fn()}
        onSelectedDomainChange={vi.fn()}
        onOpenModels={vi.fn()}
        onOpenWorkflowCatalog={vi.fn()}
        onOpenOperations={vi.fn()}
        onOpenSafety={vi.fn()}
        onOpenSetup={vi.fn()}
        onResult={vi.fn()}
      />
    );

    expect(screen.getByText("No technical domains are registered.")).toBeInTheDocument();
  });
});
