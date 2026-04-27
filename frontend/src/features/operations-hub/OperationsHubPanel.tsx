import { useCallback, useEffect, useMemo, useState } from "react";

import type { ApiResult } from "../../types";
import {
  asOperationsHubDetail,
  asOperationsHubResponse,
  controlProcess,
  fetchOperationsHub,
  fetchProcessDetail
} from "./api";
import {
  buildOperationsTimeline,
  canCancel,
  canPause,
  canResume,
  filterAndSortProcesses,
  formatTimestamp,
  getStatusClass,
  getStatusLabel,
  summarizeOperations
} from "./helpers";
import { IngestionReviewPanel } from "./IngestionReviewPanel";
import type {
  OperationsHubControlAction,
  OperationsHubProcessDetail,
  OperationsHubProcessSummary
} from "./types";

interface OperationsHubPanelProps {
  token: string;
  apiKey: string;
  onResult: (label: string, result: ApiResult) => void;
}

function stringifyMetadata(value: unknown): string {
  if (value === undefined) {
    return "";
  }
  return JSON.stringify(value, null, 2);
}

export function OperationsHubPanel({
  token,
  apiKey,
  onResult
}: OperationsHubPanelProps): JSX.Element {
  const [processes, setProcesses] = useState<OperationsHubProcessSummary[]>([]);
  const [selectedProcessId, setSelectedProcessId] = useState<string | null>(null);
  const [selectedProcess, setSelectedProcess] = useState<OperationsHubProcessDetail | null>(null);
  const [hubTimestamp, setHubTimestamp] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [textFilter, setTextFilter] = useState("");
  const [loadingHub, setLoadingHub] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [controlInFlight, setControlInFlight] = useState<OperationsHubControlAction | null>(null);
  const [hubError, setHubError] = useState("");
  const [detailError, setDetailError] = useState("");

  const loadHub = useCallback(async (): Promise<void> => {
    if (!token && !apiKey) {
      return;
    }
    setLoadingHub(true);
    try {
      const result = await fetchOperationsHub(token, apiKey);
      onResult("Operations Hub - Poll", result);
      const hub = asOperationsHubResponse(result.data);
      if (!result.ok || hub === null) {
        setHubError(`Failed to load operations hub (${result.status})`);
        return;
      }
      setHubError("");
      setProcesses(hub.processes);
      setHubTimestamp(hub.timestamp);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown operations hub error";
      setHubError(message);
    } finally {
      setLoadingHub(false);
    }
  }, [apiKey, onResult, token]);

  const loadDetail = useCallback(
    async (processId: string): Promise<void> => {
      if (!token && !apiKey) {
        return;
      }
      setLoadingDetail(true);
      try {
        const result = await fetchProcessDetail(processId, token, apiKey);
        onResult(`Operations Hub - Detail ${processId}`, result);
        const detail = asOperationsHubDetail(result.data);
        if (!result.ok || detail === null) {
          setDetailError(`Failed to load process detail (${result.status})`);
          return;
        }
        setDetailError("");
        setSelectedProcess(detail);
      } catch (error) {
        const message = error instanceof Error ? error.message : "Unknown process detail error";
        setDetailError(message);
      } finally {
        setLoadingDetail(false);
      }
    },
    [apiKey, onResult, token]
  );

  useEffect(() => {
    loadHub();
    const interval = setInterval(() => {
      loadHub();
    }, 1500);
    return () => clearInterval(interval);
  }, [loadHub]);

  useEffect(() => {
    if (selectedProcessId === null) {
      setSelectedProcess(null);
      setDetailError("");
      return;
    }
    loadDetail(selectedProcessId);
  }, [loadDetail, selectedProcessId]);

  const filteredProcesses = useMemo(() => {
    return filterAndSortProcesses(processes, statusFilter, textFilter);
  }, [processes, statusFilter, textFilter]);

  const timelineSummary = useMemo(() => summarizeOperations(processes), [processes]);
  const timelineItems = useMemo(
    () => buildOperationsTimeline(filteredProcesses, selectedProcess),
    [filteredProcesses, selectedProcess]
  );

  const availableStatuses = useMemo(() => {
    const values = new Set<string>(["all"]);
    processes.forEach((process) => values.add(process.status.toLowerCase()));
    return [...values];
  }, [processes]);

  async function handleControl(action: OperationsHubControlAction): Promise<void> {
    if (selectedProcess === null) {
      return;
    }
    if (action === "cancel") {
      const confirmed = window.confirm(
        `Cancel process '${selectedProcess.name}' (${selectedProcess.id})?`
      );
      if (!confirmed) {
        return;
      }
    }

    setControlInFlight(action);
    try {
      const result = await controlProcess(selectedProcess.id, action, token, apiKey);
      onResult(`Operations Hub - ${action}`, result);
      if (!result.ok) {
        setDetailError(`Control '${action}' failed (${result.status})`);
        return;
      }
      await Promise.all([loadHub(), loadDetail(selectedProcess.id)]);
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown control error";
      setDetailError(message);
    } finally {
      setControlInFlight(null);
    }
  }

  return (
    <section className="operations-hub-panel">
      <header className="ops-hub-head">
        <div>
          <p className="ops-hub-eyebrow">Run Timeline</p>
          <h2>See what the agents are doing right now</h2>
          <p>Plain-language progress, attention signals, and safe controls for active work.</p>
        </div>
        <div className="ops-hub-filters">
          <label>
            Status
            <select value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>
              {availableStatuses.map((status) => (
                <option key={status} value={status}>
                  {status === "all" ? "All" : getStatusLabel(status)}
                </option>
              ))}
            </select>
          </label>
          <label>
            Search
            <input
              placeholder="Filter by name, id, or type"
              value={textFilter}
              onChange={(event) => setTextFilter(event.target.value)}
            />
          </label>
        </div>
      </header>
      <section className="ops-timeline-overview" aria-label="Run timeline overview">
        <div className="ops-timeline-summary-card">
          <span>Current state</span>
          <strong>{timelineSummary.primaryMessage}</strong>
          <p>{timelineSummary.nextAction}</p>
        </div>
        <div className="ops-timeline-stats" aria-label="Run counts">
          <div>
            <strong>{timelineSummary.total}</strong>
            <span>Total</span>
          </div>
          <div>
            <strong>{timelineSummary.active}</strong>
            <span>Working</span>
          </div>
          <div>
            <strong>{timelineSummary.attention}</strong>
            <span>Needs attention</span>
          </div>
          <div>
            <strong>{timelineSummary.done}</strong>
            <span>Done</span>
          </div>
        </div>
      </section>
      <section className="ops-timeline-panel" aria-label="Latest agent activity">
        <div className="ops-timeline-head">
          <div>
            <h3>Latest activity</h3>
            <p>Select a process below to add its step-by-step actions to this timeline.</p>
          </div>
          {hubTimestamp ? <span>Updated {formatTimestamp(hubTimestamp)}</span> : null}
        </div>
        {timelineItems.length === 0 && !loadingHub ? (
          <p className="ops-hub-empty">No agent activity yet.</p>
        ) : null}
        {timelineItems.length > 0 ? (
          <ol className="ops-timeline-list">
            {timelineItems.map((item) => (
              <li key={item.id} className={`ops-timeline-item ops-timeline-item--${item.tone}`}>
                <div className="ops-timeline-marker" aria-hidden="true" />
                <div>
                  <span className="ops-timeline-time">{formatTimestamp(item.timestamp)}</span>
                  <h4>{item.title}</h4>
                  <p>{item.description}</p>
                </div>
              </li>
            ))}
          </ol>
        ) : null}
      </section>
      <div className="ops-hub-content">
        <div className="ops-hub-list">
          {hubError ? <p className="ops-hub-error" role="alert">{hubError}</p> : null}
          {loadingHub && processes.length === 0 ? (
            <p className="ops-hub-loading">Loading processes...</p>
          ) : null}
          {filteredProcesses.length === 0 && !loadingHub ? (
            <p className="ops-hub-empty">No matching processes.</p>
          ) : null}
          {filteredProcesses.map((process) => (
            <article
              key={process.id}
              className={`ops-hub-process-item ${selectedProcessId === process.id ? "selected" : ""}`}
              onClick={() => setSelectedProcessId(process.id)}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  setSelectedProcessId(process.id);
                }
              }}
              tabIndex={0}
              role="button"
              aria-pressed={selectedProcessId === process.id}
            >
              <div className="process-item-header">
                <h3>{process.name}</h3>
                <span className={`process-status ${getStatusClass(process.status)}`}>
                  {getStatusLabel(process.status)}
                </span>
              </div>
              <p className="process-item-id">{process.id}</p>
              <p className="process-item-time">Type: {process.type}</p>
              <p className="process-item-time">Started: {formatTimestamp(process.started_at)}</p>
            </article>
          ))}
          {hubTimestamp ? (
            <p className="process-item-time">Last refresh: {formatTimestamp(hubTimestamp)}</p>
          ) : null}
        </div>
        <div className="ops-hub-detail">
          {selectedProcessId === null ? (
            <p className="ops-hub-placeholder">Select a process to view details.</p>
          ) : null}
          {loadingDetail ? <p className="ops-hub-loading">Loading detail...</p> : null}
          {detailError ? <p className="ops-hub-error" role="alert">{detailError}</p> : null}
          {selectedProcess !== null && !loadingDetail ? (
            <div className="process-detail">
              <h3>{selectedProcess.name}</h3>
              <div className="detail-field">
                <span className="detail-label">ID</span>
                <span>{selectedProcess.id}</span>
              </div>
              <div className="detail-field">
                <span className="detail-label">Type</span>
                <span>{selectedProcess.type}</span>
              </div>
              <div className="detail-field">
                <span className="detail-label">Status</span>
                <span className={`process-status ${getStatusClass(selectedProcess.status)}`}>
                  {getStatusLabel(selectedProcess.status)}
                </span>
              </div>
              <div className="detail-field">
                <span className="detail-label">Started</span>
                <span>{formatTimestamp(selectedProcess.started_at)}</span>
              </div>

              {selectedProcess.metadata ? (
                <div className="detail-section">
                  <h4>Metadata</h4>
                  <pre className="detail-metadata">{stringifyMetadata(selectedProcess.metadata)}</pre>
                </div>
              ) : null}

              {selectedProcess.actions && selectedProcess.actions.length > 0 ? (
                <div className="detail-section">
                  <h4>Actions</h4>
                  <div className="detail-log">
                    {selectedProcess.actions.map((action) => (
                      <div key={action.step_id} className="log-entry log-info">
                        <span className="log-time">
                          {action.completed_at ? formatTimestamp(action.completed_at) : "In progress"}
                        </span>
                        <span className="log-message">
                          {action.step_id} ({action.action_count} actions)
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : null}

              <div className="process-controls">
                <h4>Controls</h4>
                <div className="control-buttons">
                  <button
                    disabled={!canPause(selectedProcess) || controlInFlight !== null}
                    onClick={() => handleControl("pause")}
                  >
                    Pause
                  </button>
                  <button
                    disabled={!canResume(selectedProcess) || controlInFlight !== null}
                    onClick={() => handleControl("resume")}
                  >
                    Resume
                  </button>
                  <button
                    className="control-danger"
                    disabled={!canCancel(selectedProcess) || controlInFlight !== null}
                    onClick={() => handleControl("cancel")}
                  >
                    Cancel
                  </button>
                </div>
              </div>
            </div>
          ) : null}
        </div>
      </div>
      <IngestionReviewPanel token={token} apiKey={apiKey} onResult={onResult} />
    </section>
  );
}
