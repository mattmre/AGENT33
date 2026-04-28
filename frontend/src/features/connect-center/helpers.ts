import type { OnboardingStatus } from "../onboarding/types";
import type { ConnectCard, ConnectStatus } from "./types";

function findStep(status: OnboardingStatus | null, stepId: string): boolean | null {
  const step = status?.steps.find((item) => item.step_id === stepId);
  return step?.completed ?? null;
}

function statusFromStep(status: OnboardingStatus | null, stepId: string): ConnectStatus {
  const completed = findStep(status, stepId);
  if (completed === true) {
    return "ready";
  }
  if (completed === false) {
    return "attention";
  }
  return "unknown";
}

export function buildConnectCards(hasCredentials: boolean, status: OnboardingStatus | null): ConnectCard[] {
  return [
    {
      id: "engine-access",
      title: "Engine access",
      plainLabel: "Can this browser talk to AGENT-33?",
      status: hasCredentials ? "ready" : "attention",
      detail: hasCredentials
        ? "An operator token or API key is saved for this browser session."
        : "Add an operator token or API key before checking live readiness.",
      impact: "Required before the UI can inspect setup, save provider settings, or run workflows.",
      actionLabel: hasCredentials ? "Review access" : "Connect access",
      target: "setup"
    },
    {
      id: "model-provider",
      title: "Model provider",
      plainLabel: "Can AGENT-33 call a model?",
      status: hasCredentials ? statusFromStep(status, "OB-02") : "attention",
      detail: "Connect OpenRouter first, or use a local OpenAI-compatible model path in the next setup round.",
      impact: "Required for real workflow generation, chat, research loops, and agent work.",
      actionLabel: "Open model setup",
      target: "models"
    },
    {
      id: "runtime-memory",
      title: "Runtime and memory",
      plainLabel: "Can agent work keep durable state?",
      status: hasCredentials ? statusFromStep(status, "OB-01") : "unknown",
      detail: "Checks whether the runtime database and state path are ready for longer agent work.",
      impact: "Important for multi-step work, replay, recovery, and long-running workflows.",
      actionLabel: "Open integrations",
      target: "setup"
    },
    {
      id: "mcp-tools",
      title: "MCP tools and skills",
      plainLabel: "Can AGENT-33 use its tool network?",
      status: "unknown",
      detail: "Use MCP Health to inspect proxy servers, tool discovery, CLI sync, and tool fabric readiness.",
      impact: "Unlocks richer research, code analysis, browser automation, and external workflow tools.",
      actionLabel: "Check MCP health",
      target: "mcp"
    },
    {
      id: "tool-catalog",
      title: "Tool catalog",
      plainLabel: "Can users see what tools are available?",
      status: "unknown",
      detail: "Browse available tools and schemas before granting more autonomy.",
      impact: "Makes capabilities discoverable without asking users to understand raw imports or JSON schemas.",
      actionLabel: "Browse tools",
      target: "tools"
    },
    {
      id: "safety-approvals",
      title: "Safety and approvals",
      plainLabel: "Will risky work ask before acting?",
      status: hasCredentials ? statusFromStep(status, "OB-08") : "unknown",
      detail: "Review API protection, approval defaults, and beginner/pro controls before automation runs.",
      impact: "Protects users from destructive operations while keeping productive paths visible.",
      actionLabel: "Open safety",
      target: "safety"
    }
  ];
}

export function getConnectScore(cards: ConnectCard[]): string {
  const knownCards = cards.filter((card) => card.status !== "unknown");
  if (knownCards.length === 0) {
    return "Readiness unknown";
  }
  const readyCount = knownCards.filter((card) => card.status === "ready").length;
  return `${readyCount} of ${knownCards.length} known checks ready`;
}
