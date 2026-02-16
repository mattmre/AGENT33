import type { DomainConfig } from "../../types";

export const healthDomain: DomainConfig = {
  id: "overview",
  title: "Health",
  description: "Cluster health and channel checks.",
  operations: [
    {
      id: "health",
      title: "System Health",
      method: "GET",
      path: "/health",
      description: "Aggregate service health."
    },
    {
      id: "health-channels",
      title: "Channel Health",
      method: "GET",
      path: "/health/channels",
      description: "Messaging channel adapters health."
    }
  ]
};
