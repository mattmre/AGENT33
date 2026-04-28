import { useCallback, useState } from "react";

import { AuthPanel } from "./components/AuthPanel";
import { AppNavigation } from "./components/AppNavigation";
import { GlobalSearch } from "./components/GlobalSearch";
import { SkipLink } from "./components/SkipLink";
import { LiveVoicePanel } from "./features/voice/LiveVoicePanel";
import { MessagingSetup } from "./features/integrations/MessagingSetup";
import { ModelConnectionWizardPanel } from "./features/model-connection/ModelConnectionWizardPanel";
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
import { SafetyCenterPanel } from "./features/safety-center/SafetyCenterPanel";
import { SkillWizardPanel } from "./features/skill-wizard/SkillWizardPanel";
import { ToolFabricPanel } from "./features/tool-fabric/ToolFabricPanel";
import { WorkflowStarterPanel } from "./features/workflow-starter/WorkflowStarterPanel";
import { WorkflowCatalogPanel } from "./features/workflow-catalog/WorkflowCatalogPanel";
import { ImprovementLoopsPanel } from "./features/improvement-loops/ImprovementLoopsPanel";
import { McpHealthPanel } from "./features/mcp-health/McpHealthPanel";
import { OutcomeHomePanel } from "./features/outcome-home/OutcomeHomePanel";
import { DemoModePanel } from "./features/demo-mode/DemoModePanel";
import { RoleIntakePanel } from "./features/role-intake/RoleIntakePanel";
import { UnifiedConnectCenterPanel } from "./features/connect-center/UnifiedConnectCenterPanel";
import { isUserRoleId } from "./features/role-intake/data";
import { HelpAssistantDrawer } from "./features/help-assistant/HelpAssistantDrawer";
import {
  AdvancedControlPlanePanel,
  type OperatorMode
} from "./features/advanced/AdvancedControlPlanePanel";
import { domains } from "./data/domains";
import {
  DEFAULT_APP_TAB,
  ROLE_SELECTED_DEFAULT_APP_TAB,
  getAppTabLabel,
  type AppTab
} from "./data/navigation";
import { saveApiKey, saveToken, getSavedApiKey, getSavedToken } from "./lib/auth";
import type { ActivityItem, ApiResult } from "./types";
import type { HelpAssistantTarget } from "./features/help-assistant/types";
import type { WorkflowStarterDraft } from "./features/workflow-starter/types";
import type { UserRoleId } from "./features/role-intake/types";

const ROLE_STORAGE_KEY = "agent33:selected-role";

function getSavedUserRole(): UserRoleId | null {
  if (typeof window === "undefined") {
    return null;
  }

  const savedRole = window.sessionStorage.getItem(ROLE_STORAGE_KEY);
  return isUserRoleId(savedRole) ? savedRole : null;
}

export default function App(): JSX.Element {
  const [activeTab, setActiveTab] = useState<AppTab>(() =>
    getSavedUserRole() ? ROLE_SELECTED_DEFAULT_APP_TAB : DEFAULT_APP_TAB
  );

  // Legacy Domain Panel State (Maintained for Advanced Settings)
  const [selectedDomainId, setSelectedDomainId] = useState(domains[0]?.id ?? "overview");
  const [operatorMode, setOperatorMode] = useState<OperatorMode>("beginner");
  const [token, setTokenState] = useState(getSavedToken());
  const [apiKey, setApiKeyState] = useState(getSavedApiKey());
  const [activity, setActivity] = useState<ActivityItem[]>([]);
  const [workflowStarterDraft, setWorkflowStarterDraft] = useState<WorkflowStarterDraft | null>(null);
  const [selectedRole, setSelectedRole] = useState<UserRoleId | null>(getSavedUserRole);

  function setToken(tokenValue: string): void {
    setTokenState(tokenValue);
    saveToken(tokenValue);
  }

  function setApiKey(apiKeyValue: string): void {
    setApiKeyState(apiKeyValue);
    saveApiKey(apiKeyValue);
  }

  const onResult = useCallback((label: string, result: ApiResult): void => {
    const item: ActivityItem = {
      id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
      at: new Date().toLocaleTimeString(),
      label,
      status: result.status,
      durationMs: result.durationMs,
      url: result.url
    };
    setActivity((prev) => [item, ...prev].slice(0, 15));
  }, []);

  const openWorkflowStarter = useCallback((draft?: WorkflowStarterDraft): void => {
    setWorkflowStarterDraft(draft ?? null);
    setActiveTab("starter");
  }, []);

  const chooseRole = useCallback((roleId: UserRoleId): void => {
    setSelectedRole(roleId);
    if (typeof window !== "undefined") {
      window.sessionStorage.setItem(ROLE_STORAGE_KEY, roleId);
    }
  }, []);

  const openHelpTarget = useCallback((target: HelpAssistantTarget): void => {
    setActiveTab(target);
  }, []);

  return (
    <div className="consumer-app-shell">
      <SkipLink />
      <header className="consumer-topbar">
        <div className="brand">
          <div className="logo-orb" aria-hidden="true"></div>
          <h1>AGENT-33</h1>
        </div>
        <div className="cockpit-topbar-actions">
          <GlobalSearch token={token || null} />
          <div className="operator-mode-switch" role="group" aria-label="Operator mode">
            <span>Mode</span>
            <button
              type="button"
              className={operatorMode === "beginner" ? "active" : ""}
              onClick={() => setOperatorMode("beginner")}
              aria-pressed={operatorMode === "beginner"}
            >
              Beginner
            </button>
            <button
              type="button"
              className={operatorMode === "pro" ? "active" : ""}
              onClick={() => setOperatorMode("pro")}
              aria-pressed={operatorMode === "pro"}
            >
              Pro
            </button>
          </div>
        </div>
      </header>

      <div className="cockpit-layout">
        <aside className="cockpit-sidebar">
          <div className="cockpit-sidebar-context">
            <span className="eyebrow">Workspace</span>
            <strong>Local Shipyard</strong>
            <small>Sidebar foundation for BridgeSpace-style project control.</small>
          </div>
          <AppNavigation activeTab={activeTab} onNavigate={setActiveTab} />
        </aside>

        <main className="cockpit-main" id="main-content">
          <div className="cockpit-context-bar" aria-label="Current workspace context">
            <div>
              <span className="eyebrow">Now viewing</span>
              <strong>{getAppTabLabel(activeTab)}</strong>
            </div>
            <span>Workspace, task board, agent roster, and artifact lanes land in the next Wave 4 slices.</span>
          </div>

          <div className="consumer-content">
        {activeTab === "guide" && (
          <div className="consumer-role-intake-layout">
            <RoleIntakePanel
              selectedRole={selectedRole}
              onSelectRole={chooseRole}
              onOpenDemo={() => setActiveTab("demo")}
              onOpenModels={() => setActiveTab("models")}
              onOpenWorkflowCatalog={() => setActiveTab("catalog")}
              onOpenWorkflowStarter={openWorkflowStarter}
            />
          </div>
        )}

        {activeTab === "start" && (
          <div className="consumer-onboarding-layout">
            <OutcomeHomePanel
              selectedRole={selectedRole}
              token={token}
              apiKey={apiKey}
              onOpenSetup={() => setActiveTab("setup")}
              onOpenModels={() => setActiveTab("models")}
              onOpenDemo={() => setActiveTab("demo")}
              onOpenChat={() => setActiveTab("chat")}
              onOpenOperations={() => setActiveTab("operations")}
              onOpenWorkflowStarter={openWorkflowStarter}
              onOpenLoops={() => setActiveTab("loops")}
              onOpenMcp={() => setActiveTab("mcp")}
              onOpenAdvanced={() => setActiveTab("advanced")}
              onResult={onResult}
            />
          </div>
        )}

        {activeTab === "connect" && (
          <div className="consumer-connect-center-layout">
            <UnifiedConnectCenterPanel
              token={token}
              apiKey={apiKey}
              onNavigate={setActiveTab}
              onResult={onResult}
            />
          </div>
        )}

        {activeTab === "demo" && (
          <div className="consumer-demo-mode-layout">
            <DemoModePanel
              selectedRole={selectedRole}
              onOpenModels={() => setActiveTab("models")}
              onOpenWorkflowCatalog={() => setActiveTab("catalog")}
              onOpenWorkflowStarter={openWorkflowStarter}
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

        {/* Model Connection -> plain-language provider setup and probe flow */}
        {activeTab === "models" && (
          <div className="consumer-model-wizard-layout">
            <ModelConnectionWizardPanel
              token={token}
              apiKey={apiKey}
              onOpenSetup={() => setActiveTab("setup")}
              onOpenWorkflowCatalog={() => setActiveTab("catalog")}
              onResult={onResult}
            />
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

        {/* Tool Fabric -> adaptive tool/skill/workflow discovery */}
        {activeTab === "fabric" && (
          <div className="consumer-tool-fabric-layout">
            <ToolFabricPanel
              token={token}
              apiKey={apiKey}
              onOpenSetup={() => setActiveTab("setup")}
              onOpenTools={() => setActiveTab("tools")}
              onOpenSkills={() => setActiveTab("skills")}
              onOpenWorkflowStarter={() => openWorkflowStarter()}
              onResult={onResult}
            />
          </div>
        )}

        {/* MCP Health -> server/tool/sync readiness for external tool fabric */}
        {activeTab === "mcp" && (
          <div className="consumer-mcp-health-layout">
            <McpHealthPanel
              token={token}
              apiKey={apiKey}
              onOpenSetup={() => setActiveTab("setup")}
              onOpenToolFabric={() => setActiveTab("fabric")}
              onOpenTools={() => setActiveTab("tools")}
              onResult={onResult}
            />
          </div>
        )}

        {/* Workflow Catalog -> curated outcome systems with safe starter routing */}
        {activeTab === "catalog" && (
          <div className="consumer-workflow-catalog-layout">
            <WorkflowCatalogPanel
              onOpenWorkflowStarter={openWorkflowStarter}
              onOpenSetup={() => setActiveTab("setup")}
              onOpenOperations={() => setActiveTab("operations")}
            />
          </div>
        )}

        {/* Workflow Starter -> guided research and loop workflow creation */}
        {activeTab === "starter" && (
          <div className="consumer-workflow-starter-layout">
            <WorkflowStarterPanel
              token={token}
              apiKey={apiKey}
              onOpenSetup={() => setActiveTab("setup")}
              onOpenSpawner={() => setActiveTab("spawner")}
              onOpenOperations={() => setActiveTab("operations")}
              initialDraft={workflowStarterDraft}
              onResult={onResult}
            />
          </div>
        )}

        {/* Improvement Loops -> recurring research and improvement workflows */}
        {activeTab === "loops" && (
          <div className="consumer-improvement-loops-layout">
            <ImprovementLoopsPanel
              token={token}
              apiKey={apiKey}
              onOpenSetup={() => setActiveTab("setup")}
              onOpenOperations={() => setActiveTab("operations")}
              onOpenWorkflowStarter={() => openWorkflowStarter()}
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

        {/* Advanced Settings -> quarantined raw control plane */}
        {activeTab === "advanced" && (
          <AdvancedControlPlanePanel
            domains={domains}
            selectedDomainId={selectedDomainId}
            token={token}
            apiKey={apiKey}
            activity={activity}
            operatorMode={operatorMode}
            onOperatorModeChange={setOperatorMode}
            onSelectedDomainChange={setSelectedDomainId}
            onOpenModels={() => setActiveTab("models")}
            onOpenWorkflowCatalog={() => setActiveTab("catalog")}
            onOpenOperations={() => setActiveTab("operations")}
            onOpenSafety={() => setActiveTab("safety")}
            onOpenSetup={() => setActiveTab("setup")}
            onResult={onResult}
          />
        )}
          </div>
        </main>
      </div>
      <HelpAssistantDrawer onNavigate={openHelpTarget} />
    </div>
  );
}
