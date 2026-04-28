import { DEFAULT_APP_TAB, isAppTab, type AppTab } from "../data/navigation";
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

export const ARTIFACT_DRAWER_SECTION_IDS = [
  "plan",
  "commands",
  "logs",
  "tests",
  "risks",
  "approval",
  "activity",
  "outcome"
] as const;

export type ArtifactDrawerSectionId = (typeof ARTIFACT_DRAWER_SECTION_IDS)[number];

export interface CockpitUrlState {
  readonly activeTab: AppTab;
  readonly workspaceId: WorkspaceSessionId;
  readonly permissionModeId: PermissionModeId;
  readonly drawerSectionId: ArtifactDrawerSectionId;
}

export const DEFAULT_ARTIFACT_DRAWER_SECTION_ID: ArtifactDrawerSectionId = "plan";

const ARTIFACT_DRAWER_SECTION_ID_SET = new Set<string>(ARTIFACT_DRAWER_SECTION_IDS);

export function isArtifactDrawerSectionId(value: string | null): value is ArtifactDrawerSectionId {
  return value !== null && ARTIFACT_DRAWER_SECTION_ID_SET.has(value);
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
    drawerSectionId: isArtifactDrawerSectionId(requestedDrawerSectionId)
      ? requestedDrawerSectionId
      : fallbackState.drawerSectionId ?? DEFAULT_ARTIFACT_DRAWER_SECTION_ID
  };
}

export function createCockpitUrl(baseUrl: string, state: CockpitUrlState): string {
  const url = new URL(baseUrl);

  url.searchParams.set(COCKPIT_URL_VIEW_PARAM, state.activeTab);
  url.searchParams.set(COCKPIT_URL_WORKSPACE_PARAM, state.workspaceId);
  url.searchParams.set(COCKPIT_URL_PERMISSION_PARAM, state.permissionModeId);

  if (state.activeTab === "operations") {
    url.searchParams.set(COCKPIT_URL_DRAWER_PARAM, state.drawerSectionId);
  } else {
    url.searchParams.delete(COCKPIT_URL_DRAWER_PARAM);
  }

  return `${url.pathname}${url.search}${url.hash}`;
}
