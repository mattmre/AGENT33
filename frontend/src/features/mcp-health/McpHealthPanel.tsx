import { useEffect, useMemo, useState } from "react";

import type { ApiResult } from "../../types";
import { fetchMcpHealthSnapshot } from "./api";
import type { EndpointState, McpHealthSnapshot } from "./types";

interface McpHealthPanelProps {
  token: string;
  apiKey: string;
  onOpenSetup: () => void;
  onOpenToolFabric: () => void;
  onOpenTools: () => void;
  onResult: (label: string, result: ApiResult) => void;
}

function endpointLabel<T>(endpoint: EndpointState<T>): string {
  if (endpoint.ok) {
    return "Ready";
  }
  if (endpoint.status === 503 || endpoint.status === 404) {
    return "Not configured";
  }
  return "Needs attention";
}

export function McpHealthPanel({
  token,
  apiKey,
  onOpenSetup,
  onOpenToolFabric,
  onOpenTools,
  onResult
}: McpHealthPanelProps): JSX.Element {
  const [snapshot, setSnapshot] = useState<McpHealthSnapshot | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const hasCredentials = token.trim() !== "" || apiKey.trim() !== "";
  const bridgeStatus = snapshot?.status.data;
  const proxyFleet = snapshot?.proxyServers.data;
  const proxyTools = snapshot?.proxyTools.data;
  const syncEntries = snapshot?.syncDiff.data?.entries ?? [];

  const healthLabel = useMemo(() => {
    if (bridgeStatus?.available) {
      return "MCP bridge online";
    }
    if (bridgeStatus?.mcp_sdk_installed || bridgeStatus?.transport_available) {
      return "MCP partially configured";
    }
    return "MCP needs setup";
  }, [bridgeStatus]);

  async function refresh(): Promise<void> {
    if (!hasCredentials) {
      return;
    }
    setLoading(true);
    setError("");
    try {
      const loaded = await fetchMcpHealthSnapshot(token, apiKey);
      loaded.results.forEach(([label, result]) => onResult(label, result));
      setSnapshot(loaded.snapshot);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown MCP health error";
      setError(message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasCredentials, token, apiKey]);

  if (!hasCredentials) {
    return (
      <section className="mcp-health-panel">
        <div className="onboarding-callout onboarding-callout-error">
          <h3>Connect to the engine first</h3>
          <p>Add an API key or operator token before checking MCP servers and tools.</p>
          <button onClick={onOpenSetup}>Open integrations and API access</button>
        </div>
      </section>
    );
  }

  return (
    <section className="mcp-health-panel">
      <header className="mcp-health-hero">
        <div>
          <h2>MCP Health Center</h2>
          <p>
            See whether AGENT-33 MCP transport, proxy servers, tool discovery, and CLI sync are ready
            before routing work through the Tool Fabric.
          </p>
        </div>
        <div className="mcp-health-badge">{loading ? "Refreshing..." : healthLabel}</div>
      </header>

      <div className="mcp-health-actions">
        <button type="button" onClick={() => void refresh()} disabled={loading}>
          {loading ? "Refreshing..." : "Refresh health"}
        </button>
        <button type="button" onClick={onOpenToolFabric}>Open Tool Fabric</button>
        <button type="button" onClick={onOpenTools}>Browse tool catalog</button>
      </div>

      {error ? <p className="ops-hub-error" role="alert">{error}</p> : null}

      <div className="mcp-health-grid">
        <article className="mcp-health-card mcp-health-summary">
          <h3>Bridge status</h3>
          {snapshot === null ? (
            <p>Loading MCP status...</p>
          ) : (
            <>
              <strong>{endpointLabel(snapshot.status)}</strong>
              {snapshot.status.error ? <p>{snapshot.status.error}</p> : null}
              <div className="mcp-health-metrics">
                <span>SDK {bridgeStatus?.mcp_sdk_installed ? "installed" : "missing"}</span>
                <span>Transport {bridgeStatus?.transport_available ? "ready" : "unavailable"}</span>
                <span>{bridgeStatus?.tools_loaded ?? 0} native tools</span>
                <span>{bridgeStatus?.proxy_servers_loaded ?? 0} proxy servers</span>
              </div>
            </>
          )}
        </article>

        <article className="mcp-health-card">
          <h3>Proxy fleet</h3>
          {snapshot?.proxyServers.ok ? (
            <div className="mcp-health-metrics">
              <span>{proxyFleet?.healthy ?? 0} healthy</span>
              <span>{proxyFleet?.degraded ?? 0} degraded</span>
              <span>{proxyFleet?.unhealthy ?? 0} unhealthy</span>
              <span>{proxyFleet?.stopped ?? 0} stopped</span>
            </div>
          ) : (
            <p>{snapshot?.proxyServers.error ?? "Loading proxy fleet..."}</p>
          )}
        </article>

        <article className="mcp-health-card">
          <h3>Aggregated tools</h3>
          {snapshot?.proxyTools.ok ? (
            <p>{proxyTools?.count ?? 0} MCP proxy tools are available to AGENT-33.</p>
          ) : (
            <p>{snapshot?.proxyTools.error ?? "Loading proxy tools..."}</p>
          )}
        </article>

        <article className="mcp-health-card">
          <h3>CLI sync</h3>
          {snapshot?.syncDiff.ok ? (
            <p>
              {syncEntries.filter((entry) => entry.matches).length} of {syncEntries.length} CLI targets match AGENT-33.
            </p>
          ) : (
            <p>{snapshot?.syncDiff.error ?? "Loading sync status..."}</p>
          )}
        </article>
      </div>

      <div className="mcp-health-detail-grid">
        <section className="mcp-health-card">
          <h3>Proxy servers</h3>
          {(proxyFleet?.servers ?? []).length === 0 ? <p>No MCP proxy servers are registered yet.</p> : null}
          {(proxyFleet?.servers ?? []).map((server) => (
            <article key={server.id} className="mcp-health-row">
              <div>
                <strong>{server.name}</strong>
                <span>{server.id} · {server.transport}</span>
              </div>
              <div>
                <span className={`mcp-state mcp-state-${server.state}`}>{server.state}</span>
                <small>{server.tool_count} tools · circuit {server.circuit_state}</small>
              </div>
              {server.last_error ? <p>{server.last_error}</p> : null}
            </article>
          ))}
        </section>

        <section className="mcp-health-card">
          <h3>Recent proxy tools</h3>
          {(proxyTools?.tools ?? []).length === 0 ? <p>No aggregated MCP tools are currently exposed.</p> : null}
          {(proxyTools?.tools ?? []).slice(0, 8).map((tool) => (
            <article key={`${tool.proxy_server_id}-${tool.name}`} className="mcp-health-row">
              <div>
                <strong>{tool.name}</strong>
                <span>{tool.proxy_server_id} · {tool.original_name}</span>
              </div>
              <p>{tool.description || "No description provided."}</p>
            </article>
          ))}
        </section>

        <section className="mcp-health-card">
          <h3>CLI registration drift</h3>
          {syncEntries.length === 0 ? <p>No CLI sync targets reported yet.</p> : null}
          {syncEntries.map((entry) => (
            <article key={entry.target} className="mcp-health-row">
              <div>
                <strong>{entry.target}</strong>
                <span>{entry.config_path || "No config path"}</span>
              </div>
              <div>
                <span className={entry.matches ? "mcp-state mcp-state-healthy" : "mcp-state mcp-state-degraded"}>
                  {entry.matches ? "synced" : entry.present ? "drift" : "missing"}
                </span>
                {entry.error ? <small>{entry.error}</small> : null}
              </div>
            </article>
          ))}
        </section>
      </div>
    </section>
  );
}
