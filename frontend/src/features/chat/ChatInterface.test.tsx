import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

const { apiRequestMock } = vi.hoisted(() => ({
  apiRequestMock: vi.fn()
}))

vi.mock("../../lib/api", () => ({
  apiRequest: apiRequestMock,
  getRuntimeConfig: () => ({ API_BASE_URL: "http://localhost:8000" })
}))

import { ChatInterface } from "./ChatInterface"

// SpeechSynthesis and SpeechRecognition are browser APIs not available in jsdom.
// Stub them so the component can mount without crashing.
function stubSpeechApis() {
  const speechSynthesisMock = {
    getVoices: vi.fn().mockReturnValue([]),
    speak: vi.fn(),
    cancel: vi.fn(),
    onvoiceschanged: null as (() => void) | null,
    speaking: false
  }
  Object.defineProperty(window, "speechSynthesis", {
    value: speechSynthesisMock,
    writable: true,
    configurable: true
  })
  return speechSynthesisMock
}

// jsdom does not implement scrollIntoView; stub it so the component can render.
beforeEach(() => {
  Element.prototype.scrollIntoView = vi.fn()
})

describe("ChatInterface", () => {
  beforeEach(() => {
    stubSpeechApis()
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  it("renders the initial assistant greeting", () => {
    render(<ChatInterface token="jwt" apiKey="" />)

    expect(
      screen.getByText("Hello! I am AGENT-33. How can I assist you today?")
    ).toBeInTheDocument()
  })

  it("renders the message input area", () => {
    render(<ChatInterface token="jwt" apiKey="" />)

    expect(
      screen.getByPlaceholderText("Message AGENT-33 (or click the mic to speak)...")
    ).toBeInTheDocument()
  })

  it("sends a user message and displays the assistant reply", async () => {
    const user = userEvent.setup()

    apiRequestMock.mockResolvedValue({
      ok: true,
      status: 200,
      data: {
        choices: [
          {
            message: {
              content: "I can help with that workflow."
            }
          }
        ]
      }
    })

    render(<ChatInterface token="jwt" apiKey="key" />)

    const textarea = screen.getByPlaceholderText(
      "Message AGENT-33 (or click the mic to speak)..."
    )
    await user.type(textarea, "Run my workflow")
    await user.click(screen.getByTitle("Send (Enter)"))

    expect(screen.getByText("Run my workflow")).toBeInTheDocument()

    await waitFor(() => {
      expect(
        screen.getByText("I can help with that workflow.")
      ).toBeInTheDocument()
    })

    expect(apiRequestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        method: "POST",
        path: "/v1/chat/completions"
      })
    )

    const body = JSON.parse(apiRequestMock.mock.calls[0][0].body as string)
    expect(body.model).toBe("qwen3-coder:30b")
    expect(body.temperature).toBe(0.2)
    const lastMessage = body.messages[body.messages.length - 1]
    expect(lastMessage.role).toBe("user")
    expect(lastMessage.content).toBe("Run my workflow")
  })

  it("clears the input after sending", async () => {
    const user = userEvent.setup()

    apiRequestMock.mockResolvedValue({
      ok: true,
      status: 200,
      data: { choices: [{ message: { content: "done" } }] }
    })

    render(<ChatInterface token="jwt" apiKey="" />)

    const textarea = screen.getByPlaceholderText(
      "Message AGENT-33 (or click the mic to speak)..."
    )
    await user.type(textarea, "hello")
    await user.click(screen.getByTitle("Send (Enter)"))

    expect(textarea).toHaveValue("")
  })

  it("shows loading indicator while waiting for response", async () => {
    const user = userEvent.setup()
    let resolveApi: (value: unknown) => void = () => {}

    apiRequestMock.mockImplementation(
      () =>
        new Promise((resolve) => {
          resolveApi = resolve
        })
    )

    render(<ChatInterface token="jwt" apiKey="" />)

    const textarea = screen.getByPlaceholderText(
      "Message AGENT-33 (or click the mic to speak)..."
    )
    await user.type(textarea, "test")
    await user.click(screen.getByTitle("Send (Enter)"))

    expect(textarea).toBeDisabled()
    expect(document.querySelector(".typing-indicator")).not.toBeNull()

    resolveApi({
      ok: true,
      status: 200,
      data: { choices: [{ message: { content: "reply" } }] }
    })

    await waitFor(() => {
      expect(textarea).toBeEnabled()
    })
  })

  it("displays an error message when API returns 401", async () => {
    const user = userEvent.setup()

    apiRequestMock.mockResolvedValue({
      ok: false,
      status: 401,
      data: null
    })

    render(<ChatInterface token="jwt" apiKey="" />)

    const textarea = screen.getByPlaceholderText(
      "Message AGENT-33 (or click the mic to speak)..."
    )
    await user.type(textarea, "test")
    await user.click(screen.getByTitle("Send (Enter)"))

    await waitFor(() => {
      expect(
        screen.getByText(/Unauthorized \(401\)/)
      ).toBeInTheDocument()
    })
  })

  it("displays an error message when API returns a non-401 error", async () => {
    const user = userEvent.setup()

    apiRequestMock.mockResolvedValue({
      ok: false,
      status: 500,
      data: null
    })

    render(<ChatInterface token="jwt" apiKey="" />)

    const textarea = screen.getByPlaceholderText(
      "Message AGENT-33 (or click the mic to speak)..."
    )
    await user.type(textarea, "test")
    await user.click(screen.getByTitle("Send (Enter)"))

    await waitFor(() => {
      expect(screen.getByText(/API Error: 500/)).toBeInTheDocument()
    })
  })

  it("displays error when apiRequest throws a network error", async () => {
    const user = userEvent.setup()

    apiRequestMock.mockRejectedValue(new Error("Connection refused"))

    render(<ChatInterface token="jwt" apiKey="" />)

    const textarea = screen.getByPlaceholderText(
      "Message AGENT-33 (or click the mic to speak)..."
    )
    await user.type(textarea, "test")
    await user.click(screen.getByTitle("Send (Enter)"))

    await waitFor(() => {
      expect(screen.getByText(/Connection refused/)).toBeInTheDocument()
    })
  })

  it("sends message on Enter key (without Shift)", async () => {
    const user = userEvent.setup()

    apiRequestMock.mockResolvedValue({
      ok: true,
      status: 200,
      data: { choices: [{ message: { content: "reply via enter" } }] }
    })

    render(<ChatInterface token="jwt" apiKey="" />)

    const textarea = screen.getByPlaceholderText(
      "Message AGENT-33 (or click the mic to speak)..."
    )
    await user.type(textarea, "enter test{enter}")

    await waitFor(() => {
      expect(screen.getByText("reply via enter")).toBeInTheDocument()
    })
  })

  it("does not send on empty input", async () => {
    const user = userEvent.setup()

    render(<ChatInterface token="jwt" apiKey="" />)

    await user.click(screen.getByTitle("Send (Enter)"))

    expect(apiRequestMock).not.toHaveBeenCalled()
  })

  it("does not render system messages in the chat", () => {
    render(<ChatInterface token="jwt" apiKey="" />)

    expect(
      screen.queryByText("You are a helpful AI assistant.")
    ).not.toBeInTheDocument()
  })

  it("shows settings popover when gear button is clicked", async () => {
    const user = userEvent.setup()

    render(<ChatInterface token="jwt" apiKey="" />)

    await user.click(screen.getByTitle("Chat Settings"))

    expect(screen.getByText("Chat Settings")).toBeInTheDocument()
    expect(screen.getByText("Translation Options")).toBeInTheDocument()
    expect(screen.getByText("Audio Response")).toBeInTheDocument()
  })

  it("closes settings popover with close button", async () => {
    const user = userEvent.setup()

    render(<ChatInterface token="jwt" apiKey="" />)

    await user.click(screen.getByTitle("Chat Settings"))
    expect(screen.getByText("Chat Settings")).toBeInTheDocument()

    const closeBtn = document.querySelector(".settings-close-btn")
    expect(closeBtn).not.toBeNull()
    await user.click(closeBtn!)

    expect(screen.queryByText("Translation Options")).not.toBeInTheDocument()
  })

  it("passes auth credentials through to the API request", async () => {
    const user = userEvent.setup()

    apiRequestMock.mockResolvedValue({
      ok: true,
      status: 200,
      data: { choices: [{ message: { content: "ok" } }] }
    })

    render(<ChatInterface token="my-jwt-token" apiKey="a33_key" />)

    const textarea = screen.getByPlaceholderText(
      "Message AGENT-33 (or click the mic to speak)..."
    )
    await user.type(textarea, "hello{enter}")

    await waitFor(() => {
      expect(apiRequestMock).toHaveBeenCalledTimes(1)
    })

    expect(apiRequestMock).toHaveBeenCalledWith(
      expect.objectContaining({
        token: "my-jwt-token",
        apiKey: "a33_key"
      })
    )
  })
})
