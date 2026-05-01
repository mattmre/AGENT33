import { DEFAULT_APP_TAB, isAppTab, type AppTab } from "../data/navigation";
import {
  DEFAULT_ARTIFACT_DRAWER_SECTION_ID as DEFAULT_ARTIFACT_DRAWER_SECTION_ID_VALUE,
  isArtifactDrawerSectionId as isArtifactDrawerSectionIdValue,
  type ArtifactDrawerSectionId
} from "../data/artifactDrawerSections";
import {
  DEFAULT_PERMISSION_MODE_ID,
  isPermissionModeId,
  type PermissionModeId
} from "../data/permissionModes";
import {
  DEFAULT_WORKSPACE_SESSION_ID,
  isWorkspaceSessionId,
  type WorkspaceSessionId
} from "../data/workspaces";

export const COCKPIT_URL_VIEW_PARAM = "view";
export const COCKPIT_URL_WORKSPACE_PARAM = "workspace";
export const COCKPIT_URL_PERMISSION_PARAM = "permission";
export const COCKPIT_URL_DRAWER_PARAM = "drawer";
export const COCKPIT_URL_OPERATOR_MODE_PARAM = "operatorMode";

export const COCKPIT_OPERATOR_MODES = ["beginner", "pro"] as const;
export type CockpitOperatorMode = (typeof COCKPIT_OPERATOR_MODES)[number];
export const DEFAULT_COCKPIT_OPERATOR_MODE: CockpitOperatorMode = "pro";

export {
  ARTIFACT_DRAWER_SECTION_IDS,
  DEFAULT_ARTIFACT_DRAWER_SECTION_ID,
  isArtifactDrawerSectionId
} from "../data/artifactDrawerSections";
export type { ArtifactDrawerSectionId } from "../data/artifactDrawerSections";

export interface CockpitUrlState {
  readonly activeTab: AppTab;
  readonly workspaceId: WorkspaceSessionId;
  readonly permissionModeId: PermissionModeId;
  readonly drawerSectionId: ArtifactDrawerSectionId;
  readonly operatorMode: CockpitOperatorMode;
}

export function isCockpitOperatorMode(value: string | null): value is CockpitOperatorMode {
  return value === "beginner" || value === "pro";
}

export function readCockpitUrlState(
  search: string,
  fallbackState: Partial<CockpitUrlState> = {}
): CockpitUrlState {
  const params = new URLSearchParams(search);
  const requestedTab = params.get(COCKPIT_URL_VIEW_PARAM);
  const requestedWorkspaceId = params.get(COCKPIT_URL_WORKSPACE_PARAM);
  const requestedPermissionModeId = params.get(COCKPIT_URL_PERMISSION_PARAM);
  const requestedDrawerSectionId = params.get(COCKPIT_URL_DRAWER_PARAM);
  const requestedOperatorMode = params.get(COCKPIT_URL_OPERATOR_MODE_PARAM);

  return {
    activeTab: requestedTab !== null && isAppTab(requestedTab)
      ? requestedTab
      : fallbackState.activeTab ?? DEFAULT_APP_TAB,
    workspaceId: isWorkspaceSessionId(requestedWorkspaceId)
      ? requestedWorkspaceId
      : fallbackState.workspaceId ?? DEFAULT_WORKSPACE_SESSION_ID,
    permissionModeId: isPermissionModeId(requestedPermissionModeId)
      ? requestedPermissionModeId
      : fallbackState.permissionModeId ?? DEFAULT_PERMISSION_MODE_ID,
    drawerSectionId: isArtifactDrawerSectionIdValue(requestedDrawerSectionId)
      ? requestedDrawerSectionId
      : fallbackState.drawerSectionId ?? DEFAULT_ARTIFACT_DRAWER_SECTION_ID_VALUE,
    operatorMode: isCockpitOperatorMode(requestedOperatorMode)
      ? requestedOperatorMode
      : fallbackState.operatorMode ?? DEFAULT_COCKPIT_OPERATOR_MODE
  };
}

export function createCockpitUrl(baseUrl: string, state: CockpitUrlState): string {
  const url = new URL(baseUrl);

  url.searchParams.set(COCKPIT_URL_VIEW_PARAM, state.activeTab);
  url.searchParams.set(COCKPIT_URL_WORKSPACE_PARAM, state.workspaceId);
  url.searchParams.set(COCKPIT_URL_PERMISSION_PARAM, state.permissionModeId);
  url.searchParams.set(COCKPIT_URL_OPERATOR_MODE_PARAM, state.operatorMode);

  if (state.activeTab === "operations") {
    url.searchParams.set(COCKPIT_URL_DRAWER_PARAM, state.drawerSectionId);
  } else {
    url.searchParams.delete(COCKPIT_URL_DRAWER_PARAM);
  }

  return `${url.pathname}${url.search}${url.hash}`;
}
