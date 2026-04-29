import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { afterEach, describe, expect, it, vi } from "vitest"

import { MessagingSetup } from "./MessagingSetup"

describe("MessagingSetup", () => {
  afterEach(() => {
    vi.restoreAllMocks()
  })

  it("renders the messaging integrations heading", () => {
    render(<MessagingSetup />)

    expect(screen.getByText("Messaging Integrations")).toBeInTheDocument()
    expect(
      screen.getByText(
        "Connect your agent to external messaging platforms to chat from anywhere."
      )
    ).toBeInTheDocument()
  })

  it("renders all four platform cards", () => {
    render(<MessagingSetup />)

    expect(screen.getByText("Telegram")).toBeInTheDocument()
    expect(screen.getByText("Discord")).toBeInTheDocument()
    expect(screen.getByText("Signal")).toBeInTheDocument()
    expect(screen.getByText("iMessage")).toBeInTheDocument()
  })

  it("renders platform descriptions", () => {
    render(<MessagingSetup />)

    expect(
      screen.getByText("Connect via official Telegram Bot API.")
    ).toBeInTheDocument()
    expect(
      screen.getByText("Connect via Discord Developer Portal.")
    ).toBeInTheDocument()
    expect(
      screen.getByText("Requires a self-hosted signal-cli REST bridge.")
    ).toBeInTheDocument()
    expect(
      screen.getByText("Requires BlueBubbles or a macOS AppleScript bridge.")
    ).toBeInTheDocument()
  })

  it("renders connect buttons for each platform", () => {
    render(<MessagingSetup />)

    expect(
      screen.getByRole("button", { name: "Connect Telegram" })
    ).toBeInTheDocument()
    expect(
      screen.getByRole("button", { name: "Connect Discord" })
    ).toBeInTheDocument()
    expect(
      screen.getByRole("button", { name: "Connect Signal" })
    ).toBeInTheDocument()
    expect(
      screen.getByRole("button", { name: "Connect iMessage" })
    ).toBeInTheDocument()
  })

  it("accepts Telegram bot token input", async () => {
    const user = userEvent.setup()

    render(<MessagingSetup />)

    const input = screen.getByPlaceholderText("123456789:ABCdefGHIjklMNO...")
    await user.type(input, "my-bot-token")

    expect(input).toHaveValue("my-bot-token")
  })

  it("accepts Discord bot token input", async () => {
    const user = userEvent.setup()

    render(<MessagingSetup />)

    const input = screen.getByPlaceholderText("MTAxMjM0NTY3ODkw...")
    await user.type(input, "discord-token")

    expect(input).toHaveValue("discord-token")
  })

  it("accepts Signal bridge URL input", async () => {
    const user = userEvent.setup()

    render(<MessagingSetup />)

    const input = screen.getByPlaceholderText("http://localhost:8080")
    await user.type(input, "http://signal.local:9090")

    expect(input).toHaveValue("http://signal.local:9090")
  })

  it("accepts iMessage bridge URL input", async () => {
    const user = userEvent.setup()

    render(<MessagingSetup />)

    const input = screen.getByPlaceholderText("http://mac-mini.local:1234")
    await user.type(input, "http://my-mac.local:5678")

    expect(input).toHaveValue("http://my-mac.local:5678")
  })

  it("calls alert with platform name when connect button is clicked", async () => {
    const user = userEvent.setup()
    const alertMock = vi.spyOn(window, "alert").mockImplementation(() => {})

    render(<MessagingSetup />)

    await user.click(
      screen.getByRole("button", { name: "Connect Telegram" })
    )

    expect(alertMock).toHaveBeenCalledWith("Telegram configuration saved!")

    await user.click(
      screen.getByRole("button", { name: "Connect Discord" })
    )

    expect(alertMock).toHaveBeenCalledWith("Discord configuration saved!")
  })

  it("uses password input type for bot token fields", () => {
    render(<MessagingSetup />)

    const telegramInput = screen.getByPlaceholderText("123456789:ABCdefGHIjklMNO...")
    const discordInput = screen.getByPlaceholderText("MTAxMjM0NTY3ODkw...")

    expect(telegramInput).toHaveAttribute("type", "password")
    expect(discordInput).toHaveAttribute("type", "password")
  })

  it("uses text input type for URL fields", () => {
    render(<MessagingSetup />)

    const signalInput = screen.getByPlaceholderText("http://localhost:8080")
    const imessageInput = screen.getByPlaceholderText("http://mac-mini.local:1234")

    expect(signalInput).toHaveAttribute("type", "text")
    expect(imessageInput).toHaveAttribute("type", "text")
  })
})
