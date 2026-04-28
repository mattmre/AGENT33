import { useMemo, useState } from "react";

import { searchHelpArticles } from "./search";
import type { HelpArticle, HelpAssistantTarget } from "./types";

interface HelpAssistantDrawerProps {
  onNavigate: (target: HelpAssistantTarget) => void;
}

function renderArticle(article: HelpArticle, onNavigate: (target: HelpAssistantTarget) => void): JSX.Element {
  return (
    <article className="help-assistant-answer" aria-labelledby={`help-answer-${article.id}`}>
      <div className="help-assistant-answer-head">
        <div>
          <p className="eyebrow">{article.audience}</p>
          <h3 id={`help-answer-${article.id}`}>{article.title}</h3>
        </div>
        <span>{article.sources.length} cited sources</span>
      </div>
      <p>{article.summary}</p>
      <div className="help-assistant-body">
        {article.body.map((paragraph, index) => (
          <p key={`${article.id}-body-${index}`}>{paragraph}</p>
        ))}
      </div>
      <div className="help-assistant-steps">
        <h4>Do this next</h4>
        <ol>
          {article.steps.map((step, index) => (
            <li key={`${article.id}-step-${index}`}>{step}</li>
          ))}
        </ol>
      </div>
      <div className="help-assistant-actions">
        {article.actions.map((action) => (
          <button key={`${article.id}-${action.target}`} type="button" onClick={() => onNavigate(action.target)}>
            {action.label}
          </button>
        ))}
      </div>
      <details className="help-assistant-sources">
        <summary>Sources used for this answer</summary>
        <ul>
          {article.sources.map((source) => (
            <li key={`${article.id}-${source.path}`}>
              <strong>{source.label}</strong>
              <code>{source.path}</code>
            </li>
          ))}
        </ul>
      </details>
    </article>
  );
}

export function HelpAssistantDrawer({ onNavigate }: HelpAssistantDrawerProps): JSX.Element {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState("");
  const results = useMemo(() => searchHelpArticles(query), [query]);
  const selectedArticle = results[0]?.article;

  return (
    <aside className="help-assistant" aria-label="Ask AGENT33 help assistant">
      <button
        type="button"
        className="help-assistant-toggle"
        onClick={() => setIsOpen((current) => !current)}
        aria-expanded={isOpen}
        aria-controls="help-assistant-panel"
      >
        Ask AGENT33
      </button>

      {isOpen ? (
        <div id="help-assistant-panel" className="help-assistant-panel">
          <header className="help-assistant-header">
            <div>
              <p className="eyebrow">Offline setup helper</p>
              <h2>Ask AGENT33 how to get started</h2>
              <p>
                Search built-in setup recipes and feature docs. This MVP does not call an external
                model and it never stores or reveals secrets.
              </p>
            </div>
            <button type="button" onClick={() => setIsOpen(false)} aria-label="Close help assistant">
              Close
            </button>
          </header>

          <label className="help-assistant-search">
            What are you trying to do?
            <input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="How do I connect OpenRouter?"
              autoComplete="off"
            />
          </label>

          <div className="help-assistant-quick-prompts" aria-label="Suggested help questions">
            {["Connect OpenRouter", "Start Docker", "Run a first workflow", "What is MCP?"].map((prompt) => (
              <button key={prompt} type="button" onClick={() => setQuery(prompt)}>
                {prompt}
              </button>
            ))}
          </div>

          {selectedArticle ? (
            renderArticle(selectedArticle, onNavigate)
          ) : (
            <article className="help-assistant-empty" role="status">
              <h3>No exact setup recipe yet</h3>
              <p>
                Try OpenRouter, Docker, workflow, MCP, safety, or beginner mode. If this keeps
                missing your question, use it as a signal for the next help corpus update.
              </p>
            </article>
          )}

          {results.length > 1 ? (
            <section className="help-assistant-related" aria-label="Related help topics">
              <h3>Related topics</h3>
              {results.slice(1).map((result) => (
                <button key={result.article.id} type="button" onClick={() => setQuery(result.article.title)}>
                  {result.article.title}
                  <span>{result.article.summary}</span>
                </button>
              ))}
            </section>
          ) : null}
        </div>
      ) : null}
    </aside>
  );
}
