import type { DomainConfig } from "../../types";

export const workflowsDomain: DomainConfig = {
  id: "workflows",
  title: "Workflows",
  description: "Workflow registry and execution.",
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
      )
    }
  ]
};
