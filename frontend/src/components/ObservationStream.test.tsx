import { render, screen, waitFor } from "@testing-library/react"
import { afterEach, describe, expect, it, vi } from "vitest"

import { ObservationStream } from "./ObservationStream"

function buildSseResponse(bodyText: string): Response {
  const encoder = new TextEncoder()
  const body = new ReadableStream<Uint8Array>({
    start(controller) {
      controller.enqueue(encoder.encode(bodyText))
      controller.close()
    }
  })
  return new Response(body, {
    status: 200,
    headers: { "content-type": "text/event-stream" }
  })
}

describe("ObservationStream", () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it("renders nothing when no token is provided", () => {
    const { container } = render(<ObservationStream token={null} />)

    expect(container.innerHTML).toBe("")
  })

  it("connects to the stream with bearer auth", async () => {
    const fetchMock = vi.fn().mockResolvedValue(buildSseResponse(""))
    vi.stubGlobal("fetch", fetchMock)

    render(<ObservationStream token="my-jwt" />)

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1))
    expect(fetchMock.mock.calls[0][0]).toContain("/v1/operations/stream")
    expect(fetchMock.mock.calls[0][1]).toMatchObject({
      headers: { Authorization: "Bearer my-jwt" }
    })
  })

  it("renders allowed core-mechanics events", async () => {
    const event = {
      id: "ev-1",
      agent_name: "orchestrator",
      event_type: "handoff_context_wipe",
      content: "Context wiped for handoff",
      timestamp: new Date().toISOString()
    }

    const fetchMock = vi
      .fn()
      .mockResolvedValue(buildSseResponse(`data: ${JSON.stringify(event)}\n\n`))
    vi.stubGlobal("fetch", fetchMock)

    render(<ObservationStream token="tok" />)

    await waitFor(() => {
      expect(screen.getByText("Live Core Mechanics")).toBeInTheDocument()
    })
    expect(screen.getByText("Context wiped for handoff")).toBeInTheDocument()
    expect(screen.getByText("orchestrator")).toBeInTheDocument()
  })

  it("filters irrelevant events out of the stream", async () => {
    const irrelevantEvent = {
      id: "ev-2",
      agent_name: "worker",
      event_type: "generic_event",
      content: "Something irrelevant",
      timestamp: new Date().toISOString()
    }

    const fetchMock = vi
      .fn()
      .mockResolvedValue(buildSseResponse(`data: ${JSON.stringify(irrelevantEvent)}\n\n`))
    vi.stubGlobal("fetch", fetchMock)

    const { container } = render(<ObservationStream token="tok" />)

    await waitFor(() => expect(fetchMock).toHaveBeenCalled())
    await new Promise((resolve) => setTimeout(resolve, 50))

    expect(container.querySelector(".observation-stream")).toBeNull()
  })

  it("keeps at most ten events in newest-first order", async () => {
    const events = Array.from({ length: 12 }, (_, index) => ({
      id: `ev-${index}`,
      agent_name: "orch",
      event_type: "handoff_context_wipe",
      content: `Wipe ${index}`,
      timestamp: new Date().toISOString()
    }))

    const ssePayload = events.map((event) => `data: ${JSON.stringify(event)}\n\n`).join("")
    const fetchMock = vi.fn().mockResolvedValue(buildSseResponse(ssePayload))
    vi.stubGlobal("fetch", fetchMock)

    render(<ObservationStream token="tok" />)

    await waitFor(() => {
      expect(screen.getByText("Live Core Mechanics")).toBeInTheDocument()
    })

    expect(document.querySelectorAll(".observation-item").length).toBeLessThanOrEqual(10)
    expect(screen.getByText("Wipe 11")).toBeInTheDocument()
  })

  it("cancels the stream reader on unmount", async () => {
    const cancelMock = vi.fn().mockResolvedValue(undefined)
    const mockReader = {
      read: vi.fn().mockResolvedValue({ done: true, value: undefined }),
      cancel: cancelMock
    }

    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      body: { getReader: () => mockReader }
    })
    vi.stubGlobal("fetch", fetchMock)

    const { unmount } = render(<ObservationStream token="tok" />)
    await waitFor(() => expect(fetchMock).toHaveBeenCalled())

    unmount()

    await waitFor(() => expect(cancelMock).toHaveBeenCalled())
  })
})
