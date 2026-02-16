import type { DomainConfig } from "../../types";

export const improvementsDomain: DomainConfig = {
  id: "improvements",
  title: "Improvements",
  description: "Research intake, lessons, checklists, metrics, refreshes.",
  operations: [
    {
      id: "imp-intake-create",
      title: "Create Intake",
      method: "POST",
      path: "/v1/improvements/intakes",
      description: "Create improvement intake.",
      defaultBody: JSON.stringify(
        {
          source: "session",
          title: "UI parity backlog",
          details: "Need full UI parity with OpenClaw."
        },
        null,
        2
      )
    },
    {
      id: "imp-intake-list",
      title: "List Intakes",
      method: "GET",
      path: "/v1/improvements/intakes",
      description: "List intakes."
    },
    {
      id: "imp-intake-get",
      title: "Get Intake",
      method: "GET",
      path: "/v1/improvements/intakes/{intake_id}",
      description: "Get intake.",
      defaultPathParams: {
        intake_id: "replace-with-intake-id"
      }
    },
    {
      id: "imp-intake-transition",
      title: "Transition Intake",
      method: "POST",
      path: "/v1/improvements/intakes/{intake_id}/transition",
      description: "Transition intake state.",
      defaultPathParams: {
        intake_id: "replace-with-intake-id"
      },
      defaultBody: JSON.stringify(
        {
          to_state: "ready"
        },
        null,
        2
      )
    },
    {
      id: "imp-lesson-create",
      title: "Create Lesson",
      method: "POST",
      path: "/v1/improvements/lessons",
      description: "Create lesson.",
      defaultBody: JSON.stringify(
        {
          title: "Auth bootstrap must be explicit",
          root_cause: "No seeded users for login"
        },
        null,
        2
      )
    },
    {
      id: "imp-lesson-list",
      title: "List Lessons",
      method: "GET",
      path: "/v1/improvements/lessons",
      description: "List lessons."
    },
    {
      id: "imp-lesson-get",
      title: "Get Lesson",
      method: "GET",
      path: "/v1/improvements/lessons/{lesson_id}",
      description: "Get lesson.",
      defaultPathParams: {
        lesson_id: "replace-with-lesson-id"
      }
    },
    {
      id: "imp-lesson-complete-action",
      title: "Complete Lesson Action",
      method: "POST",
      path: "/v1/improvements/lessons/{lesson_id}/complete-action",
      description: "Mark lesson action complete.",
      defaultPathParams: {
        lesson_id: "replace-with-lesson-id"
      },
      defaultBody: JSON.stringify(
        {
          action_id: "ACT-01"
        },
        null,
        2
      )
    },
    {
      id: "imp-lesson-verify",
      title: "Verify Lesson",
      method: "POST",
      path: "/v1/improvements/lessons/{lesson_id}/verify",
      description: "Verify lesson effect.",
      defaultPathParams: {
        lesson_id: "replace-with-lesson-id"
      },
      defaultBody: "{}"
    },
    {
      id: "imp-checklist-create",
      title: "Create Checklist",
      method: "POST",
      path: "/v1/improvements/checklists",
      description: "Create checklist.",
      defaultBody: JSON.stringify(
        {
          name: "UI launch checklist",
          items: ["lint", "tests", "smoke"]
        },
        null,
        2
      )
    },
    {
      id: "imp-checklist-list",
      title: "List Checklists",
      method: "GET",
      path: "/v1/improvements/checklists",
      description: "List checklists."
    },
    {
      id: "imp-checklist-get",
      title: "Get Checklist",
      method: "GET",
      path: "/v1/improvements/checklists/{checklist_id}",
      description: "Get checklist.",
      defaultPathParams: {
        checklist_id: "replace-with-checklist-id"
      }
    },
    {
      id: "imp-checklist-complete",
      title: "Complete Checklist",
      method: "POST",
      path: "/v1/improvements/checklists/{checklist_id}/complete",
      description: "Complete checklist.",
      defaultPathParams: {
        checklist_id: "replace-with-checklist-id"
      },
      defaultBody: "{}"
    },
    {
      id: "imp-checklist-evaluate",
      title: "Evaluate Checklist",
      method: "GET",
      path: "/v1/improvements/checklists/{checklist_id}/evaluate",
      description: "Evaluate checklist quality.",
      defaultPathParams: {
        checklist_id: "replace-with-checklist-id"
      }
    },
    {
      id: "imp-metrics",
      title: "Latest Metrics",
      method: "GET",
      path: "/v1/improvements/metrics",
      description: "Get latest metrics."
    },
    {
      id: "imp-metrics-history",
      title: "Metrics History",
      method: "GET",
      path: "/v1/improvements/metrics/history",
      description: "Get metrics history."
    },
    {
      id: "imp-metrics-snapshot",
      title: "Save Metrics Snapshot",
      method: "POST",
      path: "/v1/improvements/metrics/snapshot",
      description: "Save a custom snapshot.",
      defaultBody: JSON.stringify(
        {
          period: "2026-02",
          metrics: []
        },
        null,
        2
      )
    },
    {
      id: "imp-metrics-default",
      title: "Create Default Snapshot",
      method: "POST",
      path: "/v1/improvements/metrics/default-snapshot",
      description: "Save canonical default snapshot.",
      defaultBody: "{}"
    },
    {
      id: "imp-metrics-trend",
      title: "Metrics Trend",
      method: "GET",
      path: "/v1/improvements/metrics/trend/{metric_id}",
      description: "Get trend for metric.",
      defaultPathParams: {
        metric_id: "IM-01"
      },
      defaultQuery: {
        periods: "6"
      }
    },
    {
      id: "imp-refresh-create",
      title: "Create Refresh",
      method: "POST",
      path: "/v1/improvements/refreshes",
      description: "Create roadmap refresh.",
      defaultBody: JSON.stringify(
        {
          title: "Phase 22 refresh"
        },
        null,
        2
      )
    },
    {
      id: "imp-refresh-list",
      title: "List Refreshes",
      method: "GET",
      path: "/v1/improvements/refreshes",
      description: "List refreshes."
    },
    {
      id: "imp-refresh-get",
      title: "Get Refresh",
      method: "GET",
      path: "/v1/improvements/refreshes/{refresh_id}",
      description: "Get refresh detail.",
      defaultPathParams: {
        refresh_id: "replace-with-refresh-id"
      }
    },
    {
      id: "imp-refresh-complete",
      title: "Complete Refresh",
      method: "POST",
      path: "/v1/improvements/refreshes/{refresh_id}/complete",
      description: "Complete refresh.",
      defaultPathParams: {
        refresh_id: "replace-with-refresh-id"
      },
      defaultBody: "{}"
    }
  ]
};
