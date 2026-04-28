import { useMemo, useState } from "react";

import type { WorkflowStarterDraft } from "../workflow-starter/types";
import { DEMO_SCENARIOS, findDemoScenario } from "./demoScenarios";

interface DemoModePanelProps {
  onOpenModels: () => void;
  onOpenWorkflowCatalog: () => void;
  onOpenWorkflowStarter: (draft?: WorkflowStarterDraft) => void;
}

export function DemoModePanel({
  onOpenModels,
  onOpenWorkflowCatalog,
  onOpenWorkflowStarter
}: DemoModePanelProps): JSX.Element {
  const [selectedId, setSelectedId] = useState(DEMO_SCENARIOS[0]?.id ?? "");
  const scenario = useMemo(() => findDemoScenario(selectedId), [selectedId]);
  const scenarioIndex = Math.max(
    DEMO_SCENARIOS.findIndex((item) => item.id === scenario.id) + 1,
    1
  );

  return (
    <section className="demo-mode-panel" aria-labelledby="demo-mode-title">
      <header className="demo-mode-hero">
        <div>
          <p className="eyebrow">No-setup demo mode</p>
          <h2 id="demo-mode-title">See a first successful run before connecting anything</h2>
          <p>
            Demo Mode uses static sample data to show how AGENT33 should feel once a model and
            workspace are connected: clear intake, visible progress, reviewable artifacts, and a
            safe next action.
          </p>
        </div>
        <div className="demo-mode-score">
          <strong>0 credentials needed</strong>
          <span>Offline preview with no model calls</span>
        </div>
      </header>

      <div className="demo-mode-layout">
        <aside className="demo-mode-picker" aria-label="Demo scenarios">
          <h3>Choose a sample outcome</h3>
          {DEMO_SCENARIOS.map((item) => (
            <button
              key={item.id}
              type="button"
              className={item.id === scenario.id ? "active" : ""}
              onClick={() => setSelectedId(item.id)}
              aria-pressed={item.id === scenario.id}
            >
              <strong>{item.title}</strong>
              <span>{item.audience}</span>
              <small>
                {item.complexity} · {item.timeEstimate} · {item.artifacts.length} artifacts
              </small>
            </button>
          ))}
        </aside>

        <div className="demo-mode-workspace">
          <article className="demo-mode-card demo-mode-brief">
            <div>
              <p className="eyebrow">{scenario.audience}</p>
              <h3>{scenario.title}</h3>
              <div className="demo-scenario-meta" aria-label="Selected demo details">
                <span>
                  {scenarioIndex} of {DEMO_SCENARIOS.length}
                </span>
                <span>{scenario.complexity}</span>
                <span>{scenario.timeEstimate}</span>
                <span>{scenario.artifacts.length} artifacts</span>
              </div>
              <p>{scenario.outcome}</p>
            </div>
            <blockquote>{scenario.prompt}</blockquote>
            <div className="demo-mode-inputs">
              {scenario.sampleInputs.map((input) => (
                <span key={`${scenario.id}-${input}`}>{input}</span>
              ))}
            </div>
          </article>

          <article className="demo-mode-card">
            <h3>Simulated run timeline</h3>
            <ol className="demo-run-timeline">
              {scenario.runSteps.map((step) => (
                <li key={step.id} className={`demo-run-step demo-run-step--${step.tone}`}>
                  <strong>{step.title}</strong>
                  <span>{step.description}</span>
                </li>
              ))}
            </ol>
          </article>

          <section className="demo-artifact-grid" aria-label="Demo artifacts">
            {scenario.artifacts.map((artifact) => (
              <article key={artifact.id} className="demo-mode-card demo-artifact-card">
                <h3>{artifact.title}</h3>
                <p>{artifact.description}</p>
                <ul>
                  {artifact.contents.map((item, index) => (
                    <li key={`${artifact.id}-${index}`}>{item}</li>
                  ))}
                </ul>
              </article>
            ))}
          </section>

          <article className="demo-mode-card demo-mode-next">
            <div>
              <h3>Ready to make it real?</h3>
              <p>
                Keep exploring without setup, or connect a model and send this sample into Workflow
                Starter as an editable draft.
              </p>
            </div>
            <div className="demo-mode-actions">
              <button type="button" onClick={onOpenModels}>
                Connect a model
              </button>
              <button type="button" onClick={onOpenWorkflowCatalog}>
                Browse workflow catalog
              </button>
              <button type="button" onClick={() => onOpenWorkflowStarter(scenario.starterDraft)}>
                Customize this demo
              </button>
            </div>
          </article>
        </div>
      </div>
    </section>
  );
}
