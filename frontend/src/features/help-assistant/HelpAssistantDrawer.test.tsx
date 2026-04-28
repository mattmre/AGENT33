import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { HelpAssistantDrawer } from "./HelpAssistantDrawer";

describe("HelpAssistantDrawer", () => {
  it("opens the offline assistant and answers OpenRouter setup questions with citations", async () => {
    const user = userEvent.setup();

    render(<HelpAssistantDrawer onNavigate={vi.fn()} />);

    await user.click(screen.getByRole("button", { name: "Ask AGENT33" }));
    await user.type(screen.getByPlaceholderText("How do I connect OpenRouter?"), "connect openrouter");

    expect(screen.getByRole("heading", { name: "Connect OpenRouter" })).toBeInTheDocument();
    expect(screen.getByText(/OPENROUTER_API_KEY/)).toBeInTheDocument();
    expect(screen.getByText(/does not call an external model/)).toBeInTheDocument();
    expect(screen.getByText("Sources used for this answer")).toBeInTheDocument();
  });

  it("routes action buttons through the app navigation callback", async () => {
    const user = userEvent.setup();
    const onNavigate = vi.fn();

    render(<HelpAssistantDrawer onNavigate={onNavigate} />);

    await user.click(screen.getByRole("button", { name: "Ask AGENT33" }));
    await user.click(screen.getByRole("button", { name: "Connect OpenRouter" }));
    await user.click(screen.getByRole("button", { name: "Open Models" }));

    expect(onNavigate).toHaveBeenCalledWith("models");
  });

  it("opens Demo Mode directly from the guide help article", async () => {
    const user = userEvent.setup();
    const onNavigate = vi.fn();

    render(<HelpAssistantDrawer onNavigate={onNavigate} />);

    await user.click(screen.getByRole("button", { name: "Ask AGENT33" }));
    await user.click(screen.getByRole("button", { name: "Try Demo Mode" }));

    expect(onNavigate).toHaveBeenCalledWith("demo");
  });
});
