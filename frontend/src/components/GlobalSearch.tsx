import { useState } from "react";

import { getRuntimeConfig } from "../lib/api";

interface MemorySearchResult {
  content: string;
  token_estimate: number;
  level: string;
}

export function GlobalSearch({ token }: { token: string | null }): JSX.Element {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<MemorySearchResult[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const canSearch = Boolean(token);
  const { API_BASE_URL } = getRuntimeConfig();

  async function searchMemory(event: React.FormEvent): Promise<void> {
    event.preventDefault();
    if (!query.trim()) {
      return;
    }
    if (!token) {
      setResults([]);
      setIsOpen(true);
      return;
    }

    setLoading(true);
    setIsOpen(true);
    try {
      const response = await fetch(`${API_BASE_URL}/v1/memory/search`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({ query, level: "full", top_k: 3 })
      });
      const data = await response.json();
      setResults(data.results || []);
    } catch (error) {
      console.error("Failed to search globally:", error);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="global-search" role="search">
      <form className="global-search-form" onSubmit={searchMemory}>
        <input
          className="global-search-input"
          type="search"
          aria-label="Search semantic memory"
          placeholder={canSearch ? "Search semantic memory" : "Sign in to use memory search"}
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          disabled={!canSearch}
        />
      </form>

      {isOpen ? (
        <div role="region" aria-label="Search results" aria-live="polite" className="global-search-results">
          <div className="global-search-results-header">
            <strong>{loading ? "Searching..." : "Memory results"}</strong>
            <button type="button" onClick={() => setIsOpen(false)} aria-label="Close search results">
              Close
            </button>
          </div>
          {!canSearch ? <div className="global-search-empty">Add a token in Integrations to enable search.</div> : null}
          {results.length === 0 && !loading ? <div className="global-search-empty">No results found.</div> : null}
          {results.map((result, index) => (
            <article key={`${result.level}-${index}`} className="global-search-result">
              <div className="global-search-result-content">{result.content.substring(0, 150)}...</div>
              <div className="global-search-result-meta">
                Tokens: {result.token_estimate} | Match: {result.level}
              </div>
            </article>
          ))}
        </div>
      ) : null}
    </div>
  );
}
