import { useState } from "react";
import { getRuntimeConfig } from "../../lib/api";

export function ControlPanel({ token, processId }: { token: string | null; processId?: string }) {
    const [loading, setLoading] = useState(false);
    const { API_BASE_URL } = getRuntimeConfig();

    const handleAction = async (action: string) => {
        if (!token || !processId) return;
        setLoading(true);
        try {
            await fetch(`${API_BASE_URL}/v1/operations/processes/${processId}/lifecycle`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({ action })
            });
        } catch (e) {
            console.error(`Failed to ${action} process:`, e);
        } finally {
            setLoading(false);
        }
    };

    if (!processId) {
        return <div className="control-panel panel-disabled">Select a process to manage its lifecycle.</div>;
    }

    return (
        <div className="control-panel">
            <h3>Control Loop: {processId}</h3>
            <div className="button-group">
                <button onClick={() => handleAction("pause")} disabled={loading}>Pause</button>
                <button onClick={() => handleAction("resume")} disabled={loading}>Resume</button>
                <button onClick={() => handleAction("cancel")} disabled={loading} className="btn-danger">Cancel</button>
            </div>
        </div>
    );
}
