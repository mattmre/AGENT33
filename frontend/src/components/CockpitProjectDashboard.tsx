import type { PermissionModeId } from "../data/permissionModes";
import { getPermissionMode } from "../data/permissionModes";
import type { WorkspaceSessionSummary } from "../data/workspaces";
import { getWorkspaceTaskCounts } from "../data/workspaceBoard";
import type { CockpitArtifact } from "../data/cockpitArtifacts";
import { getCockpitArtifactsForWorkspace } from "../data/cockpitArtifacts";
import { buildCockpitOpsSafetySnapshot } from "../data/cockpitOpsSafety";

interface CockpitProjectDashboardProps {
  workspace: WorkspaceSessionSummary;
  permissionModeId: PermissionModeId;
  onReviewCurrentWork: () => void;
  onOpenWorkflows: () => void;
  onOpenSafety: () => void;
}

function getRecommendedAction(workspace: WorkspaceSessionSummary): string {
  if (workspace.status === "Running") {
    return "Open Sessions & Runs to inspect live progress, blockers, and review gates.";
  }

  if (workspace.status === "Planning") {
    return "Choose a workflow and turn the planning notes into an executable task sequence.";
  }

  return "Start with a guided workflow so AGENT33 can create the first safe task plan.";
}

function getArtifactStatusLabel(artifact: CockpitArtifact): string {
  return `${artifact.status.replace(/-/g, " ")} / ${artifact.reviewState.replace(/-/g, " ")}`;
}

export function CockpitProjectDashboard({
  workspace,
  permissionModeId,
  onReviewCurrentWork,
  onOpenWorkflows,
  onOpenSafety
}: CockpitProjectDashboardProps): JSX.Element {
  const permissionMode = getPermissionMode(permissionModeId);
  const taskCounts = getWorkspaceTaskCounts(workspace.id);
  const activeTaskCount = taskCounts.running + taskCounts.review + taskCounts.blocked;
  const attentionTaskLabel = activeTaskCount === 1 ? "1 task needs attention" : `${activeTaskCount} tasks need attention`;
  const artifacts = getCockpitArtifactsForWorkspace(workspace.id);
  const opsSafety = buildCockpitOpsSafetySnapshot({ workspaceId: workspace.id, permissionModeId });
  const safetySignals = opsSafety.records.slice(0, 4);

  return (
    <section className="cockpit-project-dashboard" aria-label="Project cockpit dashboard">
      <header className="cockpit-dashboard-hero">
        <div>
          <span className="eyebrow">Project cockpit</span>
          <h2>{workspace.name}</h2>
          <p>{workspace.goal}</p>
        </div>
        <div className="cockpit-dashboard-status" aria-label="Current project status">
          <span>{workspace.status}</span>
          <strong>{permissionMode.label}</strong>
        </div>
      </header>

      <div className="cockpit-dashboard-grid">
        <article className="cockpit-dashboard-card">
          <span className="eyebrow">Current run</span>
          <strong>{attentionTaskLabel}</strong>
          <p>{getRecommendedAction(workspace)}</p>
          <button type="button" onClick={onReviewCurrentWork}>
            Review task board
          </button>
        </article>

        <article className="cockpit-dashboard-card">
          <span className="eyebrow">Recommended next action</span>
          <strong>Use a guided workflow</strong>
          <p>Route the current project through a prebuilt starter instead of raw JSON or endpoint setup.</p>
          <button type="button" onClick={onOpenWorkflows}>
            Choose workflow
          </button>
        </article>

        <article className="cockpit-dashboard-card">
          <span className="eyebrow">Safety gate</span>
          <strong>{permissionMode.headline}</strong>
          <p>{permissionMode.reviewGate}</p>
          <button type="button" onClick={onOpenSafety}>
            Review approvals
          </button>
        </article>
      </div>

      <section className="cockpit-dashboard-timeline" aria-label="Artifact timeline">
        <div className="cockpit-dashboard-section-heading">
          <div>
            <span className="eyebrow">Artifacts</span>
            <h3>Review timeline</h3>
          </div>
          <p>Typed evidence cards show owner, review state, timestamp, and the next safe action.</p>
        </div>
        <div className="cockpit-dashboard-artifacts">
          {artifacts.map((artifact) => (
            <article key={artifact.id} className={`artifact-card artifact-card-${artifact.status}`}>
              <span>{artifact.kind}</span>
              <strong>{artifact.title}</strong>
              <p>{artifact.summary}</p>
              <dl className="artifact-card-meta">
                <div>
                  <dt>Status</dt>
                  <dd>{getArtifactStatusLabel(artifact)}</dd>
                </div>
                <div>
                  <dt>Owner</dt>
                  <dd>{artifact.ownerRole}</dd>
                </div>
                <div>
                  <dt>Source</dt>
                  <dd>{artifact.sourceLabel}</dd>
                </div>
                <div>
                  <dt>Updated</dt>
                  <dd>{artifact.timestampLabel}</dd>
                </div>
              </dl>
              <button type="button" onClick={onReviewCurrentWork}>
                {artifact.nextActionLabel}
              </button>
            </article>
          ))}
        </div>
      </section>

      <section className="cockpit-dashboard-safety-signals" aria-label="Safety and coordination signals">
        <div className="cockpit-dashboard-section-heading">
          <div>
            <span className="eyebrow">Coordination</span>
            <h3>{opsSafety.summary.primaryMessage}</h3>
          </div>
          <p>{opsSafety.summary.nextAction}</p>
        </div>
        <div className="cockpit-dashboard-signal-grid">
          {safetySignals.map((signal) => (
            <article key={signal.id} className={`cockpit-safety-signal signal-${signal.status}`}>
              <span>{signal.kind.replace(/-/g, " ")}</span>
              <strong>{signal.title}</strong>
              <p>{signal.summary}</p>
              <small>
                {signal.sourceLabel} {"->"} {signal.relatedArtifactKind} artifact
              </small>
            </article>
          ))}
        </div>
      </section>
    </section>
  );
}
