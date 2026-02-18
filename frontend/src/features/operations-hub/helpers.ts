import type { OperationsHubProcessDetail, OperationsHubProcessSummary } from "./types";

function normalizeStatus(status: string): string {
  return status.trim().toLowerCase();
}

export function getStatusClass(status: string): string {
  const normalized = normalizeStatus(status);
  if (normalized === "running" || normalized === "active") {
    return "status-running";
  }
  if (normalized === "paused" || normalized === "suspended") {
    return "status-paused";
  }
  if (normalized === "pending" || normalized === "draft") {
    return "status-pending";
  }
  if (normalized === "cancelled" || normalized === "expired") {
    return "status-cancelled";
  }
  if (normalized === "completed" || normalized === "success" || normalized === "verified") {
    return "status-ok";
  }
  if (normalized === "failed" || normalized === "error" || normalized === "rejected") {
    return "status-error";
  }
  return "status-pending";
}

export function getStatusLabel(status: string): string {
  const text = status.replace(/[_-]+/g, " ").trim();
  if (text === "") {
    return "Unknown";
  }
  return text
    .split(" ")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

export function filterAndSortProcesses(
  processes: OperationsHubProcessSummary[],
  statusFilter: string,
  textFilter: string
): OperationsHubProcessSummary[] {
  const normalizedStatusFilter = normalizeStatus(statusFilter);
  const normalizedTextFilter = textFilter.trim().toLowerCase();

  return [...processes]
    .filter((process) => {
      if (normalizedStatusFilter === "all" || normalizedStatusFilter === "") {
        return true;
      }
      return normalizeStatus(process.status) === normalizedStatusFilter;
    })
    .filter((process) => {
      if (normalizedTextFilter === "") {
        return true;
      }
      return (
        process.name.toLowerCase().includes(normalizedTextFilter) ||
        process.id.toLowerCase().includes(normalizedTextFilter) ||
        process.type.toLowerCase().includes(normalizedTextFilter)
      );
    })
    .sort((left, right) => {
      return new Date(right.started_at).getTime() - new Date(left.started_at).getTime();
    });
}

export function canPause(detail: OperationsHubProcessDetail): boolean {
  return detail.type === "autonomy_budget" && normalizeStatus(detail.status) === "active";
}

export function canResume(detail: OperationsHubProcessDetail): boolean {
  return detail.type === "autonomy_budget" && normalizeStatus(detail.status) === "suspended";
}

export function canCancel(detail: OperationsHubProcessDetail): boolean {
  const normalized = normalizeStatus(detail.status);
  if (detail.type === "trace") {
    return normalized === "running";
  }
  if (detail.type === "autonomy_budget") {
    return normalized === "active" || normalized === "suspended" || normalized === "draft";
  }
  return false;
}

export function formatTimestamp(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString();
}
