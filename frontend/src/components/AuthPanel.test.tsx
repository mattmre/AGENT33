import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { useState } from "react"
import { afterEach, describe, expect, it, vi } from "vitest"

const { apiRequestMock } = vi.hoisted(() => ({
  apiRequestMock: vi.fn()
}))

vi.mock("../lib/api", () => ({
  apiRequest: apiRequestMock,
  getRuntimeConfig: () => ({ API_BASE_URL: "http://localhost:8000" })
}))

import { AuthPanel } from "./AuthPanel"

function AuthPanelHarness(props: {
  onTokenChange?: (token: string) => void
  onApiKeyChange?: (apiKey: string) => void
}): JSX.Element {
  const [token, setToken] = useState("")
  const [apiKey, setApiKey] = useState("")

  return (
    <AuthPanel
      token={token}
      apiKey={apiKey}
      onTokenChange={(nextToken) => {
        setToken(nextToken)
        props.onTokenChange?.(nextToken)
      }}
      onApiKeyChange={(nextApiKey) => {
        setApiKey(nextApiKey)
        props.onApiKeyChange?.(nextApiKey)
      }}
    />
  )
}

describe("AuthPanel", () => {
  afterEach(() => {
    vi.clearAllMocks()
  })

  it("renders the access-control form", () => {
    render(
      <AuthPanel token="" apiKey="" onTokenChange={vi.fn()} onApiKeyChange={vi.fn()} />
    )

    expect(screen.getByText("Access Control")).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Sign In" })).toBeInTheDocument()
    expect(screen.getByPlaceholderText("Paste JWT token")).toBeInTheDocument()
    expect(screen.getByPlaceholderText("a33_xxx...")).toBeInTheDocument()
  })

  it("forwards bearer-token textarea edits", async () => {
    const user = userEvent.setup()
    const onTokenChange = vi.fn()

    render(<AuthPanelHarness onTokenChange={onTokenChange} />)

    const textarea = screen.getByPlaceholderText("Paste JWT token")
    await user.type(textarea, "abc")

    expect(onTokenChange).toHaveBeenCalledTimes(3)
    expect(onTokenChange).toHaveBeenLastCalledWith("abc")
    expect(textarea).toHaveValue("abc")
  })

  it("forwards api-key input edits", async () => {
    const user = userEvent.setup()
    const onApiKeyChange = vi.fn()

    render(<AuthPanelHarness onApiKeyChange={onApiKeyChange} />)

    const input = screen.getByPlaceholderText("a33_xxx...")
    await user.type(input, "key")

    expect(onApiKeyChange).toHaveBeenCalledTimes(3)
    expect(onApiKeyChange).toHaveBeenLastCalledWith("key")
    expect(input).toHaveValue("key")
  })

  it("signs in and forwards the returned token", async () => {
    const user = userEvent.setup()
    const onTokenChange = vi.fn()

    apiRequestMock.mockResolvedValue({
      ok: true,
      status: 200,
      data: { access_token: "jwt-from-server" }
    })

    render(
      <AuthPanel
        token=""
        apiKey=""
        onTokenChange={onTokenChange}
        onApiKeyChange={vi.fn()}
      />
    )

    await user.click(screen.getByRole("button", { name: "Sign In" }))

    await waitFor(() => {
      expect(onTokenChange).toHaveBeenCalledWith("jwt-from-server")
    })

    expect(apiRequestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        method: "POST",
        path: "/v1/auth/token"
      })
    )
  })

  it("shows a response-status error when login fails", async () => {
    const user = userEvent.setup()

    apiRequestMock.mockResolvedValue({
      ok: false,
      status: 401,
      data: null
    })

    render(
      <AuthPanel token="" apiKey="" onTokenChange={vi.fn()} onApiKeyChange={vi.fn()} />
    )

    await user.click(screen.getByRole("button", { name: "Sign In" }))

    await waitFor(() => {
      expect(screen.getByText("Login failed (401)")).toBeInTheDocument()
    })
  })
})
