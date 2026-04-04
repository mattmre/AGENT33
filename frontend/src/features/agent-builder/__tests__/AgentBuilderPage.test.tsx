import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import AgentBuilderPage from "../AgentBuilderPage";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("AgentBuilderPage", () => {
  const fetchMock = vi.fn<typeof fetch>();

  beforeEach(() => {
    vi.stubGlobal("fetch", fetchMock);
    window.__AGENT33_CONFIG__ = { API_BASE_URL: "http://localhost:8000" };
    // By default, resolve preview requests
    fetchMock.mockResolvedValue(
      jsonResponse({ system_prompt: "# Identity\nYou are 'test-agent'..." }),
    );
  });

  afterEach(() => {
    delete window.__AGENT33_CONFIG__;
    vi.restoreAllMocks();
  });

  it("renders all capability toggle questions", () => {
    render(<AgentBuilderPage token="test-token" />);
    expect(screen.getByText(/Can it read your files/i)).toBeInTheDocument();
    expect(
      screen.getByText(/Can it write to your files/i),
    ).toBeInTheDocument();
    expect(screen.getByText(/Can it search the web/i)).toBeInTheDocument();
    expect(screen.getByText(/Can it run code/i)).toBeInTheDocument();
    expect(
      screen.getByText(/Can it connect to external services/i),
    ).toBeInTheDocument();
  });

  it("renders save and export buttons", () => {
    render(<AgentBuilderPage token="test-token" />);
    expect(
      screen.getByRole("button", { name: /save agent/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /export json/i }),
    ).toBeInTheDocument();
  });

  it("renders the name, description, role, and version fields", () => {
    render(<AgentBuilderPage token="test-token" />);
    expect(screen.getByPlaceholderText("my-agent")).toBeInTheDocument();
    expect(
      screen.getByPlaceholderText("What does this agent do?"),
    ).toBeInTheDocument();
    expect(screen.getByDisplayValue("implementer")).toBeInTheDocument();
    expect(screen.getByDisplayValue("1.0.0")).toBeInTheDocument();
  });

  it("validates agent name format", async () => {
    const user = userEvent.setup();
    render(<AgentBuilderPage token="test-token" />);

    const nameInput = screen.getByPlaceholderText("my-agent");
    await user.type(nameInput, "Bad Name!");

    expect(screen.getByRole("alert")).toHaveTextContent(
      /must start with a lowercase letter/i,
    );
  });

  it("clears name error when valid name is entered", async () => {
    const user = userEvent.setup();
    render(<AgentBuilderPage token="test-token" />);

    const nameInput = screen.getByPlaceholderText("my-agent");

    // First type an invalid name
    await user.type(nameInput, "X");
    expect(screen.getByRole("alert")).toBeInTheDocument();

    // Clear and type a valid name
    await user.clear(nameInput);
    await user.type(nameInput, "valid-agent");
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("toggles capability switches", async () => {
    const user = userEvent.setup();
    render(<AgentBuilderPage token="test-token" />);

    const switches = screen.getAllByRole("switch");
    expect(switches).toHaveLength(5);

    // All off initially
    for (const sw of switches) {
      expect(sw).toHaveAttribute("aria-checked", "false");
    }

    // Toggle the first one on
    await user.click(switches[0]);
    expect(switches[0]).toHaveAttribute("aria-checked", "true");

    // Toggle it back off
    await user.click(switches[0]);
    expect(switches[0]).toHaveAttribute("aria-checked", "false");
  });

  it("disables save button when name is empty", () => {
    render(<AgentBuilderPage token="test-token" />);

    const saveBtn = screen.getByRole("button", { name: /save agent/i });
    expect(saveBtn).toBeDisabled();
  });

  it("fetches prompt preview after filling in the name", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });
    render(<AgentBuilderPage token="test-token" />);

    const nameInput = screen.getByPlaceholderText("my-agent");
    await user.type(nameInput, "my-agent");

    // Advance past the 500ms debounce
    vi.advanceTimersByTime(600);

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "http://localhost:8000/v1/agents/preview-prompt",
        expect.objectContaining({ method: "POST" }),
      );
    });

    vi.useRealTimers();
  });

  it("displays the system prompt preview text", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const user = userEvent.setup({ advanceTimers: vi.advanceTimersByTime });

    fetchMock.mockResolvedValue(
      jsonResponse({ system_prompt: "# Identity\nYou are 'demo-agent'." }),
    );

    render(<AgentBuilderPage token="test-token" />);

    const nameInput = screen.getByPlaceholderText("my-agent");
    await user.type(nameInput, "demo-agent");
    vi.advanceTimersByTime(600);

    await waitFor(() => {
      expect(
        screen.getByText(/You are 'demo-agent'/),
      ).toBeInTheDocument();
    });

    vi.useRealTimers();
  });

  it("shows placeholder text when preview is empty", () => {
    render(<AgentBuilderPage token="test-token" />);
    expect(
      screen.getByText(/fill in the agent details to see a live preview/i),
    ).toBeInTheDocument();
  });

  it("shows the test section with input and button", () => {
    render(<AgentBuilderPage token="test-token" />);
    expect(
      screen.getByPlaceholderText("Type a test message..."),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: /^test$/i }),
    ).toBeInTheDocument();
  });

  it("has a role selector with the correct options", () => {
    render(<AgentBuilderPage token="test-token" />);

    const select = screen.getByDisplayValue("implementer");
    expect(select.tagName).toBe("SELECT");

    const options = Array.from(
      (select as HTMLSelectElement).options,
    ).map((o) => o.value);
    expect(options).toContain("orchestrator");
    expect(options).toContain("researcher");
    expect(options).toContain("qa");
    expect(options).toContain("architect");
  });

  it("renders the header", () => {
    render(<AgentBuilderPage token="test-token" />);
    expect(screen.getByText("Agent Builder")).toBeInTheDocument();
  });
});
