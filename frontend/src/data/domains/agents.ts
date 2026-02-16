import type { DomainConfig } from "../../types";

export const agentsDomain: DomainConfig = {
  id: "agents",
  title: "Agents",
  description: "Agent registry, search, details, invoke.",
  operations: [
    {
      id: "agents-catalog",
      title: "Capabilities Catalog",
      method: "GET",
      path: "/v1/agents/capabilities/catalog",
      description: "Agent capabilities catalog."
    },
    {
      id: "agents-search",
      title: "Search Agents",
      method: "GET",
      path: "/v1/agents/search",
      description: "Search by role/tags.",
      defaultQuery: {
        role: "orchestrator"
      }
    },
    {
      id: "agents-by-id",
      title: "Get Agent by ID",
      method: "GET",
      path: "/v1/agents/by-id/{agent_id}",
      description: "Fetch agent by identifier.",
      defaultPathParams: {
        agent_id: "AGT-001"
      }
    },
    {
      id: "agents-list",
      title: "List Agents",
      method: "GET",
      path: "/v1/agents/",
      description: "List all registered agents."
    },
    {
      id: "agents-get",
      title: "Get Agent by Name",
      method: "GET",
      path: "/v1/agents/{name}",
      description: "Fetch agent definition by name.",
      defaultPathParams: {
        name: "orchestrator"
      }
    },
    {
      id: "agents-create",
      title: "Create Agent",
      method: "POST",
      path: "/v1/agents/",
      description: "Register a new agent definition.",
      defaultBody: JSON.stringify(
        {
          name: "demo-agent",
          version: "1.0.0",
          role: "worker",
          description: "Demo worker",
          capabilities: [],
          inputs: {},
          outputs: {},
          constraints: {
            max_tokens: 2048,
            timeout_seconds: 120,
            max_retries: 2,
            parallel_allowed: true
          }
        },
        null,
        2
      )
    },
    {
      id: "agents-invoke",
      title: "Invoke Agent",
      method: "POST",
      path: "/v1/agents/{name}/invoke",
      description: "Run an agent by name.",
      defaultPathParams: {
        name: "orchestrator"
      },
      defaultBody: JSON.stringify(
        {
          inputs: {
            task: "Generate a short implementation plan."
          },
          model: "qwen3-coder:30b",
          temperature: 0.2
        },
        null,
        2
      )
    },
    {
      id: "agents-invoke-iterative",
      title: "Invoke Agent (Iterative)",
      method: "POST",
      path: "/v1/agents/{name}/invoke-iterative",
      description: "Iterative tool-use loop invocation for autonomous problem solving.",
      defaultPathParams: {
        name: "orchestrator"
      },
      defaultBody: JSON.stringify(
        {
          inputs: {
            task: "Iteratively solve and validate a workflow execution plan."
          },
          model: "qwen3-coder:30b",
          temperature: 0.2,
          max_iterations: 8,
          max_tool_calls_per_iteration: 4,
          enable_double_confirmation: true
        },
        null,
        2
      ),
      uxHint: "agent-iterative"
    }
  ]
};
