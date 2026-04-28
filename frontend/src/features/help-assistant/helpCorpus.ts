import type { HelpArticle } from "./types";

export const HELP_ARTICLES: HelpArticle[] = [
  {
    id: "connect-openrouter",
    title: "Connect OpenRouter",
    audience: "New user setting up the first cloud model",
    summary:
      "Use the Models page to save an OpenRouter key, keep the base URL on the standard endpoint, choose a default model, and run the probe before launching workflows.",
    body: [
      "OpenRouter is the recommended cloud-model starting path because one key can route to many model providers.",
      "AGENT33 stores provider settings through the existing operator config flow. The UI never needs to show a stored secret back to you.",
      "For environment-based setup, use OPENROUTER_API_KEY for the key, OPENROUTER_BASE_URL=https://openrouter.ai/api/v1 for the endpoint, and DEFAULT_MODEL=openrouter/auto or the recommended stable default shown in Models."
    ],
    steps: [
      "Open Start > Models.",
      "Paste your OpenRouter API key into the provider key field.",
      "Keep the base URL as https://openrouter.ai/api/v1 unless you are using a compatible gateway.",
      "Choose the recommended default model or enter DEFAULT_MODEL=openrouter/auto.",
      "Save settings, then run Test connection before using Workflow Catalog."
    ],
    keywords: [
      "openrouter",
      "model",
      "provider",
      "api key",
      "openrouter_api_key",
      "openrouter_base_url",
      "default_model",
      "connect",
      "setup"
    ],
    sources: [
      { label: "Model Connection Wizard", path: "frontend/src/features/model-connection/ModelConnectionWizardPanel.tsx" },
      { label: "OpenRouter config helpers", path: "frontend/src/features/model-connection/helpers.ts" },
      { label: "Engine environment example", path: "engine/.env.example" },
      { label: "Setup guide", path: "docs/setup-guide.md" }
    ],
    actions: [
      { label: "Open Models", target: "models" },
      { label: "Browse workflows after setup", target: "catalog" }
    ]
  },
  {
    id: "start-docker",
    title: "Start or refresh Docker",
    audience: "Local user running AGENT33 with Docker Desktop",
    summary:
      "Run Docker Compose from the engine folder, rebuild when code changes, then open the frontend and verify API health.",
    body: [
      "The AGENT33 stack is launched from engine/docker-compose.yml, not the repository root.",
      "The frontend is exposed on http://localhost:3000 and the API health check is exposed on http://localhost:8000/health.",
      "When updating to the latest code, rebuild the api and frontend images and recreate containers so the browser sees the new UI."
    ],
    steps: [
      "Open a terminal in the repo worktree.",
      "Run cd engine.",
      "Run docker compose -p engine up -d --build --remove-orphans.",
      "Open http://localhost:3000.",
      "Verify http://localhost:8000/health returns a 200 response."
    ],
    keywords: [
      "docker",
      "docker desktop",
      "compose",
      "localhost",
      "frontend",
      "health",
      "refresh",
      "rebuild"
    ],
    sources: [
      { label: "Setup guide", path: "docs/setup-guide.md" },
      { label: "Docker compose", path: "engine/docker-compose.yml" },
      { label: "Frontend Dockerfile", path: "frontend/Dockerfile" }
    ],
    actions: [
      { label: "Open Start", target: "start" },
      { label: "Open Operations Hub", target: "operations" }
    ]
  },
  {
    id: "first-workflow",
    title: "Run a first workflow",
    audience: "Beginner trying to get a useful outcome",
    summary:
      "Start with Workflow Catalog, pick a review-gated workflow, and let Workflow Starter turn it into an editable plan before anything runs.",
    body: [
      "Workflow Catalog is the beginner-safe path for prebuilt outcomes. It shows audience, deliverables, expected time, prerequisites, and safety posture.",
      "Workflow Starter receives an editable draft from catalog cards so you can adjust the goal and output before launching.",
      "Review-gated workflows are safer for first use because they ask for confirmation before moving from planning into action."
    ],
    steps: [
      "Open Build > Workflow Catalog.",
      "Search for an outcome like landing page, repo analysis, competitive research, or SaaS scaffold.",
      "Choose Use this workflow.",
      "Review the drafted goal and expected output in Workflow Starter.",
      "Launch only after model readiness and safety expectations are clear."
    ],
    keywords: [
      "workflow",
      "catalog",
      "starter",
      "first run",
      "prebuilt",
      "template",
      "outcome",
      "beginner"
    ],
    sources: [
      { label: "Workflow Catalog", path: "frontend/src/features/workflow-catalog/WorkflowCatalogPanel.tsx" },
      { label: "Outcome workflow catalog", path: "frontend/src/features/outcome-home/catalog.ts" },
      { label: "UX backlog workflow items", path: "docs/research/ux-overhaul-backlog-2026-04-27.md" }
    ],
    actions: [
      { label: "Open Workflow Catalog", target: "catalog" },
      { label: "Open Workflow Starter", target: "starter" }
    ]
  },
  {
    id: "what-is-safe-mode",
    title: "Beginner mode vs Pro mode",
    audience: "User worried about destructive controls",
    summary:
      "Beginner mode keeps raw API/domain controls quarantined and routes you to safer pages for models, workflows, safety, and operations.",
    body: [
      "Beginner mode is the default. It hides raw endpoint forms because they are powerful and easy to misuse.",
      "Pro mode is still available for operators who need direct domain operations, endpoint search, and raw request tools.",
      "If a page shows raw JSON or endpoint language, use the safer route cards first unless you know exactly what the operation changes."
    ],
    steps: [
      "Keep Mode set to Beginner for normal setup and workflow work.",
      "Use Models, Workflow Catalog, Safety Center, and Operations Hub for guided actions.",
      "Only unlock Pro mode when you need raw domain operations.",
      "Return to Beginner mode after technical inspection."
    ],
    keywords: [
      "beginner",
      "pro",
      "advanced",
      "raw",
      "safe",
      "destructive",
      "control plane",
      "endpoint"
    ],
    sources: [
      { label: "Advanced quarantine", path: "frontend/src/features/advanced/AdvancedControlPlanePanel.tsx" },
      { label: "UX session log", path: "docs/sessions/session-133-2026-04-27-ux-overhaul.md" }
    ],
    actions: [
      { label: "Open Safety Center", target: "safety" },
      { label: "Open Advanced", target: "advanced" }
    ]
  },
  {
    id: "mcp-tools-skills",
    title: "Understand MCP, tools, and skills",
    audience: "User confused by platform vocabulary",
    summary:
      "Think of models as the brain, tools as actions, MCP as external tool connections, skills as packaged know-how, and workflows as the step-by-step plan.",
    body: [
      "A model generates reasoning and text. A tool performs a specific action. MCP connects AGENT33 to external tool servers.",
      "A skill packages instructions, workflows, and reusable operating knowledge. A workflow combines goals, tools, skills, safety gates, and outputs.",
      "If you are not sure where to start, pick a workflow first. AGENT33 should tell you which model, tools, and skills that workflow needs."
    ],
    steps: [
      "Open Workflow Catalog if you know your desired outcome.",
      "Open MCP Health if a tool server is not available.",
      "Open Tool Fabric to discover or sync tools.",
      "Open Skill Wizard only when you want to author or install a reusable skill."
    ],
    keywords: [
      "mcp",
      "tool",
      "skills",
      "skill",
      "workflow",
      "model",
      "fabric",
      "glossary"
    ],
    sources: [
      { label: "MCP Health", path: "frontend/src/features/mcp-health/McpHealthPanel.tsx" },
      { label: "Tool Fabric", path: "frontend/src/features/tool-fabric/ToolFabricPanel.tsx" },
      { label: "Skill Wizard", path: "frontend/src/features/skill-wizard/SkillWizardPanel.tsx" }
    ],
    actions: [
      { label: "Open MCP Health", target: "mcp" },
      { label: "Open Workflow Catalog", target: "catalog" }
    ]
  }
];
