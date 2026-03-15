import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { afterEach, describe, expect, it, vi } from "vitest"

vi.mock("../../lib/api", () => ({
  getRuntimeConfig: () => ({ API_BASE_URL: "http://localhost:8000" })
}))

import { SessionsDashboard } from "./Dashboard"

describe("SessionsDashboard", () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it("renders the dashboard heading and description", () => {
    render(<SessionsDashboard token={null} />)

    expect(screen.getByText("Session Logs & Alignment Status")).toBeInTheDocument()
    expect(
      screen.getByText("Historic execution contexts and system checkpoints.")
    ).toBeInTheDocument()
  })

  it("shows empty state message when no sessions are loaded", () => {
    render(<SessionsDashboard token={null} />)

    expect(
      screen.getByText("No historic sessions found or API not wired.")
    ).toBeInTheDocument()
  })

  it("does not fetch sessions when token is null", () => {
    const fetchMock = vi.fn()
    vi.stubGlobal("fetch", fetchMock)

    render(<SessionsDashboard token={null} />)

    expect(fetchMock).not.toHaveBeenCalled()
  })

  it("fetches and displays sessions when token is provided", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve([
          { id: "session-001" },
          { id: "session-002" },
          { id: "session-003" }
        ])
    })
    vi.stubGlobal("fetch", fetchMock)

    render(<SessionsDashboard token="my-jwt" />)

    await waitFor(() => {
      expect(screen.getByText("session-001")).toBeInTheDocument()
    })
    expect(screen.getByText("session-002")).toBeInTheDocument()
    expect(screen.getByText("session-003")).toBeInTheDocument()

    expect(fetchMock.mock.calls[0][0]).toContain("/v1/sessions")
    expect(fetchMock.mock.calls[0][1]).toMatchObject({
      headers: { Authorization: "Bearer my-jwt" }
    })
  })

  it("refreshes sessions on button click", async () => {
    const user = userEvent.setup()
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve([{ id: "session-old" }])
      })
      .mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve([{ id: "session-old" }, { id: "session-new" }])
      })
    vi.stubGlobal("fetch", fetchMock)

    render(<SessionsDashboard token="jwt" />)

    await waitFor(() => {
      expect(screen.getByText("session-old")).toBeInTheDocument()
    })

    await user.click(screen.getByRole("button", { name: "Refresh Sessions" }))

    await waitFor(() => {
      expect(screen.getByText("session-new")).toBeInTheDocument()
    })

    expect(fetchMock).toHaveBeenCalledTimes(2)
  })

  it("shows loading state on the refresh button", async () => {
    let resolveReq: (value: unknown) => void = () => {}
    const fetchMock = vi.fn().mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveReq = resolve
        })
    )
    vi.stubGlobal("fetch", fetchMock)

    render(<SessionsDashboard token="jwt" />)

    expect(screen.getByRole("button", { name: "Loading..." })).toBeDisabled()

    resolveReq({
      ok: true,
      json: () => Promise.resolve([])
    })

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: "Refresh Sessions" })
      ).toBeEnabled()
    })
  })

  it("handles fetch errors gracefully without crashing", async () => {
    const fetchMock = vi.fn().mockRejectedValue(new Error("Network error"))
    vi.stubGlobal("fetch", fetchMock)

    render(<SessionsDashboard token="jwt" />)

    await waitFor(() => {
      expect(
        screen.getByRole("button", { name: "Refresh Sessions" })
      ).toBeEnabled()
    })

    expect(
      screen.getByText("No historic sessions found or API not wired.")
    ).toBeInTheDocument()
  })

  it("renders session IDs as strong elements inside list items", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve([{ id: "ses-42" }])
    })
    vi.stubGlobal("fetch", fetchMock)

    render(<SessionsDashboard token="jwt" />)

    await waitFor(() => {
      expect(screen.getByText("ses-42")).toBeInTheDocument()
    })

    const strongEl = screen.getByText("ses-42")
    expect(strongEl.tagName).toBe("STRONG")
  })

  it("handles session objects without an id property", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve([{ status: "completed" }])
    })
    vi.stubGlobal("fetch", fetchMock)

    render(<SessionsDashboard token="jwt" />)

    await waitFor(() => {
      expect(screen.getByText("Unknown")).toBeInTheDocument()
    })
  })
})
