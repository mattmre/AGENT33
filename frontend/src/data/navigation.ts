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

export interface AppNavItem extends AppTabConfig {
  readonly description: string;
}

export const DEFAULT_APP_TAB: AppTab = "guide";
export const ROLE_SELECTED_DEFAULT_APP_TAB: AppTab = "start";

export const APP_TAB_GROUPS: ReadonlyArray<AppTabGroup> = [
  {
    label: "Start",
    tabs: [
      { id: "guide", label: "Guide Me" },
      { id: "start", label: "Start Here" },
      { id: "connect", label: "Connect" },
      { id: "demo", label: "Demo Mode" },
      { id: "models", label: "Models" },
      { id: "chat", label: "Chat" },
      { id: "voice", label: "Voice" }
    ]
  },
  {
    label: "Operate",
    tabs: [
      { id: "setup", label: "Integrations" },
      { id: "review", label: "Review Queue" },
      { id: "safety", label: "Safety Center" },
      { id: "operations", label: "Operations Hub" }
    ]
  },
  {
    label: "Build",
    tabs: [
      { id: "skills", label: "Skill Wizard" },
      { id: "fabric", label: "Tool Fabric" },
      { id: "mcp", label: "MCP Health" },
      { id: "catalog", label: "Workflow Catalog" },
      { id: "starter", label: "Workflow Starter" },
      { id: "tools", label: "Tools" }
    ]
  },
  {
    label: "Improve",
    tabs: [
      { id: "loops", label: "Improvement Loops" },
      { id: "outcomes", label: "Outcomes" },
      { id: "analytics", label: "Analytics" },
      { id: "impact", label: "Impact" }
    ]
  },
  {
    label: "Extend",
    tabs: [
      { id: "marketplace", label: "Marketplace" },
      { id: "builder", label: "Builder" },
      { id: "spawner", label: "Spawner" },
      { id: "advanced", label: "Advanced" }
    ]
  }
];

export const APP_PRIMARY_NAV_ITEMS: ReadonlyArray<AppNavItem> = [
  {
    id: "guide",
    label: "Guide / Intake",
    description: "Tell AGENT-33 what you want and get the safest next step."
  },
  {
    id: "start",
    label: "Home / Next Step",
    description: "Beginner launchpad for setup, demo runs, and common outcomes."
  },
  {
    id: "operations",
    label: "Sessions & Runs",
    description: "Watch active work, recent results, and operator handoffs."
  },
  {
    id: "starter",
    label: "Workflows",
    description: "Pick a prebuilt strategy instead of assembling tools manually."
  },
  {
    id: "connect",
    label: "Connect Models",
    description: "Set up providers, local models, and readiness checks."
  },
  {
    id: "safety",
    label: "Safety & Approvals",
    description: "Review risks, decisions, and protected actions before work runs."
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
