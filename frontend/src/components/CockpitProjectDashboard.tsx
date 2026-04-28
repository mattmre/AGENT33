import type { PermissionModeId } from "../data/permissionModes";
import { getPermissionMode } from "../data/permissionModes";
import type { WorkspaceSessionSummary } from "../data/workspaces";
import { getWorkspaceTaskCounts } from "../data/workspaceBoard";

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

      <div className="cockpit-dashboard-artifacts" aria-label="Recent artifact placeholders">
        <article>
          <span>Plan</span>
          <strong>{workspace.template} task plan</strong>
          <p>Assumptions, risks, and validation commands will collect here as tasks run.</p>
        </article>
        <article>
          <span>Validation</span>
          <strong>Checks not run yet</strong>
          <p>Test, lint, build, and review results will appear after a session produces evidence.</p>
        </article>
        <article>
          <span>Outcome</span>
          <strong>No PR or package linked</strong>
          <p>The done state will point to a PR, artifact package, or blocker once execution starts.</p>
        </article>
      </div>
    </section>
  );
}
