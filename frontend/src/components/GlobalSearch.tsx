import { useState } from "react";
import { getRuntimeConfig } from "../lib/api";

export function GlobalSearch({ token }: { token: string | null }) {
    const [query, setQuery] = useState("");
    const [results, setResults] = useState<any[]>([]);
    const [isOpen, setIsOpen] = useState(false);
    const [loading, setLoading] = useState(false);
    const canSearch = Boolean(token);
    const { API_BASE_URL } = getRuntimeConfig();

    const searchMemory = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!query.trim()) return;
        if (!token) {
            setResults([]);
            setIsOpen(true);
            return;
        }

        setLoading(true);
        setIsOpen(true);
        try {
            const res = await fetch(`${API_BASE_URL}/v1/memory/search`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({ query, level: "full", top_k: 3 })
            });
            const data = await res.json();
            setResults(data.results || []);
        } catch (e) {
            console.error("Failed to search globally:", e);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="global-search" style={{ position: "relative", marginLeft: "20px", flex: 1 }}>
            <form onSubmit={searchMemory} style={{ display: "flex", alignItems: "center" }}>
                <input
                    type="text"
                    placeholder={canSearch ? "Search Semantic Memory (PGVector)..." : "Sign in to use memory search"}
                    value={query}
                    onChange={e => setQuery(e.target.value)}
                    disabled={!canSearch}
                    style={{ padding: "8px 12px", width: "100%", maxWidth: "400px", borderRadius: "4px", border: "1px solid #ccc" }}
                />
            </form>

            {isOpen && (
                <div style={{ position: "absolute", top: "100%", left: 0, right: 0, background: "white", color: "black", boxShadow: "0 4px 6px rgba(0,0,0,0.1)", zIndex: 100, borderRadius: "4px", marginTop: "5px", padding: "10px", maxHeight: "400px", overflowY: "auto" }}>
                    <div style={{ display: "flex", justifyContent: "space-between", borderBottom: "1px solid #ddd", paddingBottom: "5px", marginBottom: "10px" }}>
                        <strong style={{ color: "#333" }}>{loading ? "Searching..." : "Memory Results"}</strong>
                        <button onClick={() => setIsOpen(false)} style={{ background: "none", border: "none", cursor: "pointer", color: "#666" }}>✕</button>
                    </div>
                    {!canSearch ? <div style={{ color: "#666" }}>Add a token in Integrations to enable search.</div> : null}
                    {results.length === 0 && !loading && <div style={{ color: "#666" }}>No results found.</div>}
                    {results.map((r, i) => (
                        <div key={i} style={{ marginBottom: "10px", paddingBottom: "10px", borderBottom: "1px solid #eee" }}>
                            <div style={{ fontSize: "0.9em", color: "#333" }}>{r.content.substring(0, 150)}...</div>
                            <div style={{ fontSize: "0.75em", color: "#888", marginTop: "3px" }}>Tokens: {r.token_estimate} | Match: {r.level}</div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
