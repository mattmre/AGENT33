import type { DomainConfig } from "../../types";

export const trainingDomain: DomainConfig = {
  id: "training",
  title: "Training",
  description: "Rollout, optimization, metrics, reverts.",
  operations: [
    {
      id: "training-rollout",
      title: "Run Rollout",
      method: "POST",
      path: "/v1/training/{agent}/rollout",
      description: "Start rollout for agent.",
      defaultPathParams: {
        agent: "orchestrator"
      },
      defaultBody: JSON.stringify(
        {
          prompt: "Improve reliability"
        },
        null,
        2
      )
    },
    {
      id: "training-optimize",
      title: "Optimize Agent",
      method: "POST",
      path: "/v1/training/{agent}/optimize",
      description: "Run optimization pass.",
      defaultPathParams: {
        agent: "orchestrator"
      },
      defaultBody: "{}"
    },
    {
      id: "training-rollouts",
      title: "List Rollouts",
      method: "GET",
      path: "/v1/training/{agent}/rollouts",
      description: "List rollouts for agent.",
      defaultPathParams: {
        agent: "orchestrator"
      }
    },
    {
      id: "training-metrics",
      title: "Training Metrics",
      method: "GET",
      path: "/v1/training/{agent}/metrics",
      description: "Training metrics for agent.",
      defaultPathParams: {
        agent: "orchestrator"
      }
    },
    {
      id: "training-revert",
      title: "Revert Agent",
      method: "POST",
      path: "/v1/training/{agent}/revert",
      description: "Revert agent to previous state.",
      defaultPathParams: {
        agent: "orchestrator"
      },
      defaultBody: "{}"
    }
  ]
};
