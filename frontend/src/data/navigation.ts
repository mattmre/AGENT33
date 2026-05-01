export const APP_TAB_IDS = [
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
  "advanced"
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
  readonly description: string;
}

export const DEFAULT_APP_TAB: AppTab = "guide";
export const ROLE_SELECTED_DEFAULT_APP_TAB: AppTab = "start";

export const APP_TAB_GROUPS: ReadonlyArray<AppTabGroup> = [
  {
    label: "Cockpit",
    tabs: [
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
  }
];

export const APP_PRIMARY_NAV_ITEMS: ReadonlyArray<AppPrimaryNavItem> = [
  {
    id: "start",
    description: "Launch the current workspace, model setup, and next safe action."
  },
  {
    id: "operations",
    description: "Watch active work, recent results, and operator handoffs."
  },
  {
    id: "advanced",
    description: "Open the live control plane with domains, health, and direct runtime calls."
  },
  {
    id: "starter",
    description: "Pick a prebuilt strategy instead of assembling tools manually."
  },
  {
    id: "connect",
    description: "Set up providers, local models, and readiness checks."
  },
  {
    id: "safety",
    description: "Review risks, decisions, and protected actions before work runs."
  },
  {
    id: "guide",
    description: "Capture operator intent before branching into specialized surfaces."
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
