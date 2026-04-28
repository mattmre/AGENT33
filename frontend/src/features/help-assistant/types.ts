export const HELP_ASSISTANT_TARGETS = [
  "start",
  "demo",
  "models",
  "setup",
  "catalog",
  "starter",
  "operations",
  "safety",
  "mcp",
  "advanced"
] as const;

export type HelpAssistantTarget = (typeof HELP_ASSISTANT_TARGETS)[number];

export interface HelpSource {
  label: string;
  path: string;
}

export interface HelpAction {
  label: string;
  target: HelpAssistantTarget;
}

export interface HelpArticle {
  id: string;
  title: string;
  audience: string;
  summary: string;
  body: string[];
  steps: string[];
  keywords: string[];
  sources: HelpSource[];
  actions: HelpAction[];
}

export interface HelpSearchResult {
  article: HelpArticle;
  score: number;
  matchedTerms: string[];
}
