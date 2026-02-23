import type { DomainConfig } from "../../types";

export const operationsHubDomain: DomainConfig = {
    id: "operations",
    title: "Operations Hub",
    description: "Monitor and manage autonomous agent lifecycle loops and tracking.",
    operations: [
        {
            id: "operations-list-processes",
            title: "List Active Processes",
            method: "GET",
            path: "/v1/operations/processes",
            description: "Retrieve all active or queued autonomous agent processes."
        },
        {
            id: "operations-lifecycle-control",
            title: "Control Loop Lifecycle",
            method: "POST",
            path: "/v1/operations/processes/{process_id}/lifecycle",
            description: "Send lifecycle commands (pause, resume, cancel) to a running process loop.",
            defaultPathParams: {
                process_id: "agent-session-1234"
            },
            defaultBody: JSON.stringify({
                action: "pause"
            }, null, 2)
        }
    ]
};
