import { useState } from "react";
import { getRuntimeConfig } from "../../lib/api";

interface SearchResult {
    content: string;
    level: string;
    citations: string[];
    token_estimate: number;
}

export function ResearchDashboard({ token }: { token: string | null }) {
    const [query, setQuery] = useState("");
    const [results, setResults] = useState<SearchResult[]>([]);
    const [loading, setLoading] = useState(false);
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
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({ query, level: "full", top_k: 5 })
            });
            const data = await res.json();
            setResults(data.results || []);
        } catch (e) {
            console.error("Failed to search memory:", e);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="research-dashboard">
            <h3>Research & RAG Knowledge Base</h3>
            <p>Search semantic memory vectors dynamically across the PGVector database.</p>

            <form onSubmit={searchMemory} className="search-form">
                <input
                    type="text"
                    placeholder="E.g. What did we learn about OpenClaw?"
                    value={query}
                    onChange={e => setQuery(e.target.value)}
                    style={{ padding: "8px", width: "400px", marginRight: "10px" }}
                />
                <button type="submit" disabled={loading}>
                    {loading ? "Searching..." : "Semantic Search"}
                </button>
            </form>

            <div className="results-list" style={{ marginTop: "20px" }}>
                {results.length === 0 && !loading && <p>No results yet.</p>}
                {results.map((r, i) => (
                    <div key={i} className="card" style={{ marginBottom: "15px", padding: "15px", border: "1px solid #ddd", borderRadius: "5px" }}>
                        <span className="badge" style={{ background: "#4caf50", color: "white", padding: "3px 8px", borderRadius: "12px", float: "right" }}>{r.level}</span>
                        <p>{r.content}</p>
                        {r.citations && r.citations.length > 0 && (
                            <div className="citations" style={{ fontSize: "0.8em", color: "#666" }}>
                                <strong>Citations:</strong> {r.citations.join(", ")}
                            </div>
                        )}
                        <div style={{ fontSize: "0.7em", color: "#999", marginTop: "5px" }}>Tokens: {r.token_estimate}</div>
                    </div>
                ))}
            </div>
        </div>
    );
}
