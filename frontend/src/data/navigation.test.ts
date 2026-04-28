import { describe, expect, it } from "vitest";

import { HELP_ASSISTANT_TARGETS } from "../features/help-assistant/types";
import {
  APP_TAB_GROUPS,
  APP_TAB_IDS,
  DEFAULT_APP_TAB,
  ROLE_SELECTED_DEFAULT_APP_TAB,
  getAppTabLabel,
  isAppTab
} from "./navigation";

describe("app navigation registry", () => {
  it("keeps every tab id represented exactly once in navigation groups", () => {
    const groupedTabIds = APP_TAB_GROUPS.flatMap((group) => group.tabs.map((tab) => tab.id));

    expect(new Set(groupedTabIds).size).toBe(groupedTabIds.length);
    expect(groupedTabIds).toEqual(APP_TAB_IDS);
  });

  it("keeps default destinations valid", () => {
    expect(isAppTab(DEFAULT_APP_TAB)).toBe(true);
    expect(isAppTab(ROLE_SELECTED_DEFAULT_APP_TAB)).toBe(true);
  });

  it("keeps Help Assistant targets compatible with app navigation", () => {
    expect(HELP_ASSISTANT_TARGETS.every((target) => isAppTab(target))).toBe(true);
  });

  it("returns beginner-readable labels for registered tabs", () => {
    expect(getAppTabLabel("guide")).toBe("Guide Me");
    expect(getAppTabLabel("advanced")).toBe("Advanced");
  });
});
