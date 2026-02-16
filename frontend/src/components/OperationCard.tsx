import { useMemo, useState } from "react";

import { apiRequest } from "../lib/api";
import type { ApiResult, OperationConfig } from "../types";

interface OperationCardProps {
  operation: OperationConfig;
  token: string;
  apiKey: string;
  onResult: (label: string, result: ApiResult) => void;
}

function normalizeJsonText(input: string): string {
  if (input.trim() === "") {
    return "{}";
  }
  return input;
}

function parseObjectJson(text: string): Record<string, string> {
  const parsed = JSON.parse(normalizeJsonText(text));
  if (parsed === null || Array.isArray(parsed) || typeof parsed !== "object") {
    throw new Error("Expected a JSON object");
  }
  const result: Record<string, string> = {};
  Object.entries(parsed).forEach(([key, value]) => {
    result[key] = String(value);
  });
  return result;
}

export function OperationCard({
  operation,
  token,
  apiKey,
  onResult
}: OperationCardProps): JSX.Element {
  const [pathParamsText, setPathParamsText] = useState(
    JSON.stringify(operation.defaultPathParams ?? {}, null, 2)
  );
  const [queryText, setQueryText] = useState(
    JSON.stringify(operation.defaultQuery ?? {}, null, 2)
  );
  const [bodyText, setBodyText] = useState(operation.defaultBody ?? "");
  const [error, setError] = useState("");
  const [isRunning, setIsRunning] = useState(false);
  const [result, setResult] = useState<ApiResult | null>(null);

  const hasBody = useMemo(
    () => operation.method !== "GET" && operation.method !== "DELETE",
    [operation.method]
  );

  async function runOperation(): Promise<void> {
    setError("");
    setIsRunning(true);
    try {
      const pathParams = parseObjectJson(pathParamsText);
      const query = parseObjectJson(queryText);
      const res = await apiRequest({
        method: operation.method,
        path: operation.path,
        token,
        apiKey,
        pathParams,
        query,
        body: hasBody ? bodyText : undefined
      });
      setResult(res);
      onResult(operation.title, res);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Unknown error while running operation";
      setError(message);
    } finally {
      setIsRunning(false);
    }
  }

  return (
    <article className="operation-card">
      <header className="operation-head">
        <span className={`method-badge method-${operation.method.toLowerCase()}`}>
          {operation.method}
        </span>
        <div>
          <h3>{operation.title}</h3>
          <p>{operation.description}</p>
        </div>
      </header>
      <p className="operation-path">{operation.path}</p>
      <div className="operation-grid">
        <label>
          Path Params (JSON)
          <textarea
            value={pathParamsText}
            onChange={(e) => setPathParamsText(e.target.value)}
            rows={4}
          />
        </label>
        <label>
          Query Params (JSON)
          <textarea value={queryText} onChange={(e) => setQueryText(e.target.value)} rows={4} />
        </label>
      </div>
      {hasBody ? (
        <label>
          Request Body (JSON)
          <textarea value={bodyText} onChange={(e) => setBodyText(e.target.value)} rows={8} />
        </label>
      ) : null}
      <div className="operation-actions">
        <button onClick={runOperation} disabled={isRunning}>
          {isRunning ? "Running..." : "Run"}
        </button>
        {result ? (
          <span className={result.ok ? "status-ok" : "status-error"}>
            {result.status} in {result.durationMs}ms
          </span>
        ) : null}
      </div>
      {error ? <pre className="error-box">{error}</pre> : null}
      {result ? <pre className="response-box">{JSON.stringify(result.data, null, 2)}</pre> : null}
    </article>
  );
}
