import type { DomainConfig } from "../../types";

export const chatDomain: DomainConfig = {
  id: "chat",
  title: "Chat",
  description: "LLM chat completions.",
  operations: [
    {
      id: "chat-completions",
      title: "Chat Completion",
      method: "POST",
      path: "/v1/chat/completions",
      description: "OpenAI-compatible chat completion.",
      defaultBody: JSON.stringify(
        {
          model: "qwen3-coder:30b",
          messages: [{ role: "user", content: "Summarize AGENT-33 status." }],
          temperature: 0.2
        },
        null,
        2
      )
    }
  ]
};
