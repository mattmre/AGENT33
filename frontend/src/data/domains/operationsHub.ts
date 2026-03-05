import type { DomainConfig } from "../../types";

export const operationsHubDomain: DomainConfig = {
    id: "operations",
    title: "Operations Hub",
    description: "Monitor and manage autonomous agent lifecycle loops and tracking.",
    operations: [
        {
            id: "operations-hub-overview",
            title: "Hub Overview",
            method: "GET",
            path: "/v1/operations/hub",
            description: "Unified operations-hub view with active process counts, optional trace/budget/improvement/workflow inclusions.",
            defaultQuery: {
                include: "traces,budgets",
                limit: "100"
            }
        },
        {
            id: "operations-process-detail",
            title: "Process Detail",
            method: "GET",
            path: "/v1/operations/processes/{process_id}",
            description: "Retrieve detail for a single process including actions and metadata.",
            defaultPathParams: {
                process_id: "replace-with-process-id"
            }
        },
        {
            id: "operations-process-control",
            title: "Process Control",
            method: "POST",
            path: "/v1/operations/processes/{process_id}/control",
            description: "Execute lifecycle controls (pause, resume, cancel) against a running process.",
            defaultPathParams: {
                process_id: "replace-with-process-id"
            },
            defaultBody: JSON.stringify({
                action: "pause",
                reason: ""
            }, null, 2)
        }
    ]
};
