import { useState } from "react";
import { getRuntimeConfig } from "../../lib/api";

interface EvolutionPR {
    proposal_id: string;
    title: string;
    description: string;
    branch: string;
}

export function EvolutionDashboard({ token }: { token: string | null }) {
    const [prs, setPrs] = useState<EvolutionPR[]>([]);
    const { API_BASE_URL } = getRuntimeConfig();

    // Mocking PR load for now as the backend route isn't fully piped
    const loadPRs = () => {
        setPrs([
            {
                proposal_id: "evolve-security_audit_local-20260219",
                title: "Autonomous Improvement: Optimize security_audit_local",
                description: "Automated PR generated from context: Triggered from Self-Evolution dashboard",
                branch: "auto-evolve/evolve-security_audit_local-20260219"
            }
        ]);
    };

    const triggerAudit = async () => {
        if (!token) return;
        try {
            await fetch(`${API_BASE_URL}/v1/outcomes/improvements`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`
                },
                body: JSON.stringify({ metric_id: "security_audit_local", context: "Triggered from Self-Evolution dashboard" })
            });
            alert("Rigorous Security Audit initiated in the background.");
            setTimeout(loadPRs, 3000); // Simulate finding a PR after a few seconds
        } catch (e) {
            console.error("Failed to trigger audit:", e);
        }
    };

    return (
        <div className="evolution-dashboard">
            <h3>Self-Evolution & Security Engine</h3>
            <div className="action-bar">
                <button onClick={triggerAudit} className="btn-primary">Execute Simulated Hack / Audit</button>
                <button onClick={loadPRs}>Refresh Pending PRs</button>
            </div>

            <div className="prs-list">
                <h4>Pending Agent-Generated Pull Requests</h4>
                {prs.length === 0 ? (
                    <p>No pending evolutionary PRs.</p>
                ) : (
                    <ul>
                        {prs.map(pr => (
                            <li key={pr.proposal_id} className="pr-card">
                                <strong>{pr.title}</strong>
                                <p>{pr.description}</p>
                                <code>Branch: {pr.branch}</code>
                                <div className="button-group pt-2">
                                    <button className="btn-success">Merge & Approve</button>
                                    <button className="btn-danger">Reject</button>
                                </div>
                            </li>
                        ))}
                    </ul>
                )}
            </div>
        </div>
    );
}
