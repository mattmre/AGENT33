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
  canCancel,
  canPause,
  canResume,
  filterAndSortProcesses,
  formatTimestamp,
  getStatusClass,
  getStatusLabel
} from "./helpers";
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
          <h2>Operations Hub</h2>
          <p>Unified lifecycle view with pause/resume/cancel controls.</p>
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
      <div className="ops-hub-content">
        <div className="ops-hub-list">
          {hubError ? <p className="ops-hub-error">{hubError}</p> : null}
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
          {detailError ? <p className="ops-hub-error">{detailError}</p> : null}
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
    </section>
  );
}
