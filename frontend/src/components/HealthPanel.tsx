import { useEffect, useState } from "react";

import { apiRequest } from "../lib/api";

interface HealthSnapshot {
  status: string;
  services?: Record<string, string>;
}

export function HealthPanel(): JSX.Element {
  const [health, setHealth] = useState<HealthSnapshot | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    let canceled = false;

    async function load(): Promise<void> {
      try {
        const result = await apiRequest({
          method: "GET",
          path: "/health"
        });
        if (!canceled && result.ok && typeof result.data === "object" && result.data !== null) {
          setHealth(result.data as HealthSnapshot);
          setError("");
        } else if (!canceled) {
          setError(`Health check failed (${result.status})`);
        }
      } catch (err) {
        if (!canceled) {
          setError(err instanceof Error ? err.message : "Health check error");
        }
      }
    }

    load();
    const timer = window.setInterval(load, 5000);
    return () => {
      canceled = true;
      window.clearInterval(timer);
    };
  }, []);

  return (
    <section className="health-panel">
      <h2>Runtime Health</h2>
      {error ? <pre className="error-box">{error}</pre> : null}
      {health ? (
        <div className="health-grid">
          <div className="health-item">
            <h3>Overall</h3>
            <p className={health.status === "healthy" ? "status-ok" : "status-error"}>
              {health.status}
            </p>
          </div>
          {Object.entries(health.services ?? {}).map(([name, status]) => (
            <div className="health-item" key={name}>
              <h3>{name}</h3>
              <p className={status === "ok" ? "status-ok" : "status-error"}>{status}</p>
            </div>
          ))}
        </div>
      ) : (
        <p>Loading health...</p>
      )}
    </section>
  );
}
