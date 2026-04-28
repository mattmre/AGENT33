import { useMemo } from "react";

import type { WorkspaceSessionSummary } from "../data/workspaces";
import {
  WORKSPACE_TASK_STATUS_LABELS,
  WORKSPACE_TASK_STATUSES,
  getWorkspaceBoard,
  groupWorkspaceTasksByStatus
} from "../data/workspaceBoard";

interface WorkspaceTaskBoardProps {
  workspace: WorkspaceSessionSummary;
  onOpenSafety: () => void;
  onOpenWorkflows: () => void;
}

export function WorkspaceTaskBoard({
  workspace,
  onOpenSafety,
  onOpenWorkflows
}: WorkspaceTaskBoardProps): JSX.Element {
  const board = getWorkspaceBoard(workspace.id);
  const tasksByStatus = useMemo(() => groupWorkspaceTasksByStatus(board.tasks), [board.tasks]);

  return (
    <section className="workspace-board" aria-label={`${workspace.name} task board`}>
      <header className="workspace-board-header">
        <div>
          <span className="eyebrow">Workspace command board</span>
          <h2>{workspace.template}</h2>
          <p>{workspace.goal}</p>
        </div>
        <div className="workspace-board-actions" aria-label="Workspace board actions">
          <button type="button" onClick={onOpenWorkflows}>
            Choose workflow
          </button>
          <button type="button" onClick={onOpenSafety}>
            Review approvals
          </button>
        </div>
      </header>

      <div className="workspace-board-grid">
        <div className="workspace-kanban" aria-label="Workspace task lanes">
          {WORKSPACE_TASK_STATUSES.map((status) => {
            const laneTasks = tasksByStatus[status];
            return (
              <section key={status} className="workspace-kanban-lane" aria-label={`${WORKSPACE_TASK_STATUS_LABELS[status]} tasks`}>
                <div className="workspace-lane-header">
                  <h3>{WORKSPACE_TASK_STATUS_LABELS[status]}</h3>
                  <span>{laneTasks.length}</span>
                </div>
                {laneTasks.length === 0 ? (
                  <p className="workspace-empty-lane">No tasks yet.</p>
                ) : null}
                {laneTasks.map((task) => (
                  <article key={task.id} className={`workspace-task-card workspace-task-card--${task.status}`}>
                    <span>{task.ownerRole}</span>
                    <h4>{task.title}</h4>
                    <p>{task.outcome}</p>
                  </article>
                ))}
              </section>
            );
          })}
        </div>

        <aside className="workspace-agent-roster" aria-label="Workspace agent roster">
          <div className="workspace-roster-header">
            <h3>Agent roster</h3>
            <p>BridgeSpace-style roles for this workspace template.</p>
          </div>
          {board.agents.map((agent) => (
            <article key={agent.id} className="workspace-agent-card">
              <div>
                <strong>{agent.name}</strong>
                <span>{agent.role}</span>
              </div>
              <p>{agent.focus}</p>
              <small>{agent.state}</small>
            </article>
          ))}
        </aside>
      </div>
    </section>
  );
}
