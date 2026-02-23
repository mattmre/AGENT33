import { useState, useEffect } from "react";
import { getRuntimeConfig } from "../../lib/api";

interface ProcessInfo {
    id: string;
    tenant_id: string;
    state: string;
    created_at: string;
}

export function ProcessList({ token }: { token: string | null }) {
    const [processes, setProcesses] = useState<ProcessInfo[]>([]);
    const { API_BASE_URL } = getRuntimeConfig();

    const fetchProcesses = async () => {
        if (!token) return;
        try {
            const res = await fetch(`${API_BASE_URL}/v1/operations/processes`, {
                headers: { Authorization: `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                setProcesses(data);
            }
        } catch (e) {
            console.error("Failed to fetch processes:", e);
        }
    };

    useEffect(() => {
        fetchProcesses();
        const interval = setInterval(fetchProcesses, 2000);
        return () => clearInterval(interval);
    }, [token]);

    return (
        <div className="process-list">
            <h3>Active Processes</h3>
            {processes.length === 0 && <p>No active processes.</p>}
            <ul>
                {processes.map((p) => (
                    <li key={p.id}>
                        <strong>{p.id}</strong> - {p.state} ({new Date(p.created_at).toLocaleString()})
                    </li>
                ))}
            </ul>
        </div>
    );
}
