import { useMemo, useState } from "react";

import type { ApiResult, DomainConfig } from "../types";
import { OperationCard } from "./OperationCard";
import { SecurityDashboard } from "../features/security-dashboard/SecurityDashboard";
import { OperationsHub } from "../features/operations-hub/OperationsHub";

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
          <OperationsHub token={token} />
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
