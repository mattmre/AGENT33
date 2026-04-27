import { useCallback, useEffect, useMemo, useState } from "react";

import { formatTimestamp, getStatusClass, getStatusLabel } from "../operations-hub/helpers";
import type { ApiResult } from "../../types";
import {
  asToolApprovalList,
  asToolApprovalRequest,
  decideToolApproval,
  fetchToolApprovals
} from "./api";
import {
  TOOL_APPROVAL_STATUSES,
  type ToolApprovalDecision,
  type ToolApprovalRequest,
  type ToolApprovalStatus
} from "./types";

interface SafetyCenterPanelProps {
  token: string;
  apiKey: string;
  onOpenSetup: () => void;
  onResult: (label: string, result: ApiResult) => void;
}

type ApprovalFilter = ToolApprovalStatus | "all";

function describeReason(reason: string): string {
  switch (reason) {
    case "supervised_destructive":
      return "Destructive or high-impact action";
    case "tool_policy_ask":
      return "Configured to ask before running";
    default:
      return getStatusLabel(reason);
  }
}

function formatRelativeRisk(request: ToolApprovalRequest): string {
  if (request.reason === "supervised_destructive") {
    return "High risk";
  }
  if (request.command || request.operation) {
    return "Needs review";
  }
  return "Routine approval";
}

function getApprovalTitle(request: ToolApprovalRequest): string {
  if (request.operation) {
    return `${request.tool_name}: ${request.operation}`;
  }
  return request.tool_name;
}

export function SafetyCenterPanel({
  token,
  apiKey,
  onOpenSetup,
  onResult
}: SafetyCenterPanelProps): JSX.Element {
  const [approvals, setApprovals] = useState<ToolApprovalRequest[]>([]);
  const [selectedApprovalId, setSelectedApprovalId] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<ApprovalFilter>("pending");
  const [textFilter, setTextFilter] = useState("");
  const [reviewNote, setReviewNote] = useState("");
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState("");
  const [actionError, setActionError] = useState("");
  const [actionSuccess, setActionSuccess] = useState("");
  const [actionInFlight, setActionInFlight] = useState<ToolApprovalDecision | null>(null);

  const hasCredentials = token.trim() !== "" || apiKey.trim() !== "";

  const loadApprovals = useCallback(async (): Promise<ToolApprovalRequest[] | null> => {
    if (!hasCredentials) {
      return null;
    }
    setLoading(true);
    try {
      const result = await fetchToolApprovals(statusFilter, token, apiKey);
      onResult("Safety Center - Tool Approvals", result);
      const records = asToolApprovalList(result.data);
      if (!result.ok || records === null) {
        setLoadError(`Failed to load safety approvals (${result.status})`);
        return null;
      }
      setLoadError("");
      setApprovals(records);
      if (records.length === 0) {
        setSelectedApprovalId(null);
        return records;
      }
      setSelectedApprovalId((current) => {
        if (current !== null && records.some((approval) => approval.approval_id === current)) {
          return current;
        }
        return records[0].approval_id;
      });
      return records;
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown safety approval error";
      setLoadError(message);
      return null;
    } finally {
      setLoading(false);
    }
  }, [apiKey, hasCredentials, onResult, statusFilter, token]);

  useEffect(() => {
    void loadApprovals();
    const interval = setInterval(() => {
      void loadApprovals();
    }, 5000);
    return () => clearInterval(interval);
  }, [loadApprovals]);

  const filteredApprovals = useMemo(() => {
    const normalizedText = textFilter.trim().toLowerCase();
    return approvals.filter((approval) => {
      if (normalizedText === "") {
        return true;
      }
      return (
        approval.approval_id.toLowerCase().includes(normalizedText) ||
        approval.tool_name.toLowerCase().includes(normalizedText) ||
        approval.operation.toLowerCase().includes(normalizedText) ||
        approval.command.toLowerCase().includes(normalizedText) ||
        approval.requested_by.toLowerCase().includes(normalizedText) ||
        approval.details.toLowerCase().includes(normalizedText)
      );
    });
  }, [approvals, textFilter]);

  const selectedApproval = useMemo(() => {
    if (selectedApprovalId === null) {
      return null;
    }
    return approvals.find((approval) => approval.approval_id === selectedApprovalId) ?? null;
  }, [approvals, selectedApprovalId]);

  const pendingCount = useMemo(() => {
    return approvals.filter((approval) => approval.status === "pending").length;
  }, [approvals]);

  async function handleDecision(decision: ToolApprovalDecision): Promise<void> {
    if (selectedApproval === null) {
      return;
    }
    const trimmedNote = reviewNote.trim();
    if (trimmedNote === "") {
      setActionError("Add a short review note before approving or rejecting this action.");
      return;
    }
    setActionError("");
    setActionSuccess("");
    setActionInFlight(decision);
    try {
      const result = await decideToolApproval(
        selectedApproval.approval_id,
        decision,
        trimmedNote,
        token,
        apiKey
      );
      onResult(`Safety Center - ${decision}`, result);
      const updated = asToolApprovalRequest(result.data);
      if (!result.ok || updated === null) {
        setActionError(`${getStatusLabel(decision)} failed (${result.status})`);
        return;
      }
      setActionSuccess(
        decision === "approve"
          ? `${getApprovalTitle(selectedApproval)} approved. The governed action may now continue.`
          : `${getApprovalTitle(selectedApproval)} rejected. The governed action will remain blocked.`
      );
      setReviewNote("");
      await loadApprovals();
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown approval decision error";
      setActionError(message);
    } finally {
      setActionInFlight(null);
    }
  }

  if (!hasCredentials) {
    return (
      <section className="safety-center-panel">
        <div className="onboarding-callout onboarding-callout-error">
          <h3>Connect to the engine first</h3>
          <p>
            Safety approvals are tenant-scoped. Add an API key or operator token before approving
            destructive tool actions.
          </p>
          <button onClick={onOpenSetup}>Open integrations and API access</button>
        </div>
      </section>
    );
  }

  return (
    <section className="safety-center-panel">
      <header className="safety-center-hero">
        <div>
          <h2>Safety Center</h2>
          <p>
            Review high-impact tool calls before they can run. This keeps destructive commands,
            file mutations, and governed operations visible to a human operator.
          </p>
        </div>
        <div className="safety-center-score" aria-label={`${pendingCount} pending approvals`}>
          <strong>{pendingCount}</strong>
          <span>pending approvals</span>
        </div>
      </header>

      <div className="review-panel-toolbar" aria-label="Safety approval filters">
        <label>
          Search approvals
          <input
            placeholder="Tool, command, requester, or id"
            value={textFilter}
            onChange={(event) => setTextFilter(event.target.value)}
          />
        </label>
        <label>
          Status
          <select
            value={statusFilter}
            onChange={(event) => {
              setStatusFilter(event.target.value as ApprovalFilter);
              setSelectedApprovalId(null);
            }}
          >
            <option value="all">All statuses</option>
            {TOOL_APPROVAL_STATUSES.map((status) => (
              <option key={status} value={status}>
                {getStatusLabel(status)}
              </option>
            ))}
          </select>
        </label>
        <button onClick={() => void loadApprovals()} disabled={loading}>
          {loading ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      <div className="safety-center-content">
        <div className="review-asset-list safety-approval-list">
          {loadError ? <p className="ops-hub-error" role="alert">{loadError}</p> : null}
          {loading && approvals.length === 0 ? (
            <p className="ops-hub-loading">Loading safety approvals...</p>
          ) : null}
          {approvals.length === 0 && !loading && !loadError ? (
            <p className="ops-hub-empty">No tool approvals match this status.</p>
          ) : null}
          {approvals.length > 0 && filteredApprovals.length === 0 ? (
            <p className="ops-hub-empty">No approvals match the current search.</p>
          ) : null}
          {filteredApprovals.map((approval) => (
            <article
              key={approval.approval_id}
              className={`ops-hub-process-item ${selectedApprovalId === approval.approval_id ? "selected" : ""}`}
              onClick={() => setSelectedApprovalId(approval.approval_id)}
              onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                  event.preventDefault();
                  setSelectedApprovalId(approval.approval_id);
                }
              }}
              tabIndex={0}
              role="button"
              aria-pressed={selectedApprovalId === approval.approval_id}
            >
              <div className="process-item-header">
                <h4>{getApprovalTitle(approval)}</h4>
                <span className={`process-status ${getStatusClass(approval.status)}`}>
                  {getStatusLabel(approval.status)}
                </span>
              </div>
              <p className="process-item-id">{approval.approval_id}</p>
              <p className="process-item-time">
                {formatRelativeRisk(approval)} • {describeReason(approval.reason)}
              </p>
              <div className="review-asset-flags">
                {approval.requested_by ? (
                  <span className="review-asset-flag">Requested by {approval.requested_by}</span>
                ) : null}
                {approval.expires_at ? (
                  <span className="review-asset-flag">Expires {formatTimestamp(approval.expires_at)}</span>
                ) : null}
              </div>
            </article>
          ))}
        </div>

        <div className="ops-hub-detail safety-approval-detail">
          {selectedApproval === null ? (
            <p className="ops-hub-placeholder">Select an approval to inspect impact and decide.</p>
          ) : null}
          {actionError ? <p className="ops-hub-error" role="alert">{actionError}</p> : null}
          {actionSuccess ? <p className="review-action-success">{actionSuccess}</p> : null}
          {selectedApproval !== null ? (
            <div className="process-detail">
              <h3>{getApprovalTitle(selectedApproval)}</h3>
              <p className="safety-risk-summary">{describeReason(selectedApproval.reason)}</p>

              <div className="detail-field">
                <span className="detail-label">Approval ID</span>
                <span>{selectedApproval.approval_id}</span>
              </div>
              <div className="detail-field">
                <span className="detail-label">Status</span>
                <span className={`process-status ${getStatusClass(selectedApproval.status)}`}>
                  {getStatusLabel(selectedApproval.status)}
                </span>
              </div>
              <div className="detail-field">
                <span className="detail-label">Tool</span>
                <span>{selectedApproval.tool_name}</span>
              </div>
              <div className="detail-field">
                <span className="detail-label">Operation</span>
                <span>{selectedApproval.operation || "Not specified"}</span>
              </div>
              <div className="detail-field">
                <span className="detail-label">Requester</span>
                <span>{selectedApproval.requested_by || "Unknown"}</span>
              </div>
              <div className="detail-field">
                <span className="detail-label">Created</span>
                <span>{formatTimestamp(selectedApproval.created_at)}</span>
              </div>
              <div className="detail-field">
                <span className="detail-label">Expires</span>
                <span>{selectedApproval.expires_at ? formatTimestamp(selectedApproval.expires_at) : "No expiry"}</span>
              </div>

              {selectedApproval.command ? (
                <div className="detail-section">
                  <h4>Command preview</h4>
                  <pre className="safety-command-preview">{selectedApproval.command}</pre>
                </div>
              ) : null}

              {selectedApproval.details ? (
                <div className="detail-section">
                  <h4>Request details</h4>
                  <p>{selectedApproval.details}</p>
                </div>
              ) : null}

              {selectedApproval.status === "pending" ? (
                <div className="detail-section">
                  <h4>Operator decision</h4>
                  <div className="review-action-form">
                    <label>
                      Review note
                      <textarea
                        rows={3}
                        value={reviewNote}
                        onChange={(event) => setReviewNote(event.target.value)}
                        placeholder="Explain why this action is safe or why it should stay blocked."
                      />
                    </label>
                    <div className="review-action-buttons">
                      <button
                        className="danger"
                        onClick={() => void handleDecision("reject")}
                        disabled={actionInFlight !== null}
                      >
                        {actionInFlight === "reject" ? "Rejecting..." : "Reject action"}
                      </button>
                      <button onClick={() => void handleDecision("approve")} disabled={actionInFlight !== null}>
                        {actionInFlight === "approve" ? "Approving..." : "Approve action"}
                      </button>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="detail-section">
                  <h4>Audit trail</h4>
                  <p>
                    Reviewed by {selectedApproval.reviewed_by || "unknown operator"}
                    {selectedApproval.reviewed_at ? ` on ${formatTimestamp(selectedApproval.reviewed_at)}` : ""}.
                  </p>
                  {selectedApproval.review_note ? <p>{selectedApproval.review_note}</p> : null}
                </div>
              )}
            </div>
          ) : null}
        </div>
      </div>
    </section>
  );
}
