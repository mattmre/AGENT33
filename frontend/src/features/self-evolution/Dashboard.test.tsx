import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { afterEach, describe, expect, it, vi } from "vitest"

vi.mock("../../lib/api", () => ({
  getRuntimeConfig: () => ({ API_BASE_URL: "http://localhost:8000" })
}))

import { EvolutionDashboard } from "./Dashboard"

describe("EvolutionDashboard", () => {
  afterEach(() => {
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
  })

  it("renders the dashboard heading", () => {
    render(<EvolutionDashboard token={null} />)

    expect(
      screen.getByText("Self-Evolution & Security Engine")
    ).toBeInTheDocument()
  })

  it("renders action buttons", () => {
    render(<EvolutionDashboard token="jwt" />)

    expect(
      screen.getByRole("button", { name: "Execute Simulated Hack / Audit" })
    ).toBeInTheDocument()
    expect(
      screen.getByRole("button", { name: "Refresh Pending PRs" })
    ).toBeInTheDocument()
  })

  it("shows empty PR state initially", () => {
    render(<EvolutionDashboard token="jwt" />)

    expect(screen.getByText("No pending evolutionary PRs.")).toBeInTheDocument()
  })

  it("loads and displays mock PRs when Refresh button is clicked", async () => {
    const user = userEvent.setup()

    render(<EvolutionDashboard token="jwt" />)

    await user.click(
      screen.getByRole("button", { name: "Refresh Pending PRs" })
    )

    expect(
      screen.getByText("Autonomous Improvement: Optimize security_audit_local")
    ).toBeInTheDocument()
    expect(
      screen.getByText(/auto-evolve\/evolve-security_audit_local/)
    ).toBeInTheDocument()
    expect(
      screen.queryByText("No pending evolutionary PRs.")
    ).not.toBeInTheDocument()
  })

  it("renders Merge & Reject buttons for each PR", async () => {
    const user = userEvent.setup()

    render(<EvolutionDashboard token="jwt" />)

    await user.click(
      screen.getByRole("button", { name: "Refresh Pending PRs" })
    )

    expect(
      screen.getByRole("button", { name: "Merge & Approve" })
    ).toBeInTheDocument()
    expect(
      screen.getByRole("button", { name: "Reject" })
    ).toBeInTheDocument()
  })

  it("triggers audit and shows alert", async () => {
    const user = userEvent.setup()
    const alertMock = vi.spyOn(window, "alert").mockImplementation(() => {})
    const fetchMock = vi.fn().mockResolvedValue({ ok: true })
    vi.stubGlobal("fetch", fetchMock)

    render(<EvolutionDashboard token="my-jwt" />)

    await user.click(
      screen.getByRole("button", { name: "Execute Simulated Hack / Audit" })
    )

    await waitFor(() => {
      expect(alertMock).toHaveBeenCalledWith(
        "Rigorous Security Audit initiated in the background."
      )
    })

    expect(fetchMock).toHaveBeenCalledWith(
      "http://localhost:8000/v1/outcomes/improvements",
      expect.objectContaining({
        method: "POST",
        headers: expect.objectContaining({
          Authorization: "Bearer my-jwt",
          "Content-Type": "application/json"
        })
      })
    )

    const body = JSON.parse(fetchMock.mock.calls[0][1].body as string)
    expect(body.metric_id).toBe("security_audit_local")
    expect(body.context).toContain("Self-Evolution dashboard")
  })

  it("does not trigger audit when token is null", async () => {
    const user = userEvent.setup()
    const fetchMock = vi.fn()
    vi.stubGlobal("fetch", fetchMock)

    render(<EvolutionDashboard token={null} />)

    await user.click(
      screen.getByRole("button", { name: "Execute Simulated Hack / Audit" })
    )

    expect(fetchMock).not.toHaveBeenCalled()
  })

  it("displays PR description and branch info", async () => {
    const user = userEvent.setup()

    render(<EvolutionDashboard token="jwt" />)

    await user.click(
      screen.getByRole("button", { name: "Refresh Pending PRs" })
    )

    expect(
      screen.getByText(/Automated PR generated from context/)
    ).toBeInTheDocument()
    expect(
      screen.getByText(
        /Branch: auto-evolve\/evolve-security_audit_local-20260219/
      )
    ).toBeInTheDocument()
  })
})
