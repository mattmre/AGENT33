import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { afterEach, describe, expect, it, vi } from "vitest"

vi.mock("../lib/api", () => ({
  getRuntimeConfig: () => ({ API_BASE_URL: "http://localhost:8000" })
}))

import { GlobalSearch } from "./GlobalSearch"

describe("GlobalSearch", () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it("renders a disabled input without a token", () => {
    render(<GlobalSearch token={null} />)

    expect(screen.getByPlaceholderText("Sign in to use memory search")).toBeDisabled()
  })

  it("renders an enabled input with a token", () => {
    render(<GlobalSearch token="jwt-token" />)

    expect(
      screen.getByPlaceholderText("Search Semantic Memory (PGVector)...")
    ).not.toBeDisabled()
  })

  it("submits a memory-search request with auth", async () => {
    const user = userEvent.setup()
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ results: [] })
    })
    vi.stubGlobal("fetch", fetchMock)

    render(<GlobalSearch token="my-jwt" />)
    await user.type(
      screen.getByPlaceholderText("Search Semantic Memory (PGVector)..."),
      "test query{enter}"
    )

    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(1))
    expect(fetchMock.mock.calls[0][0]).toContain("/v1/memory/search")
    expect(fetchMock.mock.calls[0][1]).toMatchObject({
      method: "POST",
      headers: expect.objectContaining({
        Authorization: "Bearer my-jwt",
        "Content-Type": "application/json"
      })
    })
    expect(JSON.parse(fetchMock.mock.calls[0][1].body as string)).toMatchObject({
      query: "test query",
      level: "full",
      top_k: 3
    })
  })

  it("renders returned search results", async () => {
    const user = userEvent.setup()
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: () =>
        Promise.resolve({
          results: [
            {
              content: "Result one content here that is important",
              token_estimate: 42,
              level: "full"
            },
            {
              content: "Result two content here that is also important",
              token_estimate: 20,
              level: "summary"
            }
          ]
        })
    })
    vi.stubGlobal("fetch", fetchMock)

    render(<GlobalSearch token="tok" />)
    await user.type(
      screen.getByPlaceholderText("Search Semantic Memory (PGVector)..."),
      "search{enter}"
    )

    await waitFor(() => {
      expect(screen.getByText("Memory Results")).toBeInTheDocument()
    })
    expect(screen.getByText(/Result one content/)).toBeInTheDocument()
    expect(screen.getByText(/Result two content/)).toBeInTheDocument()
  })

  it("closes the result panel", async () => {
    const user = userEvent.setup()
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ results: [] })
    })
    vi.stubGlobal("fetch", fetchMock)

    render(<GlobalSearch token="tok" />)
    await user.type(
      screen.getByPlaceholderText("Search Semantic Memory (PGVector)..."),
      "test{enter}"
    )

    await waitFor(() => {
      expect(screen.getByText("No results found.")).toBeInTheDocument()
    })

    await user.click(screen.getByRole("button", { name: "✕" }))

    expect(screen.queryByText("No results found.")).not.toBeInTheDocument()
  })
})
