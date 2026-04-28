import { describe, expect, it } from "vitest";

import { buildConnectCards, getConnectScore } from "./helpers";
import type { OnboardingStatus } from "../onboarding/types";

const READY_STATUS: OnboardingStatus = {
  completed_count: 2,
  total_count: 3,
  overall_complete: false,
  steps: [
    {
      step_id: "OB-01",
      category: "runtime",
      title: "Database",
      description: "Runtime database",
      completed: true,
      remediation: ""
    },
    {
      step_id: "OB-02",
      category: "models",
      title: "Model",
      description: "Model provider",
      completed: true,
      remediation: ""
    },
    {
      step_id: "OB-08",
      category: "api",
      title: "API",
      description: "API protection",
      completed: false,
      remediation: "Review API safety."
    }
  ]
};

describe("connect center helpers", () => {
  it("builds beginner-readable connection cards from onboarding status", () => {
    const cards = buildConnectCards(true, READY_STATUS);

    expect(cards).toHaveLength(6);
    expect(cards.find((card) => card.id === "model-provider")?.status).toBe("ready");
    expect(cards.find((card) => card.id === "safety-approvals")?.status).toBe("attention");
    expect(cards.every((card) => card.actionLabel.length > 0)).toBe(true);
  });

  it("marks engine access as attention when credentials are missing", () => {
    const cards = buildConnectCards(false, null);

    expect(cards[0]).toMatchObject({
      id: "engine-access",
      status: "attention",
      target: "setup"
    });
  });

  it("summarizes known readiness without counting unknown cards", () => {
    expect(getConnectScore(buildConnectCards(true, READY_STATUS))).toBe("3 of 4 known checks ready");
  });
});
