import { useState } from "react";
import { getRuntimeConfig } from "../../lib/api";

import { CitationList } from "./CitationList";
import type { WebResearchResult } from "./CitationTypes";

interface SearchResult {
    content: string;
    level: string;
    citations: string[];
    token_estimate: number;
}

type ActiveTab = "memory" | "web";

export function ResearchDashboard({ token }: { token: string | null }) {
    const [activeTab, setActiveTab] = useState<ActiveTab>("memory");
    const [query, setQuery] = useState("");
    const [results, setResults] = useState<SearchResult[]>([]);
    const [webResults, setWebResults] = useState<WebResearchResult[]>([]);
    const [loading, setLoading] = useState(false);
    const [webError, setWebError] = useState("");
    const { API_BASE_URL } = getRuntimeConfig();

    const searchMemory = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!token || !query.trim()) return;

        setLoading(true);
        try {
            const res = await fetch(`${API_BASE_URL}/v1/memory/search`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({ query, level: "full", top_k: 5 }),
            });
            const data = await res.json();
            setResults(data.results || []);
        } catch (err) {
            console.error("Failed to search memory:", err);
        } finally {
            setLoading(false);
        }
    };

    const searchWeb = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!token || !query.trim()) return;

        setLoading(true);
        setWebError("");
        try {
            const res = await fetch(`${API_BASE_URL}/v1/research/search`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({ query, limit: 10 }),
            });
            if (!res.ok) {
                const errData = await res.json();
                setWebError(errData.detail || "Web search failed");
                setWebResults([]);
            } else {
                const data = await res.json();
                setWebResults(data.results || []);
            }
        } catch (err) {
            setWebError(err instanceof Error ? err.message : "Web search failed");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="research-dashboard">
            <h3>Research & RAG Knowledge Base</h3>
            <p>
                Search semantic memory vectors or run grounded web research
                queries.
            </p>

            {/* Tab switcher */}
            <div
                className="research-tabs"
                role="tablist"
                style={{
                    display: "flex",
                    gap: "8px",
                    marginBottom: "12px",
                }}
            >
                <button
                    role="tab"
                    aria-selected={activeTab === "memory"}
                    onClick={() => setActiveTab("memory")}
                    style={{
                        padding: "6px 14px",
                        fontWeight: activeTab === "memory" ? 700 : 400,
                        borderBottom:
                            activeTab === "memory"
                                ? "2px solid #1a73e8"
                                : "2px solid transparent",
                        background: "none",
                        border: "none",
                        cursor: "pointer",
                    }}
                >
                    Memory Search
                </button>
                <button
                    role="tab"
                    aria-selected={activeTab === "web"}
                    onClick={() => setActiveTab("web")}
                    style={{
                        padding: "6px 14px",
                        fontWeight: activeTab === "web" ? 700 : 400,
                        borderBottom:
                            activeTab === "web"
                                ? "2px solid #1a73e8"
                                : "2px solid transparent",
                        background: "none",
                        border: "none",
                        cursor: "pointer",
                    }}
                >
                    Web Research
                </button>
            </div>

            {/* Memory search tab */}
            {activeTab === "memory" && (
                <>
                    <form onSubmit={searchMemory} className="search-form">
                        <input
                            type="text"
                            placeholder="E.g. What did we learn about OpenClaw?"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            style={{
                                padding: "8px",
                                width: "400px",
                                marginRight: "10px",
                            }}
                        />
                        <button type="submit" disabled={loading}>
                            {loading ? "Searching..." : "Semantic Search"}
                        </button>
                    </form>

                    <div
                        className="results-list"
                        style={{ marginTop: "20px" }}
                    >
                        {results.length === 0 && !loading && (
                            <p>No results yet.</p>
                        )}
                        {results.map((r, i) => (
                            <div
                                key={i}
                                className="card"
                                style={{
                                    marginBottom: "15px",
                                    padding: "15px",
                                    border: "1px solid #ddd",
                                    borderRadius: "5px",
                                }}
                            >
                                <span
                                    className="badge"
                                    style={{
                                        background: "#4caf50",
                                        color: "white",
                                        padding: "3px 8px",
                                        borderRadius: "12px",
                                        float: "right",
                                    }}
                                >
                                    {r.level}
                                </span>
                                <p>{r.content}</p>
                                {r.citations && r.citations.length > 0 && (
                                    <div
                                        className="citations"
                                        style={{
                                            fontSize: "0.8em",
                                            color: "#666",
                                        }}
                                    >
                                        <strong>Citations:</strong>{" "}
                                        {r.citations.join(", ")}
                                    </div>
                                )}
                                <div
                                    style={{
                                        fontSize: "0.7em",
                                        color: "#999",
                                        marginTop: "5px",
                                    }}
                                >
                                    Tokens: {r.token_estimate}
                                </div>
                            </div>
                        ))}
                    </div>
                </>
            )}

            {/* Web research tab */}
            {activeTab === "web" && (
                <>
                    <form onSubmit={searchWeb} className="search-form">
                        <input
                            type="text"
                            placeholder="E.g. FastAPI dependency injection patterns"
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            style={{
                                padding: "8px",
                                width: "400px",
                                marginRight: "10px",
                            }}
                        />
                        <button type="submit" disabled={loading}>
                            {loading ? "Searching..." : "Web Search"}
                        </button>
                    </form>

                    {webError && (
                        <div
                            className="error-box"
                            style={{
                                color: "#c62828",
                                marginTop: "10px",
                            }}
                        >
                            {webError}
                        </div>
                    )}

                    <div style={{ marginTop: "20px" }}>
                        <CitationList citations={webResults} />
                    </div>
                </>
            )}
        </div>
    );
}
