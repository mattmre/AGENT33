/**
 * ExplanationView component - minimal stub for explanation display.
 *
 * Scaffold for Phase 26 Stage 1. Future enhancements:
 * - Render explanation content with syntax highlighting
 * - Display fact-check status with visual indicators
 * - Show metadata (model, confidence, timestamp)
 * - Interactive fact-check controls
 */

import React from "react";

export interface ExplanationData {
  id: string;
  entity_type: string;
  entity_id: string;
  content: string;
   mode?: "generic" | "diff_review" | "plan_review" | "project_recap";
  fact_check_status: "pending" | "verified" | "flagged" | "skipped";
  created_at: string;
  metadata?: Record<string, unknown>;
  claims?: ExplanationClaimData[];
}

export interface ExplanationClaimData {
  id: string;
  claim_type: string;
  target: string;
  expected?: string;
  actual?: string;
  description?: string;
  message?: string;
  status: "pending" | "verified" | "flagged" | "skipped";
}

export interface ExplanationViewProps {
  explanation: ExplanationData;
}

export const ExplanationView: React.FC<ExplanationViewProps> = ({
  explanation
}) => {
  return (
    <div data-testid="explanation-view" className="explanation-view">
      <div className="explanation-header">
        <h3>Explanation: {explanation.id}</h3>
        <span
          className={`fact-check-badge fact-check-${explanation.fact_check_status}`}
          data-testid="fact-check-status"
        >
          {explanation.fact_check_status}
        </span>
      </div>

      <div className="explanation-meta">
        <span>
          Entity: {explanation.entity_type} / {explanation.entity_id}
        </span>
        <span>Created: {new Date(explanation.created_at).toLocaleString()}</span>
      </div>

      <div className="explanation-content" data-testid="explanation-content">
        <p>{explanation.content}</p>
      </div>

      {explanation.claims && explanation.claims.length > 0 && (
        <div className="explanation-claims" data-testid="explanation-claims">
          <h4>Fact-check claims</h4>
          <ul>
            {explanation.claims.map((claim) => (
              <li key={claim.id}>
                <strong>{claim.claim_type}</strong>: {claim.description || claim.target} (
                {claim.status})
                {claim.message ? <span> - {claim.message}</span> : null}
              </li>
            ))}
          </ul>
        </div>
      )}

      {explanation.metadata && Object.keys(explanation.metadata).length > 0 && (
        <div className="explanation-metadata">
          <h4>Metadata</h4>
          <pre>{JSON.stringify(explanation.metadata, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};
