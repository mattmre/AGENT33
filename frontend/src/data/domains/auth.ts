import type { DomainConfig } from "../../types";

export const authDomain: DomainConfig = {
  id: "auth",
  title: "Auth",
  description: "Token and API key operations.",
  operations: [
    {
      id: "auth-token",
      title: "Login Token",
      method: "POST",
      path: "/v1/auth/token",
      description: "Exchange username/password for JWT.",
      defaultBody: JSON.stringify(
        {
          username: "admin",
          password: "admin"
        },
        null,
        2
      )
    },
    {
      id: "auth-create-api-key",
      title: "Create API Key",
      method: "POST",
      path: "/v1/auth/api-keys",
      description: "Generate a scoped API key.",
      defaultBody: JSON.stringify(
        {
          subject: "agent-service",
          scopes: ["agents:read", "workflows:read"]
        },
        null,
        2
      )
    },
    {
      id: "auth-delete-api-key",
      title: "Delete API Key",
      method: "DELETE",
      path: "/v1/auth/api-keys/{key_id}",
      description: "Revoke an API key by ID.",
      defaultPathParams: {
        key_id: "replace-with-key-id"
      }
    }
  ]
};
