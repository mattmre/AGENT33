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

function parseJsonValue(text: string, emptyFallback: unknown = {}): unknown {
  if (text.trim() === "") {
    return emptyFallback;
  }
  return JSON.parse(text);
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
  const initialPathParamsText = useMemo(
    () => JSON.stringify(operation.defaultPathParams ?? {}, null, 2),
    [operation.defaultPathParams]
  );
  const initialQueryText = useMemo(
    () => JSON.stringify(operation.defaultQuery ?? {}, null, 2),
    [operation.defaultQuery]
  );
  const initialBodyText = useMemo(() => operation.defaultBody ?? "", [operation.defaultBody]);

  const isWorkflowExecute = operation.uxHint === "workflow-execute";
  const isWorkflowSchedule = operation.uxHint === "workflow-schedule";
  const isAgentIterative = operation.uxHint === "agent-iterative";

  const [pathParamsText, setPathParamsText] = useState(
    initialPathParamsText
  );
  const [queryText, setQueryText] = useState(initialQueryText);
  const [bodyText, setBodyText] = useState(initialBodyText);
  const [error, setError] = useState("");
  const [isRunning, setIsRunning] = useState(false);
  const [result, setResult] = useState<ApiResult | null>(null);
  const [executionMode, setExecutionMode] = useState<"single" | "repeat" | "autonomous">("single");
  const [repeatCount, setRepeatCount] = useState(3);
  const [repeatIntervalSeconds, setRepeatIntervalSeconds] = useState(0);
  const [scheduleMode, setScheduleMode] = useState<"interval" | "cron">("interval");
  const [scheduleIntervalSeconds, setScheduleIntervalSeconds] = useState(900);
  const [scheduleCronExpr, setScheduleCronExpr] = useState("0 */6 * * *");
  const [iterativePreset, setIterativePreset] = useState<"quick" | "balanced" | "deep">("balanced");

  const hasBody = useMemo(
    () => operation.method !== "GET" && operation.method !== "DELETE",
    [operation.method]
  );

  const responseSummary = useMemo(() => {
    if (!result || typeof result.data !== "object" || result.data === null) {
      return "";
    }
    const payload = result.data as Record<string, unknown>;
    if (isAgentIterative && typeof payload.iterations === "number") {
      const toolCalls = typeof payload.tool_calls_made === "number" ? payload.tool_calls_made : 0;
      return `Iterative run completed in ${payload.iterations} iterations with ${toolCalls} tool calls.`;
    }
    if (isWorkflowExecute && typeof payload.executions === "number") {
      return `Workflow autonomous run executed ${payload.executions} iterations.`;
    }
    if (isWorkflowSchedule && typeof payload.job_id === "string") {
      return `Schedule created: ${payload.job_id}`;
    }
    return "";
  }, [isAgentIterative, isWorkflowExecute, isWorkflowSchedule, result]);

  function formatObjectEditor(value: string, setter: (text: string) => void, label: string): void {
    try {
      setter(JSON.stringify(parseObjectJson(value), null, 2));
      setError("");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Invalid JSON object";
      setError(`${label}: ${message}`);
    }
  }

  function formatBodyEditor(): void {
    try {
      const parsed = parseJsonValue(bodyText, {});
      setBodyText(JSON.stringify(parsed, null, 2));
      setError("");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Invalid JSON";
      setError(`Request Body: ${message}`);
    }
  }

  function prepareGuidedBody(): string {
    const parsed = parseJsonValue(bodyText, {});
    if (parsed === null || Array.isArray(parsed) || typeof parsed !== "object") {
      throw new Error("Guided mode requires a JSON object body.");
    }
    const nextBody = { ...(parsed as Record<string, unknown>) };

    if (isWorkflowExecute) {
      delete nextBody.repeat_count;
      delete nextBody.repeat_interval_seconds;
      delete nextBody.autonomous;
      if (executionMode !== "single") {
        nextBody.repeat_count = repeatCount;
        if (repeatIntervalSeconds > 0) {
          nextBody.repeat_interval_seconds = repeatIntervalSeconds;
        }
        nextBody.autonomous = executionMode === "autonomous";
      }
    }

    if (isWorkflowSchedule) {
      if (scheduleMode === "cron") {
        nextBody.cron_expr = scheduleCronExpr;
        delete nextBody.interval_seconds;
      } else {
        nextBody.interval_seconds = scheduleIntervalSeconds;
        delete nextBody.cron_expr;
      }
      if (
        typeof nextBody.inputs !== "object" ||
        nextBody.inputs === null ||
        Array.isArray(nextBody.inputs)
      ) {
        nextBody.inputs = {};
      }
    }

    if (isAgentIterative) {
      const preset =
        iterativePreset === "quick"
          ? { max_iterations: 4, max_tool_calls_per_iteration: 2, enable_double_confirmation: false }
          : iterativePreset === "deep"
            ? { max_iterations: 16, max_tool_calls_per_iteration: 6, enable_double_confirmation: true }
            : { max_iterations: 8, max_tool_calls_per_iteration: 4, enable_double_confirmation: true };
      Object.assign(nextBody, preset);
    }

    return JSON.stringify(nextBody, null, 2);
  }

  function renderGuidedControls(): JSX.Element | null {
    if (!hasBody) {
      return null;
    }
    if (isWorkflowExecute) {
      return (
        <section className="helper-panel">
          <h4>Execution Controls</h4>
          <div className="helper-grid">
            <label>
              Mode
              <select value={executionMode} onChange={(e) => setExecutionMode(e.target.value as "single" | "repeat" | "autonomous")}>
                <option value="single">Single</option>
                <option value="repeat">Repeat</option>
                <option value="autonomous">Autonomous</option>
              </select>
            </label>
            <label>
              Repeat Count
              <input
                type="number"
                min={1}
                max={100}
                value={repeatCount}
                onChange={(e) => setRepeatCount(Math.max(1, Number(e.target.value) || 1))}
              />
            </label>
            <label>
              Repeat Interval (seconds)
              <input
                type="number"
                min={0}
                max={3600}
                value={repeatIntervalSeconds}
                onChange={(e) =>
                  setRepeatIntervalSeconds(Math.max(0, Number(e.target.value) || 0))
                }
              />
            </label>
          </div>
        </section>
      );
    }
    if (isWorkflowSchedule) {
      return (
        <section className="helper-panel">
          <h4>Schedule Controls</h4>
          <div className="helper-grid">
            <label>
              Schedule Type
              <select
                value={scheduleMode}
                onChange={(e) => setScheduleMode(e.target.value as "interval" | "cron")}
              >
                <option value="interval">Interval</option>
                <option value="cron">Cron</option>
              </select>
            </label>
            {scheduleMode === "interval" ? (
              <label>
                Interval (seconds)
                <input
                  type="number"
                  min={1}
                  max={86400}
                  value={scheduleIntervalSeconds}
                  onChange={(e) =>
                    setScheduleIntervalSeconds(Math.max(1, Number(e.target.value) || 1))
                  }
                />
              </label>
            ) : (
              <label>
                Cron (minute hour day month weekday)
                <input
                  value={scheduleCronExpr}
                  onChange={(e) => setScheduleCronExpr(e.target.value)}
                  placeholder="0 */6 * * *"
                />
              </label>
            )}
          </div>
        </section>
      );
    }
    if (isAgentIterative) {
      return (
        <section className="helper-panel">
          <h4>Iterative Strategy</h4>
          <div className="helper-grid">
            <label>
              Preset
              <select
                value={iterativePreset}
                onChange={(e) => setIterativePreset(e.target.value as "quick" | "balanced" | "deep")}
              >
                <option value="quick">Quick</option>
                <option value="balanced">Balanced</option>
                <option value="deep">Deep</option>
              </select>
            </label>
          </div>
        </section>
      );
    }
    return null;
  }

  async function runOperation(): Promise<void> {
    setError("");
    setIsRunning(true);
    try {
      const pathParams = parseObjectJson(pathParamsText);
      const query = parseObjectJson(queryText);
      let requestBody = bodyText;
      if (hasBody) {
        requestBody = operation.uxHint ? prepareGuidedBody() : bodyText;
        if (requestBody.trim() !== "") {
          JSON.parse(requestBody);
        }
        if (operation.uxHint) {
          setBodyText(requestBody);
        }
      }
      const res = await apiRequest({
        method: operation.method,
        path: operation.path,
        token,
        apiKey,
        pathParams,
        query,
        body: hasBody ? requestBody : undefined
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
          <div className="json-tools">
            <button type="button" onClick={() => formatObjectEditor(pathParamsText, setPathParamsText, "Path Params")}>
              Format
            </button>
            <button type="button" onClick={() => setPathParamsText(initialPathParamsText)}>
              Reset
            </button>
          </div>
        </label>
        <label>
          Query Params (JSON)
          <textarea value={queryText} onChange={(e) => setQueryText(e.target.value)} rows={4} />
          <div className="json-tools">
            <button type="button" onClick={() => formatObjectEditor(queryText, setQueryText, "Query Params")}>
              Format
            </button>
            <button type="button" onClick={() => setQueryText(initialQueryText)}>
              Reset
            </button>
          </div>
        </label>
      </div>
      {renderGuidedControls()}
      {hasBody ? (
        <label>
          Request Body (JSON)
          <textarea value={bodyText} onChange={(e) => setBodyText(e.target.value)} rows={8} />
          <div className="json-tools">
            <button type="button" onClick={formatBodyEditor}>
              Format
            </button>
            <button type="button" onClick={() => setBodyText(initialBodyText)}>
              Reset
            </button>
          </div>
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
      {responseSummary ? <p className="operation-note">{responseSummary}</p> : null}
      {error ? <pre className="error-box">{error}</pre> : null}
      {result ? <pre className="response-box">{JSON.stringify(result.data, null, 2)}</pre> : null}
    </article>
  );
}
