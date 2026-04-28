import type { WorkspaceSessionSummary } from "../data/workspaces";
import {
  getWorkspaceBoard,
  type WorkspaceAgentRole,
  type WorkspaceTaskCard
} from "../data/workspaceBoard";

const SHIPYARD_ROLE_ORDER: ReadonlyArray<WorkspaceAgentRole> = ["Coordinator", "Scout", "Builder", "Reviewer"];

const SHIPYARD_ROLE_OUTPUTS: Record<WorkspaceAgentRole, string> = {
  Coordinator: "Sequenced task plan, blockers, and handoff notes.",
  Scout: "Research evidence, risk notes, and comparison findings.",
  Builder: "Implementation slice, validation commands, and changed artifacts.",
  Reviewer: "Review comments, quality gate status, and merge recommendation."
};

interface ShipyardLaneScaffoldProps {
  workspace: WorkspaceSessionSummary;
  onOpenWorkflows: () => void;
  onOpenSafety: () => void;
}

function getLaneStatus(tasks: ReadonlyArray<WorkspaceTaskCard>): string {
  if (tasks.some((task) => task.status === "blocked")) {
    return "Blocked";
  }

  if (tasks.some((task) => task.status === "running")) {
    return "Working";
  }

  if (tasks.some((task) => task.status === "review")) {
    return "Reviewing";
  }

  if (tasks.length > 0 && tasks.every((task) => task.status === "complete")) {
    return "Complete";
  }

  return "Ready";
}

export function ShipyardLaneScaffold({
  workspace,
  onOpenWorkflows,
  onOpenSafety
}: ShipyardLaneScaffoldProps): JSX.Element {
  const board = getWorkspaceBoard(workspace.id);

  return (
    <section className="shipyard-lanes" aria-label="Shipyard lanes">
      <header className="shipyard-lanes-header">
        <div>
          <span className="eyebrow">BridgeSpace-style lanes</span>
          <h2>Shipyard command lanes</h2>
          <p>
            See how coordinator, scout, builder, and reviewer responsibilities split across this
            workspace before deeper execution wiring lands.
          </p>
        </div>
        <div className="shipyard-lanes-actions" aria-label="Shipyard lane actions">
          <button type="button" onClick={onOpenWorkflows}>
            Launch workflow
          </button>
          <button type="button" onClick={onOpenSafety}>
            Check approvals
          </button>
        </div>
      </header>

      <div className="shipyard-lane-grid">
        {SHIPYARD_ROLE_ORDER.map((role) => {
          const agents = board.agents.filter((agent) => agent.role === role);
          const tasks = board.tasks.filter((task) => task.ownerRole === role);
          const status = getLaneStatus(tasks);

          return (
            <article key={role} className={`shipyard-lane-card shipyard-lane-card--${status.toLowerCase()}`}>
              <div className="shipyard-lane-card-header">
                <div>
                  <span>{role}</span>
                  <h3>{agents.map((agent) => agent.name).join(", ") || `${role} lane`}</h3>
                </div>
                <strong>{status}</strong>
              </div>

              <p>{agents.map((agent) => agent.focus).join(" ") || "No agent assigned yet."}</p>
              <small>Expected output: {SHIPYARD_ROLE_OUTPUTS[role]}</small>

              <ul>
                {tasks.length > 0 ? (
                  tasks.map((task) => (
                    <li key={task.id}>
                      <span>{task.status}</span>
                      {task.title}
                    </li>
                  ))
                ) : (
                  <li>
                    <span>ready</span>
                    No tasks assigned to this role yet.
                  </li>
                )}
              </ul>
            </article>
          );
        })}
      </div>
    </section>
  );
}
