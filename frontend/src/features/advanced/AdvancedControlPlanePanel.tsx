import { useMemo, useState } from "react";

import { DomainPanel } from "../../components/DomainPanel";
import { HealthPanel } from "../../components/HealthPanel";
import { ObservationStream } from "../../components/ObservationStream";
import type { ActivityItem, ApiResult, DomainConfig } from "../../types";

export type OperatorMode = "beginner" | "pro";

interface AdvancedControlPlanePanelProps {
  domains: DomainConfig[];
  selectedDomainId: string;
  token: string;
  apiKey: string;
  activity: ActivityItem[];
  operatorMode: OperatorMode;
  onOperatorModeChange: (mode: OperatorMode) => void;
  onSelectedDomainChange: (domainId: string) => void;
  onOpenModels: () => void;
  onOpenWorkflowCatalog: () => void;
  onOpenOperations: () => void;
  onOpenSafety: () => void;
  onOpenSetup: () => void;
  onResult: (label: string, result: ApiResult) => void;
}

const SAFE_ROUTES = [
  {
    title: "Connect a model",
    description: "Use the guided provider setup instead of editing auth/config endpoints.",
    actionLabel: "Open Models",
    action: "models"
  },
  {
    title: "Launch a baked-in workflow",
    description: "Start with curated systems instead of raw workflow JSON payloads.",
    actionLabel: "Open Workflow Catalog",
    action: "catalog"
  },
  {
    title: "Watch active work",
    description: "Use the timeline and safe controls before touching process endpoints.",
    actionLabel: "Open Run Timeline",
    action: "operations"
  },
  {
    title: "Approve risky actions",
    description: "Review governed tool calls in the Safety Center before using direct API calls.",
    actionLabel: "Open Safety Center",
    action: "safety"
  }
] as const;

function domainMatchesQuery(domain: DomainConfig, query: string): boolean {
  const normalized = query.trim().toLowerCase();
  if (normalized === "") {
    return true;
  }
  return (
    domain.title.toLowerCase().includes(normalized) ||
    domain.description.toLowerCase().includes(normalized) ||
    domain.operations.some((operation) => {
      return (
        operation.title.toLowerCase().includes(normalized) ||
        operation.description.toLowerCase().includes(normalized) ||
        operation.path.toLowerCase().includes(normalized)
      );
    })
  );
}

export function AdvancedControlPlanePanel({
  domains,
  selectedDomainId,
  token,
  apiKey,
  activity,
  operatorMode,
  onOperatorModeChange,
  onSelectedDomainChange,
  onOpenModels,
  onOpenWorkflowCatalog,
  onOpenOperations,
  onOpenSafety,
  onOpenSetup,
  onResult
}: AdvancedControlPlanePanelProps): JSX.Element {
  const [advancedSearch, setAdvancedSearch] = useState("");
  const selectedDomain = useMemo(
    () => domains.find((domain) => domain.id === selectedDomainId) ?? domains[0],
    [domains, selectedDomainId]
  );
  const matchedDomains = useMemo(
    () => domains.filter((domain) => domainMatchesQuery(domain, advancedSearch)),
    [advancedSearch, domains]
  );

  if (selectedDomain === undefined) {
    return <p className="advanced-quarantine-empty">No technical domains are registered.</p>;
  }

  function openSafeRoute(action: (typeof SAFE_ROUTES)[number]["action"]): void {
    if (action === "models") {
      onOpenModels();
    } else if (action === "catalog") {
      onOpenWorkflowCatalog();
    } else if (action === "operations") {
      onOpenOperations();
    } else if (action === "safety") {
      onOpenSafety();
    }
  }

  if (operatorMode !== "pro") {
    return (
      <section className="advanced-quarantine-panel">
        <div className="advanced-quarantine-hero">
          <div>
            <p className="advanced-quarantine-eyebrow">Beginner mode</p>
            <h2>Advanced controls are quarantined by default.</h2>
            <p>
              This area exposes raw endpoints, JSON payloads, and destructive operations. Use the
              guided screens below unless you intentionally need the low-level control plane.
            </p>
          </div>
          <button type="button" className="control-danger" onClick={() => onOperatorModeChange("pro")}>
            Unlock Pro control plane
          </button>
        </div>

        <div className="advanced-safe-route-grid">
          {SAFE_ROUTES.map((route) => (
            <article key={route.action} className="advanced-safe-route-card">
              <h3>{route.title}</h3>
              <p>{route.description}</p>
              <button type="button" onClick={() => openSafeRoute(route.action)}>
                {route.actionLabel}
              </button>
            </article>
          ))}
        </div>

        <div className="advanced-quarantine-search">
          <label>
            Find a technical domain before unlocking Pro mode
            <input
              value={advancedSearch}
              onChange={(event) => setAdvancedSearch(event.target.value)}
              placeholder="Search endpoints, workflows, memory, auth..."
            />
          </label>
          <button type="button" onClick={onOpenSetup}>
            Configure access instead
          </button>
        </div>

        <div className="advanced-domain-preview-grid">
          {matchedDomains.map((domain) => (
            <article key={domain.id} className="advanced-domain-preview-card">
              <div>
                <h3>{domain.title}</h3>
                <p>{domain.description}</p>
                <span>{domain.operations.length} raw operations hidden</span>
              </div>
              <button
                type="button"
                onClick={() => {
                  onSelectedDomainChange(domain.id);
                  onOperatorModeChange("pro");
                }}
              >
                Inspect in Pro mode
              </button>
            </article>
          ))}
          {matchedDomains.length === 0 ? (
            <p className="advanced-quarantine-empty">No matching technical domains.</p>
          ) : null}
        </div>
      </section>
    );
  }

  return (
    <div className="legacy-control-plane app-shell advanced-pro-shell">
      <div className="advanced-pro-banner">
        <div>
          <p className="advanced-quarantine-eyebrow">Pro mode unlocked</p>
          <h2>Raw control plane</h2>
          <p>
            You are viewing low-level endpoints. Prefer guided screens for routine work and review
            payloads before running POST, PATCH, PUT, or DELETE calls.
          </p>
        </div>
        <div className="advanced-pro-actions">
          <label>
            Search all technical domains
            <input
              value={advancedSearch}
              onChange={(event) => setAdvancedSearch(event.target.value)}
              placeholder="Filter domains and operation cards"
            />
          </label>
          <button type="button" onClick={() => onOperatorModeChange("beginner")}>
            Return to Beginner mode
          </button>
        </div>
      </div>

      <div className="content">
        <aside className="sidebar" aria-label="Sidebar">
          <HealthPanel />
          <nav className="domain-nav" aria-label="Technical domains">
            <h2>Technical Domains</h2>
            {matchedDomains.map((domain) => (
              <button
                key={domain.id}
                className={domain.id === selectedDomainId ? "active" : ""}
                onClick={() => onSelectedDomainChange(domain.id)}
                aria-current={domain.id === selectedDomainId ? "true" : undefined}
              >
                {domain.title}
              </button>
            ))}
            {matchedDomains.length === 0 ? <p>No domains match this search.</p> : null}
          </nav>
        </aside>

        <main className="workspace">
          <DomainPanel
            domain={selectedDomain}
            token={token}
            apiKey={apiKey}
            externalFilter={advancedSearch}
            onResult={onResult}
          />
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
  );
}
