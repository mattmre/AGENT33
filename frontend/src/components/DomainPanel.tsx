import { useMemo, useState } from "react";

import type { ApiResult, DomainConfig } from "../types";
import { OperationCard } from "./OperationCard";
import { ProcessList } from "../features/operations-hub/ProcessList";
import { ControlPanel } from "../features/operations-hub/ControlPanel";
import { Dashboard } from "../features/outcomes/Dashboard";
import { EvolutionDashboard } from "../features/self-evolution/Dashboard";
import { ResearchDashboard } from "../features/research/Dashboard";
import { SessionsDashboard } from "../features/sessions/Dashboard";
import { ModulesDashboard } from "../features/modules/Dashboard";
import { TasksDashboard } from "../features/tasks/Dashboard";
import { SecurityDashboard } from "../features/security-dashboard/SecurityDashboard";

interface DomainPanelProps {
  domain: DomainConfig;
  token: string;
  apiKey: string;
  onResult: (label: string, result: ApiResult) => void;
}

export function DomainPanel({
  domain,
  token,
  apiKey,
  onResult
}: DomainPanelProps): JSX.Element {
  const [filter, setFilter] = useState("");
  const operations = useMemo(() => {
    const q = filter.trim().toLowerCase();
    if (q === "") {
      return domain.operations;
    }
    return domain.operations.filter((op) => {
      return (
        op.title.toLowerCase().includes(q) ||
        op.path.toLowerCase().includes(q) ||
        op.description.toLowerCase().includes(q)
      );
    });
  }, [domain.operations, filter]);

  return (
    <section className="domain-panel">
      <header className="domain-head">
        <div>
          <h2>{domain.title}</h2>
          <p>{domain.description}</p>
        </div>
        <label className="search-field">
          Search
          <input
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            placeholder="Filter operations"
          />
        </label>
      </header>

      {domain.id === "operations" && (
        <div className="custom-feature-panel">
          <ProcessList token={token} />
          <ControlPanel token={token} processId="" />
        </div>
      )}

      {domain.id === "dashboard" && (
        <div className="custom-feature-panel">
          <Dashboard token={token} />
        </div>
      )}

      {domain.id === "outcomes" && (
        <div className="custom-feature-panel">
          <Dashboard token={token} />
        </div>
      )}

      {domain.id === "self-evolution" && (
        <div className="custom-feature-panel">
          <EvolutionDashboard token={token} />
        </div>
      )}

      {domain.id === "research" && (
        <div className="custom-feature-panel">
          <ResearchDashboard token={token} />
        </div>
      )}

      {domain.id === "sessions" && (
        <div className="custom-feature-panel">
          <SessionsDashboard token={token} />
        </div>
      )}

      {domain.id === "modules" && (
        <div className="custom-feature-panel">
          <ModulesDashboard token={token} />
        </div>
      )}

      {domain.id === "tasks" && (
        <div className="custom-feature-panel">
          <TasksDashboard token={token} />
        </div>
      )}

      {domain.id === "component-security" && (
        <div className="custom-feature-panel">
          <SecurityDashboard token={token} />
        </div>
      )}

      <div className="domain-ops">
        {operations.map((operation) => (
          <OperationCard
            key={operation.id}
            operation={operation}
            token={token}
            apiKey={apiKey}
            onResult={onResult}
          />
        ))}
      </div>
    </section>
  );
}
