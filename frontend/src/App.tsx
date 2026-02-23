import { useMemo, useState } from "react";

import { AuthPanel } from "./components/AuthPanel";
import { DomainPanel } from "./components/DomainPanel";
import { HealthPanel } from "./components/HealthPanel";
import { GlobalSearch } from "./components/GlobalSearch";
import { LiveVoicePanel } from "./features/voice/LiveVoicePanel";
import { ObservationStream } from "./components/ObservationStream";
import { MessagingSetup } from "./features/integrations/MessagingSetup";
import { ChatInterface } from "./features/chat/ChatInterface";
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
  const [activeTab, setActiveTab] = useState<"chat" | "voice" | "setup" | "advanced">("chat");

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
      {/* Clean Top Navigation */}
      <header className="consumer-topbar">
        <div className="brand">
          <div className="logo-orb"></div>
          <h1>AGENT-33</h1>
        </div>
        <nav className="main-nav">
          <button className={activeTab === "chat" ? "active" : ""} onClick={() => setActiveTab("chat")}>💬 Chat Central</button>
          <button className={activeTab === "voice" ? "active" : ""} onClick={() => setActiveTab("voice")}>🎙️ Voice Call</button>
          <button className={activeTab === "setup" ? "active" : ""} onClick={() => setActiveTab("setup")}>🔌 Integrations</button>
          <button className={activeTab === "advanced" ? "active" : ""} onClick={() => setActiveTab("advanced")}>⚙️ Advanced Settings</button>
        </nav>
      </header>

      <div className="consumer-content">
        {/* Chat Central -> Render new ChatInterface */}
        {activeTab === "chat" && (
          <div className="consumer-chat-layout">
            <ChatInterface token={token} apiKey={apiKey} />
          </div>
        )}

        {/* Voice Call -> Render LiveVoicePanel cleanly centered */}
        {activeTab === "voice" && (
          <div className="consumer-voice-layout">
            <LiveVoicePanel token={token} />
          </div>
        )}

        {/* Integrations Setup -> Render new MessagingSetup component */}
        {activeTab === "setup" && (
          <div className="consumer-setup-layout">
            <MessagingSetup />
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

        {/* Advanced Settings -> The original complex "Control Plane" Grid layout */}
        {activeTab === "advanced" && (
          <div className="legacy-control-plane app-shell">
            <div className="content">
              <aside className="sidebar">
                <HealthPanel />
                <nav className="domain-nav">
                  <h2>Technical Domains</h2>
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
