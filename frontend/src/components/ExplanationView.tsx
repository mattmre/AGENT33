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
  fact_check_status: "pending" | "verified" | "flagged" | "skipped";
  created_at: string;
  metadata?: Record<string, unknown>;
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

      {explanation.metadata && Object.keys(explanation.metadata).length > 0 && (
        <div className="explanation-metadata">
          <h4>Metadata</h4>
          <pre>{JSON.stringify(explanation.metadata, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};
