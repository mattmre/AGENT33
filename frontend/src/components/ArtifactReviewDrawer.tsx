import { useRef, useState, type KeyboardEvent } from "react";

import type { PermissionModeId } from "../data/permissionModes";
import { getPermissionMode } from "../data/permissionModes";
import type { WorkspaceSessionSummary } from "../data/workspaces";
import {
  ARTIFACT_DRAWER_SECTIONS,
  type ArtifactDrawerSectionId
} from "../data/artifactDrawerSections";

type ArtifactReviewDrawerBaseProps = {
  workspace: WorkspaceSessionSummary;
  permissionModeId: PermissionModeId;
};

type ArtifactReviewDrawerControlledProps = ArtifactReviewDrawerBaseProps & {
  activeSectionId: ArtifactDrawerSectionId;
  onSectionChange: (sectionId: ArtifactDrawerSectionId) => void;
};

type ArtifactReviewDrawerUncontrolledProps = ArtifactReviewDrawerBaseProps & {
  activeSectionId?: undefined;
  onSectionChange?: (sectionId: ArtifactDrawerSectionId) => void;
};

type ArtifactReviewDrawerProps = ArtifactReviewDrawerControlledProps | ArtifactReviewDrawerUncontrolledProps;

export function ArtifactReviewDrawer({
  workspace,
  permissionModeId,
  activeSectionId: controlledActiveSectionId,
  onSectionChange
}: ArtifactReviewDrawerProps): JSX.Element {
  const [uncontrolledActiveSectionId, setUncontrolledActiveSectionId] = useState<ArtifactDrawerSectionId>("plan");
  const activeSectionId = controlledActiveSectionId ?? uncontrolledActiveSectionId;
  const tabRefs = useRef<Record<string, HTMLButtonElement | null>>({});
  const activeSection =
    ARTIFACT_DRAWER_SECTIONS.find((section) => section.id === activeSectionId) ?? ARTIFACT_DRAWER_SECTIONS[0];
  const permissionMode = getPermissionMode(permissionModeId);
  const activeTabId = `artifact-drawer-tab-${activeSection.id}`;

  function selectSection(sectionId: ArtifactDrawerSectionId, shouldFocus = false): void {
    if (controlledActiveSectionId === undefined) {
      setUncontrolledActiveSectionId(sectionId);
    }
    onSectionChange?.(sectionId);
    if (shouldFocus) {
      window.requestAnimationFrame(() => tabRefs.current[sectionId]?.focus());
    }
  }

  function onTabKeyDown(event: KeyboardEvent<HTMLButtonElement>, sectionIndex: number): void {
    let nextIndex: number | null = null;

    if (event.key === "ArrowRight" || event.key === "ArrowDown") {
      nextIndex = (sectionIndex + 1) % ARTIFACT_DRAWER_SECTIONS.length;
    } else if (event.key === "ArrowLeft" || event.key === "ArrowUp") {
      nextIndex = (sectionIndex - 1 + ARTIFACT_DRAWER_SECTIONS.length) % ARTIFACT_DRAWER_SECTIONS.length;
    } else if (event.key === "Home") {
      nextIndex = 0;
    } else if (event.key === "End") {
      nextIndex = ARTIFACT_DRAWER_SECTIONS.length - 1;
    }

    if (nextIndex !== null) {
      event.preventDefault();
      selectSection(ARTIFACT_DRAWER_SECTIONS[nextIndex].id, true);
    }
  }

  return (
    <aside className="artifact-review-drawer" aria-label="Artifact and review drawer">
      <header>
        <span className="eyebrow">Review drawer</span>
        <h2>{workspace.template}</h2>
        <p>{permissionMode.label}: {permissionMode.allowedNow}</p>
      </header>

      <div className="artifact-drawer-tabs" role="tablist" aria-label="Artifact drawer sections">
        {ARTIFACT_DRAWER_SECTIONS.map((section, sectionIndex) => (
          <button
            key={section.id}
            id={`artifact-drawer-tab-${section.id}`}
            ref={(element) => {
              tabRefs.current[section.id] = element;
            }}
            type="button"
            role="tab"
            className={section.id === activeSectionId ? "active" : ""}
            aria-controls="artifact-drawer-panel"
            aria-selected={section.id === activeSectionId}
            tabIndex={section.id === activeSectionId ? 0 : -1}
            onClick={() => selectSection(section.id)}
            onKeyDown={(event) => onTabKeyDown(event, sectionIndex)}
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
