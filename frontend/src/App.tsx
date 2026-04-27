import { useMemo, useState } from "react";

import { AuthPanel } from "./components/AuthPanel";
import { DomainPanel } from "./components/DomainPanel";
import { HealthPanel } from "./components/HealthPanel";
import { GlobalSearch } from "./components/GlobalSearch";
import { SkipLink } from "./components/SkipLink";
import { LiveVoicePanel } from "./features/voice/LiveVoicePanel";
import { ObservationStream } from "./components/ObservationStream";
import { MessagingSetup } from "./features/integrations/MessagingSetup";
import { ChatInterface } from "./features/chat/ChatInterface";
import { OperationsHubPanel } from "./features/operations-hub/OperationsHubPanel";
import { IngestionReviewPanel } from "./features/operations-hub/IngestionReviewPanel";
import { OutcomesDashboardPanel } from "./features/outcomes-dashboard/OutcomesDashboardPanel";
import { SessionAnalyticsDashboard } from "./features/session-analytics/SessionAnalyticsDashboard";
import AgentBuilderPage from "./features/agent-builder/AgentBuilderPage";
import "./features/agent-builder/AgentBuilderPage.css";
import { PackMarketplacePage } from "./features/pack-marketplace";
import "./features/pack-marketplace/PackMarketplacePage.css";
import { SpawnerPage } from "./features/spawner";
import { ToolCatalogPage } from "./features/tool-catalog";
import { ImpactDashboardPanel } from "./features/impact-dashboard";
import { OnboardingPanel } from "./features/onboarding/OnboardingPanel";
import { SafetyCenterPanel } from "./features/safety-center/SafetyCenterPanel";
import { SkillWizardPanel } from "./features/skill-wizard/SkillWizardPanel";
import { domains } from "./data/domains";
import { saveApiKey, saveToken, getSavedApiKey, getSavedToken } from "./lib/auth";
import { getRuntimeConfig } from "./lib/api";
import type { ApiResult } from "./types";

type AppTab =
  | "start"
  | "chat"
  | "voice"
  | "setup"
  | "review"
  | "safety"
  | "skills"
  | "operations"
  | "outcomes"
  | "analytics"
  | "impact"
  | "tools"
  | "marketplace"
  | "builder"
  | "spawner"
  | "advanced";

interface ActivityItem {
  id: string;
  at: string;
  label: string;
  status: number;
  durationMs: number;
  url: string;
}

const APP_TABS: ReadonlyArray<{ id: AppTab; label: string }> = [
  { id: "start", label: "Start Here" },
  { id: "chat", label: "💬 Chat Central" },
  { id: "voice", label: "🎙️ Voice Call" },
  { id: "setup", label: "🔌 Integrations" },
  { id: "review", label: "Review Queue" },
  { id: "safety", label: "Safety Center" },
  { id: "skills", label: "Skill Wizard" },
  { id: "operations", label: "Operations Hub" },
  { id: "outcomes", label: "Outcomes" },
  { id: "analytics", label: "Analytics" },
  { id: "impact", label: "Impact" },
  { id: "tools", label: "Tools" },
  { id: "marketplace", label: "Marketplace" },
  { id: "builder", label: "Builder" },
  { id: "spawner", label: "Spawner" },
  { id: "advanced", label: "⚙️ Advanced Settings" }
];

export default function App(): JSX.Element {
  const [activeTab, setActiveTab] = useState<AppTab>("start");

  // Legacy Domain Panel State (Maintained for Advanced Settings)
  const [selectedDomainId, setSelectedDomainId] = useState(domains[0]?.id ?? "overview");
  const [token, setTokenState] = useState(getSavedToken());
  const [apiKey, setApiKeyState] = useState(getSavedApiKey());
  const [activity, setActivity] = useState<ActivityItem[]>([]);

  const selectedDomain = useMemo(
    () => domains.find((domain) => domain.id === selectedDomainId) ?? domains[0],
    [selectedDomainId]
  );

  const { API_BASE_URL } = getRuntimeConfig();

  function setToken(tokenValue: string): void {
    setTokenState(tokenValue);
    saveToken(tokenValue);
  }

  function setApiKey(apiKeyValue: string): void {
    setApiKeyState(apiKeyValue);
    saveApiKey(apiKeyValue);
  }

  function onResult(label: string, result: ApiResult): void {
    const item: ActivityItem = {
      id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
      at: new Date().toLocaleTimeString(),
      label,
      status: result.status,
      durationMs: result.durationMs,
      url: result.url
    };
    setActivity((prev) => [item, ...prev].slice(0, 15));
  }

  return (
    <div className="consumer-app-shell">
      <SkipLink />
      {/* Clean Top Navigation */}
      <header className="consumer-topbar">
        <div className="brand">
          <div className="logo-orb" aria-hidden="true"></div>
          <h1>AGENT-33</h1>
        </div>
        <GlobalSearch token={token || null} />
        <nav className="main-nav" aria-label="Main navigation">
          {APP_TABS.map((tab) => (
            <button
              key={tab.id}
              className={activeTab === tab.id ? "active" : ""}
              onClick={() => setActiveTab(tab.id)}
              aria-current={activeTab === tab.id ? "page" : undefined}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </header>

      <div className="consumer-content" id="main-content" role="main">
        {activeTab === "start" && (
          <div className="consumer-onboarding-layout">
            <OnboardingPanel
              token={token}
              apiKey={apiKey}
              onOpenSetup={() => setActiveTab("setup")}
              onOpenChat={() => setActiveTab("chat")}
              onOpenOperations={() => setActiveTab("operations")}
              onResult={onResult}
            />
          </div>
        )}

        {/* Chat Central -> Render new ChatInterface */}
        {activeTab === "chat" && (
          <div className="consumer-chat-layout">
            <div
              style={{
                display: "grid",
                gap: "0.65rem",
                gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))"
              }}
            >
              <button
                onClick={() => setActiveTab("voice")}
                style={{
                  background: "rgba(11, 30, 39, 0.65)",
                  border: "1px solid rgba(48, 213, 200, 0.35)",
                  borderRadius: "10px",
                  color: "#d9edf4",
                  padding: "0.65rem 0.85rem",
                  fontSize: "0.86rem",
                  textAlign: "left",
                  cursor: "pointer"
                }}
              >
                🎙️ Start a voice session
              </button>
              <button
                onClick={() => setActiveTab("setup")}
                style={{
                  background: "rgba(11, 30, 39, 0.65)",
                  border: "1px solid rgba(48, 213, 200, 0.35)",
                  borderRadius: "10px",
                  color: "#d9edf4",
                  padding: "0.65rem 0.85rem",
                  fontSize: "0.86rem",
                  textAlign: "left",
                  cursor: "pointer"
                }}
              >
                🔌 Connect integrations
              </button>
              <button
                onClick={() => setActiveTab("advanced")}
                style={{
                  background: "rgba(11, 30, 39, 0.65)",
                  border: "1px solid rgba(48, 213, 200, 0.35)",
                  borderRadius: "10px",
                  color: "#d9edf4",
                  padding: "0.65rem 0.85rem",
                  fontSize: "0.86rem",
                  textAlign: "left",
                  cursor: "pointer"
                }}
              >
                ⚙️ Open control plane
              </button>
            </div>
            <ChatInterface token={token} apiKey={apiKey} />
          </div>
        )}

        {/* Voice Call -> Render LiveVoicePanel cleanly centered */}
        {activeTab === "voice" && (
          <div className="consumer-voice-layout">
            <LiveVoicePanel token={token || null} onOpenSetup={() => setActiveTab("setup")} />
          </div>
        )}

        {/* Integrations Setup -> Render new MessagingSetup component */}
        {activeTab === "setup" && (
          <div className="consumer-setup-layout">
            <MessagingSetup token={token} apiKey={apiKey} />
            <div className="auth-settings-card">
              <h3>Agent API Access</h3>
              <p>Configure internal tokens to securely access the AGENT-33 engine.</p>
              <AuthPanel
                token={token}
                apiKey={apiKey}
                onTokenChange={setToken}
                onApiKeyChange={setApiKey}
              />
            </div>
          </div>
        )}

        {/* Review Queue -> direct operator surface for candidate assets */}
        {activeTab === "review" && (
          <div className="consumer-review-layout">
            <IngestionReviewPanel token={token} apiKey={apiKey} onResult={onResult} />
          </div>
        )}

        {/* Safety Center -> direct HITL approval surface for governed tool calls */}
        {activeTab === "safety" && (
          <div className="consumer-safety-layout">
            <SafetyCenterPanel
              token={token}
              apiKey={apiKey}
              onOpenSetup={() => setActiveTab("setup")}
              onResult={onResult}
            />
          </div>
        )}

        {/* Skill Wizard -> plain-language skill authoring and installation */}
        {activeTab === "skills" && (
          <div className="consumer-skill-wizard-layout">
            <SkillWizardPanel
              token={token}
              apiKey={apiKey}
              onOpenSetup={() => setActiveTab("setup")}
              onResult={onResult}
            />
          </div>
        )}

        {/* Operations Hub -> Unified lifecycle view with pause/resume/cancel controls */}
        {activeTab === "operations" && (
          <div className="consumer-operations-layout">
            <OperationsHubPanel token={token} apiKey={apiKey} onResult={onResult} />
          </div>
        )}

        {/* Outcomes Dashboard -> Trend analysis, domain filtering, decline-triggered improvements */}
        {activeTab === "outcomes" && (
          <div className="consumer-outcomes-layout">
            <OutcomesDashboardPanel token={token} apiKey={apiKey} onResult={onResult} />
          </div>
        )}

        {/* Session Analytics -> Usage insights, model costs, daily activity */}
        {activeTab === "analytics" && (
          <div className="consumer-analytics-layout">
            <SessionAnalyticsDashboard token={token} apiKey={apiKey} onResult={onResult} />
          </div>
        )}

        {/* Impact Dashboard -> ROI, pack impact, week-over-week trends */}
        {activeTab === "impact" && (
          <div className="consumer-impact-layout">
            <ImpactDashboardPanel token={token} apiKey={apiKey} onResult={onResult} />
          </div>
        )}

        {/* Tool Catalog -> Runtime tool catalog with search, filters, schema */}
        {activeTab === "tools" && (
          <div className="consumer-tools-layout">
            <ToolCatalogPage token={token || null} apiKey={apiKey || null} />
          </div>
        )}

        {activeTab === "marketplace" && (
          <div className="consumer-marketplace-layout">
            <PackMarketplacePage token={token || null} apiKey={apiKey || null} />
          </div>
        )}

        {/* Agent Builder -> Visual agent creation with capability toggles and preview */}
        {activeTab === "builder" && (
          <div className="consumer-builder-layout">
            <AgentBuilderPage token={token} apiKey={apiKey} />
          </div>
        )}

        {/* Sub-Agent Spawner -> Visual workflow builder for parent-child delegation */}
        {activeTab === "spawner" && (
          <div className="consumer-spawner-layout">
            <SpawnerPage token={token} apiKey={apiKey} />
          </div>
        )}

        {/* Advanced Settings -> The original complex "Control Plane" Grid layout */}
        {activeTab === "advanced" && (
          <div className="legacy-control-plane app-shell">
            <div className="content">
              <aside className="sidebar" aria-label="Sidebar">
                <HealthPanel />
                <nav className="domain-nav" aria-label="Technical domains">
                  <h2>Technical Domains</h2>
                  {domains.map((domain) => (
                    <button
                      key={domain.id}
                      className={domain.id === selectedDomainId ? "active" : ""}
                      onClick={() => setSelectedDomainId(domain.id)}
                      aria-current={domain.id === selectedDomainId ? "true" : undefined}
                    >
                      {domain.title}
                    </button>
                  ))}
                </nav>
              </aside>

              <main className="workspace">
                <DomainPanel domain={selectedDomain} token={token} apiKey={apiKey} onResult={onResult} />
              </main>

              <aside className="activity-panel" aria-label="Activity log">
                <ObservationStream token={token} />
                <h2>System Calls</h2>
                {activity.length === 0 ? <p>No calls yet.</p> : null}
                <div className="activity-list">
                  {activity.map((item) => (
                    <article key={item.id} className="activity-item">
                      <p className="activity-time">{item.at}</p>
                      <h3>{item.label}</h3>
                      <p>
                        <span className={item.status < 400 ? "status-ok" : "status-error"}>
                          <span className="sr-only">{item.status < 400 ? "Success" : "Error"}:</span>
                          {item.status}
                        </span>
                        {" in "}
                        {item.durationMs}ms
                      </p>
                      <p className="activity-url">{item.url}</p>
                    </article>
                  ))}
                </div>
              </aside>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
