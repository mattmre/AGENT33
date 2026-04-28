import { useState } from "react";

import type { PermissionModeId } from "../data/permissionModes";
import { getPermissionMode } from "../data/permissionModes";
import type { WorkspaceSessionSummary } from "../data/workspaces";

const DRAWER_SECTIONS = [
  {
    id: "plan",
    label: "Plan",
    title: "Plan artifact",
    body: "Checklist, assumptions, risks, and validation commands will appear here before execution."
  },
  {
    id: "commands",
    label: "Command Blocks",
    title: "Command blocks",
    body: "Tool and command runs will be grouped with source agent, status, duration, and redaction state."
  },
  {
    id: "logs",
    label: "Logs",
    title: "Run logs",
    body: "Readable logs will summarize important output instead of forcing users into terminal walls."
  },
  {
    id: "tests",
    label: "Tests",
    title: "Validation evidence",
    body: "Test, lint, build, and smoke results will show pass/fail status and next repair action."
  },
  {
    id: "risks",
    label: "Risks",
    title: "Risk register",
    body: "Known blockers, secrets warnings, destructive actions, and uncertainty notes will collect here."
  },
  {
    id: "approval",
    label: "Approval",
    title: "Approval gate",
    body: "Permission requests will explain what runs, why it is needed, and what can be safely skipped."
  },
  {
    id: "activity",
    label: "Activity / Mailbox",
    title: "Agent mailbox",
    body: "Coordinator, Builder, Scout, and Reviewer handoffs will be typed events, not transcript noise."
  },
  {
    id: "outcome",
    label: "Outcome",
    title: "Done state",
    body: "Completed sessions should end as PR ready, artifact package ready, or blocked with a clear action."
  }
] as const;

type DrawerSectionId = (typeof DRAWER_SECTIONS)[number]["id"];

interface ArtifactReviewDrawerProps {
  workspace: WorkspaceSessionSummary;
  permissionModeId: PermissionModeId;
}

export function ArtifactReviewDrawer({
  workspace,
  permissionModeId
}: ArtifactReviewDrawerProps): JSX.Element {
  const [activeSectionId, setActiveSectionId] = useState<DrawerSectionId>("plan");
  const activeSection = DRAWER_SECTIONS.find((section) => section.id === activeSectionId) ?? DRAWER_SECTIONS[0];
  const permissionMode = getPermissionMode(permissionModeId);
  const activeTabId = `artifact-drawer-tab-${activeSection.id}`;

  return (
    <aside className="artifact-review-drawer" aria-label="Artifact and review drawer">
      <header>
        <span className="eyebrow">Review drawer</span>
        <h2>{workspace.template}</h2>
        <p>{permissionMode.label}: {permissionMode.allowedNow}</p>
      </header>

      <div className="artifact-drawer-tabs" role="tablist" aria-label="Artifact drawer sections">
        {DRAWER_SECTIONS.map((section) => (
          <button
            key={section.id}
            id={`artifact-drawer-tab-${section.id}`}
            type="button"
            role="tab"
            className={section.id === activeSectionId ? "active" : ""}
            aria-controls="artifact-drawer-panel"
            aria-selected={section.id === activeSectionId}
            onClick={() => setActiveSectionId(section.id)}
          >
            {section.label}
          </button>
        ))}
      </div>

      <article
        id="artifact-drawer-panel"
        className="artifact-drawer-panel"
        role="tabpanel"
        aria-labelledby={activeTabId}
        aria-live="polite"
      >
        <span>{activeSection.label}</span>
        <h3>{activeSection.title}</h3>
        <p>{activeSection.body}</p>
        <dl>
          <div>
            <dt>Workspace</dt>
            <dd>{workspace.name}</dd>
          </div>
          <div>
            <dt>Current status</dt>
            <dd>{workspace.status}</dd>
          </div>
          <div>
            <dt>Review gate</dt>
            <dd>{permissionMode.reviewGate}</dd>
          </div>
        </dl>
      </article>
    </aside>
  );
}
