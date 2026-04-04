/**
 * AgentBuilderPage: visual agent definition builder with capability toggles,
 * live system-prompt preview, inline testing, and JSON export.
 */

import { useCallback, useEffect, useRef, useState } from "react";

import { getRuntimeConfig } from "../../lib/api";
import type { AgentBuilderState, AgentDefinitionExport } from "../../types";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const AGENT_ROLES = [
  "orchestrator",
  "director",
  "implementer",
  "qa",
  "reviewer",
  "researcher",
  "documentation",
  "security",
  "architect",
  "test-engineer",
] as const;

interface CapabilityToggle {
  key: keyof Pick<
    AgentBuilderState,
    "canReadFiles" | "canWriteFiles" | "canSearchWeb" | "canRunCode" | "canCallAPIs"
  >;
  label: string;
  capability: string;
}

const CAPABILITY_TOGGLES: CapabilityToggle[] = [
  { key: "canReadFiles", label: "Can it read your files?", capability: "file-read" },
  { key: "canWriteFiles", label: "Can it write to your files?", capability: "file-write" },
  { key: "canSearchWeb", label: "Can it search the web?", capability: "web-search" },
  { key: "canRunCode", label: "Can it run code?", capability: "code-execution" },
  { key: "canCallAPIs", label: "Can it connect to external services?", capability: "api-calls" },
];

const NAME_PATTERN = /^[a-z][a-z0-9-]*$/;

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface AgentBuilderPageProps {
  apiUrl?: string;
  token: string | null;
  apiKey?: string | null;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function buildCapabilities(state: AgentBuilderState): string[] {
  const caps: string[] = [];
  for (const toggle of CAPABILITY_TOGGLES) {
    if (state[toggle.key]) {
      caps.push(toggle.capability);
    }
  }
  return caps;
}

function buildGovernance(state: AgentBuilderState) {
  const network = state.canCallAPIs
    ? "external"
    : state.canSearchWeb
      ? "external-read"
      : "none";
  return {
    scope: "workspace",
    network,
    approval_required: [] as string[],
    tool_policies: {} as Record<string, string>,
  };
}

function buildDefinitionPayload(state: AgentBuilderState) {
  return {
    name: state.name,
    version: state.version || "1.0.0",
    role: state.role,
    description: state.description,
    capabilities: buildCapabilities(state),
    inputs: {},
    outputs: {},
    governance: buildGovernance(state),
    autonomy_level:
      state.canWriteFiles || state.canRunCode ? "supervised" : "read-only",
  };
}

function buildExport(state: AgentBuilderState): AgentDefinitionExport {
  return {
    name: state.name,
    version: state.version || "1.0.0",
    role: state.role,
    description: state.description,
    capabilities: buildCapabilities(state),
    governance: buildGovernance(state),
    autonomy_level:
      state.canWriteFiles || state.canRunCode ? "supervised" : "read-only",
  };
}

function authHeaders(token: string | null, apiKey: string | null | undefined): Record<string, string> {
  const h: Record<string, string> = {
    "Content-Type": "application/json",
    Accept: "application/json",
  };
  if (token) h.Authorization = `Bearer ${token}`;
  if (apiKey) h["X-API-Key"] = apiKey;
  return h;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

const INITIAL_STATE: AgentBuilderState = {
  name: "",
  description: "",
  role: "implementer",
  version: "1.0.0",
  canReadFiles: false,
  canWriteFiles: false,
  canSearchWeb: false,
  canRunCode: false,
  canCallAPIs: false,
  systemPromptPreview: "",
  isPreviewLoading: false,
  testMessage: "",
  testResponse: "",
  isTestLoading: false,
};

export default function AgentBuilderPage({
  token,
  apiKey,
}: AgentBuilderPageProps): JSX.Element {
  const [state, setState] = useState<AgentBuilderState>({ ...INITIAL_STATE });
  const [nameError, setNameError] = useState("");
  const [saveStatus, setSaveStatus] = useState<"idle" | "saving" | "saved" | "error">("idle");
  const [saveMessage, setSaveMessage] = useState("");
  const [validationErrors, setValidationErrors] = useState<string[]>([]);

  const previewTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const { API_BASE_URL } = getRuntimeConfig();

  // -- Name validation -------------------------------------------------------

  const validateName = useCallback((name: string) => {
    if (!name) {
      setNameError("");
      return;
    }
    if (!NAME_PATTERN.test(name)) {
      setNameError("Must start with a lowercase letter, only a-z, 0-9, and hyphens");
    } else if (name.length < 2) {
      setNameError("Must be at least 2 characters");
    } else {
      setNameError("");
    }
  }, []);

  // -- Live prompt preview (debounced) ----------------------------------------

  const fetchPreview = useCallback(
    async (currentState: AgentBuilderState) => {
      if (!currentState.name || !NAME_PATTERN.test(currentState.name)) return;

      setState((s) => ({ ...s, isPreviewLoading: true }));
      try {
        const payload = buildDefinitionPayload(currentState);
        const resp = await fetch(`${API_BASE_URL}/v1/agents/preview-prompt`, {
          method: "POST",
          headers: authHeaders(token, apiKey),
          body: JSON.stringify(payload),
        });
        if (resp.ok) {
          const data = await resp.json();
          setState((s) => ({
            ...s,
            systemPromptPreview: data.system_prompt ?? "",
            isPreviewLoading: false,
          }));
        } else {
          setState((s) => ({ ...s, isPreviewLoading: false }));
        }
      } catch {
        setState((s) => ({ ...s, isPreviewLoading: false }));
      }
    },
    [API_BASE_URL, token, apiKey],
  );

  useEffect(() => {
    if (previewTimerRef.current) clearTimeout(previewTimerRef.current);
    previewTimerRef.current = setTimeout(() => {
      void fetchPreview(state);
    }, 500);
    return () => {
      if (previewTimerRef.current) clearTimeout(previewTimerRef.current);
    };
  }, [
    state.name,
    state.description,
    state.role,
    state.canReadFiles,
    state.canWriteFiles,
    state.canSearchWeb,
    state.canRunCode,
    state.canCallAPIs,
    fetchPreview,
  ]);

  // -- State updaters --------------------------------------------------------

  function updateField<K extends keyof AgentBuilderState>(
    key: K,
    value: AgentBuilderState[K],
  ) {
    setState((prev) => ({ ...prev, [key]: value }));
    if (key === "name") validateName(value as string);
  }

  // -- Save agent ------------------------------------------------------------

  async function handleSave() {
    if (!state.name || nameError) return;
    setSaveStatus("saving");
    setSaveMessage("");
    setValidationErrors([]);

    const payload = buildDefinitionPayload(state);
    const headers = authHeaders(token, apiKey);

    // Try PUT first (update), fall back to POST (create) on 404
    try {
      const putResp = await fetch(`${API_BASE_URL}/v1/agents/${encodeURIComponent(state.name)}`, {
        method: "PUT",
        headers,
        body: JSON.stringify(payload),
      });

      if (putResp.ok) {
        setSaveStatus("saved");
        setSaveMessage("Agent updated successfully.");
        return;
      }

      if (putResp.status === 404) {
        // Agent doesn't exist yet -- create it
        const postResp = await fetch(`${API_BASE_URL}/v1/agents/`, {
          method: "POST",
          headers,
          body: JSON.stringify(payload),
        });
        if (postResp.ok) {
          setSaveStatus("saved");
          setSaveMessage("Agent created successfully.");
        } else {
          const errData = await postResp.json().catch(() => null);
          setSaveStatus("error");
          setSaveMessage(errData?.detail ?? `Error ${postResp.status}`);
        }
        return;
      }

      if (putResp.status === 422) {
        const errData = await putResp.json().catch(() => null);
        const detail = errData?.detail;
        if (Array.isArray(detail)) {
          setValidationErrors(detail.map((d: { msg?: string }) => d.msg ?? JSON.stringify(d)));
        } else {
          setValidationErrors([typeof detail === "string" ? detail : JSON.stringify(detail)]);
        }
        setSaveStatus("error");
        setSaveMessage("Validation failed.");
        return;
      }

      setSaveStatus("error");
      setSaveMessage(`Error ${putResp.status}`);
    } catch (err) {
      setSaveStatus("error");
      setSaveMessage(err instanceof Error ? err.message : "Network error");
    }
  }

  // -- Export JSON ------------------------------------------------------------

  function handleExport() {
    const exportData = buildExport(state);
    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${state.name || "agent"}-definition.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  // -- Inline test -----------------------------------------------------------

  async function handleTest() {
    if (!state.name || !state.testMessage.trim()) return;
    setState((s) => ({ ...s, isTestLoading: true, testResponse: "" }));

    try {
      const resp = await fetch(
        `${API_BASE_URL}/v1/agents/${encodeURIComponent(state.name)}/invoke`,
        {
          method: "POST",
          headers: authHeaders(token, apiKey),
          body: JSON.stringify({
            inputs: { task: state.testMessage },
            temperature: 0.4,
          }),
        },
      );
      if (resp.ok) {
        const data = await resp.json();
        const output = data.output?.response ?? data.output?.text ?? JSON.stringify(data.output);
        setState((s) => ({ ...s, testResponse: output, isTestLoading: false }));
      } else {
        const errData = await resp.json().catch(() => null);
        setState((s) => ({
          ...s,
          testResponse: `Error ${resp.status}: ${errData?.detail ?? "Request failed"}`,
          isTestLoading: false,
        }));
      }
    } catch (err) {
      setState((s) => ({
        ...s,
        testResponse: err instanceof Error ? err.message : "Network error",
        isTestLoading: false,
      }));
    }
  }

  // -- Render ----------------------------------------------------------------

  const nameValid = state.name.length >= 2 && NAME_PATTERN.test(state.name) && !nameError;

  return (
    <div className="agent-builder-page">
      <header className="agent-builder-header">
        <h1>Agent Builder</h1>
        <p>Design and deploy custom agents with a visual interface.</p>
      </header>

      <div className="agent-builder-layout">
        {/* Left column: form */}
        <div className="agent-builder-form">
          {/* Basic Info */}
          <section className="builder-section">
            <h2>Basic Info</h2>

            <label>
              Name
              <input
                type="text"
                placeholder="my-agent"
                value={state.name}
                onChange={(e) => updateField("name", e.target.value)}
                aria-invalid={!!nameError}
                aria-describedby={nameError ? "name-error" : undefined}
              />
              {nameError && (
                <span id="name-error" className="field-error" role="alert">
                  {nameError}
                </span>
              )}
            </label>

            <label>
              Description
              <textarea
                placeholder="What does this agent do?"
                value={state.description}
                onChange={(e) => updateField("description", e.target.value)}
                rows={3}
              />
            </label>

            <label>
              Role
              <select
                value={state.role}
                onChange={(e) => updateField("role", e.target.value)}
              >
                {AGENT_ROLES.map((role) => (
                  <option key={role} value={role}>
                    {role}
                  </option>
                ))}
              </select>
            </label>

            <label>
              Version
              <input
                type="text"
                placeholder="1.0.0"
                value={state.version}
                onChange={(e) => updateField("version", e.target.value)}
              />
            </label>
          </section>

          {/* Capability Toggles */}
          <section className="builder-section">
            <h2>Capabilities</h2>
            <p className="section-subtitle">
              Enable the tools and permissions this agent needs.
            </p>

            <div className="capability-toggles">
              {CAPABILITY_TOGGLES.map((toggle) => (
                <label key={toggle.key} className="toggle-row">
                  <span className="toggle-label">{toggle.label}</span>
                  <button
                    type="button"
                    role="switch"
                    aria-checked={state[toggle.key] as boolean}
                    className={`toggle-switch ${state[toggle.key] ? "active" : ""}`}
                    onClick={() =>
                      updateField(toggle.key, !state[toggle.key])
                    }
                  >
                    <span className="toggle-knob" />
                  </button>
                </label>
              ))}
            </div>
          </section>

          {/* Inline Test */}
          <section className="builder-section">
            <h2>Test Agent</h2>
            <p className="section-subtitle">
              Send a message to the saved agent and see its response.
            </p>
            <div className="test-area">
              <input
                type="text"
                placeholder="Type a test message..."
                value={state.testMessage}
                onChange={(e) => updateField("testMessage", e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") void handleTest();
                }}
              />
              <button
                type="button"
                onClick={() => void handleTest()}
                disabled={!nameValid || !state.testMessage.trim() || state.isTestLoading}
              >
                {state.isTestLoading ? "Testing..." : "Test"}
              </button>
            </div>
            {state.testResponse && (
              <pre className="test-response">{state.testResponse}</pre>
            )}
          </section>

          {/* Actions */}
          <div className="builder-actions">
            <button
              type="button"
              className="action-primary"
              onClick={() => void handleSave()}
              disabled={!nameValid || saveStatus === "saving"}
            >
              {saveStatus === "saving" ? "Saving..." : "Save Agent"}
            </button>
            <button
              type="button"
              onClick={handleExport}
              disabled={!nameValid}
            >
              Export JSON
            </button>
          </div>

          {saveMessage && (
            <p
              className={`save-feedback ${saveStatus === "error" ? "error" : "success"}`}
              role="status"
            >
              {saveMessage}
            </p>
          )}

          {validationErrors.length > 0 && (
            <ul className="validation-errors" role="alert">
              {validationErrors.map((err, i) => (
                <li key={i}>{err}</li>
              ))}
            </ul>
          )}
        </div>

        {/* Right column: live preview */}
        <div className="agent-builder-preview">
          <h2>System Prompt Preview</h2>
          {state.isPreviewLoading && (
            <p className="preview-loading">Generating preview...</p>
          )}
          {state.systemPromptPreview ? (
            <pre className="prompt-preview">{state.systemPromptPreview}</pre>
          ) : (
            !state.isPreviewLoading && (
              <p className="preview-placeholder">
                Fill in the agent details to see a live preview of the system prompt.
              </p>
            )
          )}
        </div>
      </div>
    </div>
  );
}
