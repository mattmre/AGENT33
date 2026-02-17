import type { DomainConfig } from "../../types";

export const explanationsDomain: DomainConfig = {
  id: "explanations",
  title: "Explanations",
  description: "Generate and manage explanations with fact-check validation.",
  operations: [
    {
      id: "explanations-create",
      title: "Create Explanation",
      method: "POST",
      path: "/v1/explanations/",
      description: "Generate a new explanation for an entity.",
      defaultBody: JSON.stringify(
        {
          entity_type: "workflow",
          entity_id: "hello-flow",
          metadata: {
            model: "llama3.1"
          }
        },
        null,
        2
      )
    },
    {
      id: "explanations-get",
      title: "Get Explanation",
      method: "GET",
      path: "/v1/explanations/{explanation_id}",
      description: "Retrieve an explanation by ID.",
      defaultPathParams: {
        explanation_id: "expl-abc123"
      }
    },
    {
      id: "explanations-list",
      title: "List Explanations",
      method: "GET",
      path: "/v1/explanations/",
      description: "List all explanations with optional filters."
    },
    {
      id: "explanations-list-by-entity",
      title: "List by Entity",
      method: "GET",
      path: "/v1/explanations/",
      description: "List explanations filtered by entity.",
      defaultQuery: {
        entity_type: "workflow",
        entity_id: "hello-flow"
      }
    },
    {
      id: "explanations-delete",
      title: "Delete Explanation",
      method: "DELETE",
      path: "/v1/explanations/{explanation_id}",
      description: "Delete an explanation.",
      defaultPathParams: {
        explanation_id: "expl-abc123"
      }
    }
  ]
};
