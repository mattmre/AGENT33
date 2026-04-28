import { useCallback, useEffect, useMemo, useState } from "react";

import type { ApiResult } from "../../types";
import { asOnboardingStatus, fetchOnboardingStatus } from "../onboarding/api";
import type { OnboardingStatus } from "../onboarding/types";
import { buildConnectCards, getConnectScore } from "./helpers";
import type { ConnectTarget } from "./types";

interface UnifiedConnectCenterPanelProps {
  token: string;
  apiKey: string;
  onNavigate: (target: ConnectTarget) => void;
  onResult: (label: string, result: ApiResult) => void;
}

function statusLabel(status: string): string {
  if (status === "ready") {
    return "Ready";
  }
  if (status === "attention") {
    return "Needs attention";
  }
  return "Unknown";
}

export function UnifiedConnectCenterPanel({
  token,
  apiKey,
  onNavigate,
  onResult
}: UnifiedConnectCenterPanelProps): JSX.Element {
  const [status, setStatus] = useState<OnboardingStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const hasCredentials = token.trim() !== "" || apiKey.trim() !== "";
  const cards = useMemo(() => buildConnectCards(hasCredentials, status), [hasCredentials, status]);
  const score = getConnectScore(cards);
  const nextAttention = cards.find((card) => card.status === "attention") ?? cards[0];

  const refresh = useCallback(async (): Promise<void> => {
    if (!hasCredentials) {
      setStatus(null);
      setError("");
      return;
    }

    setLoading(true);
    setError("");
    try {
      const result = await fetchOnboardingStatus(token, apiKey);
      onResult("Connect Center - Readiness", result);
      const parsed = asOnboardingStatus(result.data);
      if (!result.ok || parsed === null) {
        setError(`Connection scan failed (${result.status})`);
        return;
      }
      setStatus(parsed);
    } catch (refreshError) {
      setError(refreshError instanceof Error ? refreshError.message : "Unknown connection scan error");
    } finally {
      setLoading(false);
    }
  }, [apiKey, hasCredentials, onResult, token]);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return (
    <section className="connect-center-panel" aria-labelledby="connect-center-title">
      <header className="connect-center-hero">
        <div>
          <p className="eyebrow">Unified setup</p>
          <h2 id="connect-center-title">Connect the pieces AGENT-33 needs to work</h2>
          <p>
            One readable checklist for engine access, model providers, integrations, MCP tools,
            tool catalog visibility, and safe approvals. Each card routes to the existing setup
            surface instead of making users hunt through settings.
          </p>
        </div>
        <div className="connect-center-score">
          <strong>{loading ? "Scanning..." : score}</strong>
          <span>{hasCredentials ? "Live readiness when available" : "Add access to scan live status"}</span>
        </div>
      </header>

      <article className="connect-center-next">
        <div>
          <p className="eyebrow">Recommended next connection</p>
          <h3>{nextAttention.title}</h3>
          <p>{nextAttention.detail}</p>
        </div>
        <div className="connect-center-actions">
          <button type="button" onClick={() => void refresh()} disabled={loading}>
            {loading ? "Refreshing..." : "Refresh connection scan"}
          </button>
          <button type="button" onClick={() => onNavigate(nextAttention.target)}>
            {nextAttention.actionLabel}
          </button>
        </div>
      </article>

      {error ? (
        <p className="connect-center-error" role="alert">
          {error}
        </p>
      ) : null}

      <div className="connect-center-grid">
        {cards.map((card) => (
          <article className={`connect-card connect-card--${card.status}`} key={card.id}>
            <div className="connect-card-head">
              <span>{statusLabel(card.status)}</span>
              <strong>{card.title}</strong>
            </div>
            <h3>{card.plainLabel}</h3>
            <p>{card.detail}</p>
            <p>{card.impact}</p>
            <button type="button" onClick={() => onNavigate(card.target)}>
              {card.actionLabel}
            </button>
          </article>
        ))}
      </div>
    </section>
  );
}
