import type { DomainConfig } from "../../types";

export const workflowsDomain: DomainConfig = {
  id: "workflows",
  title: "Workflows",
  description: "Workflow registry, execution, and scheduling orchestration.",
  operations: [
    {
      id: "workflows-list",
      title: "List Workflows",
      method: "GET",
      path: "/v1/workflows/",
      description: "List workflow definitions."
    },
    {
      id: "workflows-get",
      title: "Get Workflow",
      method: "GET",
      path: "/v1/workflows/{name}",
      description: "Get workflow details.",
      defaultPathParams: {
        name: "hello-flow"
      }
    },
    {
      id: "workflows-create",
      title: "Create Workflow",
      method: "POST",
      path: "/v1/workflows/",
      description: "Register a workflow definition.",
      defaultBody: JSON.stringify(
        {
          name: "hello-flow",
          version: "1.0.0",
          description: "Simple flow",
          triggers: { manual: true },
          inputs: {
            name: { type: "string", required: true }
          },
          outputs: {
            message: { type: "string" }
          },
          steps: [
            {
              id: "step-1",
              action: "transform",
              inputs: { template: { message: "Hello {{ name }}" } }
            }
          ],
          execution: { mode: "sequential" }
        },
        null,
        2
      )
    },
    {
      id: "workflows-execute",
      title: "Execute Workflow",
      method: "POST",
      path: "/v1/workflows/{name}/execute",
      description: "Execute a registered workflow.",
      defaultPathParams: {
        name: "hello-flow"
      },
      defaultBody: JSON.stringify(
        {
          inputs: {
            name: "AGENT-33"
          }
        },
        null,
        2
      ),
      uxHint: "workflow-execute"
    },
    {
      id: "workflows-schedule-create",
      title: "Schedule Workflow",
      method: "POST",
      path: "/v1/workflows/{name}/schedule",
      description: "Create repeating cron/interval execution for a workflow.",
      defaultPathParams: {
        name: "hello-flow"
      },
      defaultBody: JSON.stringify(
        {
          interval_seconds: 900,
          inputs: {
            name: "AGENT-33"
          }
        },
        null,
        2
      ),
      uxHint: "workflow-schedule"
    },
    {
      id: "workflows-schedule-list",
      title: "List Schedules",
      method: "GET",
      path: "/v1/workflows/schedules",
      description: "List active workflow schedules."
    },
    {
      id: "workflows-schedule-delete",
      title: "Delete Schedule",
      method: "DELETE",
      path: "/v1/workflows/schedules/{job_id}",
      description: "Delete a schedule by job ID.",
      defaultPathParams: {
        job_id: "replace-with-job-id"
      }
    },
    {
      id: "workflows-history",
      title: "Workflow History",
      method: "GET",
      path: "/v1/workflows/{name}/history",
      description: "Recent execution history for a workflow.",
      defaultPathParams: {
        name: "hello-flow"
      }
    },
    {
      id: "workflows-graph",
      title: "Workflow Graph",
      method: "GET",
      path: "/v1/visualizations/workflows/{workflow_id}/graph",
      description: "Get workflow graph visualization data.",
      defaultPathParams: {
        workflow_id: "hello-flow"
      },
      uxHint: "workflow-graph"
    }
  ]
};
