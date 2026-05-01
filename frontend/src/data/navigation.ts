export const APP_TAB_IDS = [
  "cockpit",
  "guide",
  "start",
  "connect",
  "demo",
  "models",
  "chat",
  "voice",
  "setup",
  "review",
  "safety",
  "operations",
  "skills",
  "fabric",
  "mcp",
  "catalog",
  "starter",
  "tools",
  "loops",
  "outcomes",
  "analytics",
  "impact",
  "marketplace",
  "builder",
  "spawner",
  "advanced",
  "design-kit"
] as const;

export type AppTab = (typeof APP_TAB_IDS)[number];

export interface AppTabConfig {
  readonly id: AppTab;
  readonly label: string;
}

export interface AppTabGroup {
  readonly label: string;
  readonly tabs: ReadonlyArray<AppTabConfig>;
}

export interface AppPrimaryNavItem {
  readonly id: AppTab;
  readonly label?: string;
  readonly description: string;
}

export const DEFAULT_APP_TAB: AppTab = "cockpit";
export const ROLE_SELECTED_DEFAULT_APP_TAB: AppTab = "cockpit";

export const APP_TAB_GROUPS: ReadonlyArray<AppTabGroup> = [
  {
    label: "Cockpit",
    tabs: [
      { id: "cockpit", label: "Operations Cockpit" },
      { id: "guide", label: "Guide / Intake" },
      { id: "start", label: "Home / Next Step" },
      { id: "operations", label: "Sessions & Runs" },
      { id: "advanced", label: "Control Plane" },
      { id: "connect", label: "Connect Models" },
      { id: "demo", label: "Demo Mode" },
      { id: "models", label: "Models" },
      { id: "chat", label: "Chat" },
      { id: "voice", label: "Voice" }
    ]
  },
  {
    label: "Build",
    tabs: [
      { id: "catalog", label: "Workflow Catalog" },
      { id: "starter", label: "Workflow Starter" },
      { id: "skills", label: "Skill Wizard" },
      { id: "fabric", label: "Tool Fabric" },
      { id: "tools", label: "Tool Catalog" },
      { id: "builder", label: "Agent Builder" },
      { id: "spawner", label: "Spawner" },
      { id: "marketplace", label: "Marketplace" }
    ]
  },
  {
    label: "Inspect",
    tabs: [
      { id: "review", label: "Review Queue" },
      { id: "outcomes", label: "Outcomes" },
      { id: "analytics", label: "Analytics" },
      { id: "impact", label: "Impact" },
      { id: "mcp", label: "MCP Health" }
    ]
  },
  {
    label: "Govern",
    tabs: [
      { id: "safety", label: "Safety & Approvals" },
      { id: "setup", label: "Integrations" },
      { id: "loops", label: "Improvement Loops" }
    ]
  },
  {
    label: "Reference",
    tabs: [
      { id: "design-kit", label: "Design Kit Surfaces" }
    ]
  }
];

export const APP_PRIMARY_NAV_ITEMS: ReadonlyArray<AppPrimaryNavItem> = [
  {
    id: "cockpit",
    label: "Operations Cockpit",
    description: "Active project · gates"
  },
  {
    id: "operations",
    label: "Sessions & Runs",
    description: "Traces · blockers · reviews"
  },
  {
    id: "starter",
    label: "Workflows",
    description: "Starters · execution"
  },
  {
    id: "advanced",
    label: "Agents & API",
    description: "Invoke · configure · scope"
  }
];

const APP_PRIMARY_TAB_ID_SET = new Set<AppTab>(APP_PRIMARY_NAV_ITEMS.map((item) => item.id));

export const APP_SECONDARY_NAV_GROUPS: ReadonlyArray<AppTabGroup> = APP_TAB_GROUPS.map((group) => ({
  ...group,
  tabs: group.tabs.filter((tab) => !APP_PRIMARY_TAB_ID_SET.has(tab.id))
})).filter((group) => group.tabs.length > 0);

const APP_TAB_ID_SET = new Set<string>(APP_TAB_IDS);
const APP_TAB_LABEL_MAP = new Map<AppTab, string>(
  APP_TAB_GROUPS.flatMap((group) => group.tabs.map((tab) => [tab.id, tab.label] as const))
);

export function isAppTab(value: string): value is AppTab {
  return APP_TAB_ID_SET.has(value);
}

export function getAppTabLabel(tabId: AppTab): string {
  return APP_TAB_LABEL_MAP.get(tabId) ?? tabId;
}

export function isPrimaryAppTab(tabId: AppTab): boolean {
  return APP_PRIMARY_TAB_ID_SET.has(tabId);
}

export function isSecondaryAppTab(tabId: AppTab): boolean {
  return !APP_PRIMARY_TAB_ID_SET.has(tabId);
}
