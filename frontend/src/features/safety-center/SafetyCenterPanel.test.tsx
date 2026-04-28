import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

const { apiRequestMock } = vi.hoisted(() => ({
  apiRequestMock: vi.fn()
}));

vi.mock("../../lib/api", () => ({
  apiRequest: apiRequestMock
}));

import { SafetyCenterPanel } from "./SafetyCenterPanel";

const pendingApproval = {
  approval_id: "APR-123",
  status: "pending",
  reason: "supervised_destructive",
  tool_name: "filesystem",
  operation: "delete",
  command: "Remove-Item C:\\temp\\unsafe.txt",
  requested_by: "research-agent",
  tenant_id: "tenant-a",
  details: "Delete generated artifact",
  created_at: "2026-01-01T12:00:00Z",
  expires_at: "2026-01-01T13:00:00Z",
  reviewed_by: "",
  reviewed_at: null,
  review_note: ""
};

function renderPanel(overrides: Partial<React.ComponentProps<typeof SafetyCenterPanel>> = {}) {
  return render(
    <SafetyCenterPanel
      token="token"
      apiKey=""
      onOpenSetup={vi.fn()}
      onResult={vi.fn()}
      {...overrides}
    />
  );
}

describe("SafetyCenterPanel", () => {
  afterEach(() => {
    vi.clearAllMocks();
  });

  it("prompts for credentials before loading approval state", () => {
    const onOpenSetup = vi.fn();

    renderPanel({ token: "", apiKey: "", onOpenSetup });

    expect(screen.getByText("Connect to the engine first")).toBeInTheDocument();
    expect(apiRequestMock).not.toHaveBeenCalled();
  });

  it("renders pending approval details and submits an approval decision", async () => {
    apiRequestMock
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        data: [pendingApproval]
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        data: {
          ...pendingApproval,
          status: "approved",
          reviewed_by: "operator",
          reviewed_at: "2026-01-01T12:10:00Z",
          review_note: "Reviewed command scope"
        }
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        data: []
      });

    renderPanel();

    expect(await screen.findAllByText("filesystem: delete")).toHaveLength(3);
    expect(screen.getByRole("heading", { name: "Decide the riskiest items first" })).toBeInTheDocument();
    expect(screen.getByText("1 high-priority item should be reviewed one by one.")).toBeInTheDocument();
    expect(screen.getByText(/Policy preset: Deny by default/)).toBeInTheDocument();
    expect(screen.getByText("Destructive or high-impact action")).toBeInTheDocument();
    expect(screen.getByText("Remove-Item C:\\temp\\unsafe.txt")).toBeInTheDocument();

    await userEvent.type(screen.getByLabelText("Review note"), "Reviewed command scope");
    await userEvent.click(screen.getByRole("button", { name: "Approve action" }));

    await waitFor(() => {
      expect(apiRequestMock).toHaveBeenCalledWith({
        method: "POST",
        path: "/v1/approvals/tools/{approval_id}/decision",
        pathParams: { approval_id: "APR-123" },
        token: "token",
        apiKey: "",
        body: JSON.stringify({
          decision: "approve",
          review_note: "Reviewed command scope"
        })
      });
    });
  });
});
