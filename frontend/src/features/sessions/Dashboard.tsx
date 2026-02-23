import { useState, useEffect } from "react";
import { getRuntimeConfig } from "../../lib/api";

export function SessionsDashboard({ token }: { token: string | null }) {
    const [sessions, setSessions] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);
    const { API_BASE_URL } = getRuntimeConfig();

    const loadSessions = async () => {
        if (!token) return;
        setLoading(true);
        try {
            const res = await fetch(`${API_BASE_URL}/v1/sessions`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            const data = await res.json();
            setSessions(data);
        } catch (e) {
            console.error("Failed to load sessions:", e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadSessions();
    }, [token]);

    return (
        <div className="sessions-dashboard">
            <h3>Session Logs & Alignment Status</h3>
            <p>Historic execution contexts and system checkpoints.</p>
            <button onClick={loadSessions} disabled={loading} style={{ marginBottom: "15px" }}>
                {loading ? "Loading..." : "Refresh Sessions"}
            </button>

            <div className="sessions-list">
                {sessions.length === 0 ? (
                    <p>No historic sessions found or API not wired.</p>
                ) : (
                    <ul>
                        {sessions.map((s, i) => (
                            <li key={i} style={{ padding: "10px", borderBottom: "1px solid #ccc" }}>
                                Session: <strong>{s.id || "Unknown"}</strong>
                            </li>
                        ))}
                    </ul>
                )}
            </div>
        </div>
    );
}
