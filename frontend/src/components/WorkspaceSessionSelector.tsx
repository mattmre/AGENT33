import {
  WORKSPACE_SESSIONS,
  getWorkspaceSession,
  isWorkspaceSessionId,
  type WorkspaceSessionId
} from "../data/workspaces";

interface WorkspaceSessionSelectorProps {
  selectedWorkspaceId: WorkspaceSessionId;
  onSelectWorkspace: (workspaceId: WorkspaceSessionId) => void;
  onOpenRuns: () => void;
  onOpenWorkflows: () => void;
}

export function WorkspaceSessionSelector({
  selectedWorkspaceId,
  onSelectWorkspace,
  onOpenRuns,
  onOpenWorkflows
}: WorkspaceSessionSelectorProps): JSX.Element {
  const selectedWorkspace = getWorkspaceSession(selectedWorkspaceId);

  return (
    <section className="cockpit-sidebar-context workspace-session-card" aria-label="Workspace session">
      <div className="workspace-session-heading">
        <span className="eyebrow">Workspace</span>
        <strong>{selectedWorkspace.name}</strong>
      </div>

      <label className="workspace-session-select-label" htmlFor="workspace-session-select">
        Active project template
      </label>
      <select
        id="workspace-session-select"
        className="workspace-session-select"
        value={selectedWorkspaceId}
        onChange={(event) => {
          const workspaceId = event.target.value;
          if (!isWorkspaceSessionId(workspaceId)) {
            console.error(`Unknown workspace session: ${workspaceId}`);
            return;
          }
          onSelectWorkspace(workspaceId);
        }}
      >
        {WORKSPACE_SESSIONS.map((workspace) => (
          <option key={workspace.id} value={workspace.id}>
            {workspace.name} - {workspace.template}
          </option>
        ))}
      </select>

      <p>{selectedWorkspace.goal}</p>

      <dl className="workspace-session-stats" aria-label="Workspace snapshot">
        <div>
          <dt>Status</dt>
          <dd>{selectedWorkspace.status}</dd>
        </div>
        <div>
          <dt>Agents</dt>
          <dd>{selectedWorkspace.agents}</dd>
        </div>
        <div>
          <dt>Tasks</dt>
          <dd>{selectedWorkspace.tasks}</dd>
        </div>
      </dl>

      <div className="workspace-session-actions" aria-label="Workspace quick actions">
        <button type="button" onClick={onOpenWorkflows}>
          Open workflows
        </button>
        <button type="button" onClick={onOpenRuns}>
          View runs
        </button>
      </div>

      <small>{selectedWorkspace.updatedLabel}</small>
    </section>
  );
}
