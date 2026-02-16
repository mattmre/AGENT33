import { useMemo, useState } from "react";

import { AuthPanel } from "./components/AuthPanel";
import { DomainPanel } from "./components/DomainPanel";
import { HealthPanel } from "./components/HealthPanel";
import { domains } from "./data/domains";
import { saveApiKey, saveToken, getSavedApiKey, getSavedToken } from "./lib/auth";
import { getRuntimeConfig } from "./lib/api";
import type { ApiResult } from "./types";

interface ActivityItem {
  id: string;
  at: string;
  label: string;
  status: number;
  durationMs: number;
  url: string;
}

export default function App(): JSX.Element {
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
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">AGENT-33</p>
          <h1>Control Plane</h1>
        </div>
        <div className="top-meta">
          <span>API: {API_BASE_URL}</span>
          <span>{token ? "Token loaded" : "No token"}</span>
        </div>
      </header>

      <div className="content">
        <aside className="sidebar">
          <AuthPanel
            token={token}
            apiKey={apiKey}
            onTokenChange={setToken}
            onApiKeyChange={setApiKey}
          />
          <HealthPanel />
          <nav className="domain-nav">
            <h2>Domains</h2>
            {domains.map((domain) => (
              <button
                key={domain.id}
                className={domain.id === selectedDomainId ? "active" : ""}
                onClick={() => setSelectedDomainId(domain.id)}
              >
                {domain.title}
              </button>
            ))}
          </nav>
        </aside>

        <main className="workspace">
          <DomainPanel domain={selectedDomain} token={token} apiKey={apiKey} onResult={onResult} />
        </main>

        <aside className="activity-panel">
          <h2>Recent Calls</h2>
          {activity.length === 0 ? <p>No calls yet.</p> : null}
          <div className="activity-list">
            {activity.map((item) => (
              <article key={item.id} className="activity-item">
                <p className="activity-time">{item.at}</p>
                <h3>{item.label}</h3>
                <p>
                  <span className={item.status < 400 ? "status-ok" : "status-error"}>
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
