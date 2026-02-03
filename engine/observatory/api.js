/**
 * AGENT-33 Observatory - API Client
 *
 * Handles all communication with the backend API endpoints.
 */

const ObservatoryAPI = (function () {
    // Base URL for API calls - adjust based on deployment
    const BASE_URL = window.location.origin;

    /**
     * Generic fetch wrapper with error handling
     * @param {string} endpoint - API endpoint path
     * @param {Object} options - Fetch options
     * @returns {Promise<any>} Response data
     */
    async function request(endpoint, options = {}) {
        const url = `${BASE_URL}${endpoint}`;
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };

        const mergedOptions = {
            ...defaultOptions,
            ...options,
            headers: {
                ...defaultOptions.headers,
                ...options.headers,
            },
        };

        try {
            const response = await fetch(url, mergedOptions);

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                const error = new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
                error.status = response.status;
                error.data = errorData;
                throw error;
            }

            return await response.json();
        } catch (error) {
            if (error.name === 'TypeError' && error.message === 'Failed to fetch') {
                const networkError = new Error('Network error: Unable to connect to the server');
                networkError.isNetworkError = true;
                throw networkError;
            }
            throw error;
        }
    }

    /**
     * Fetch activity feed with pagination
     * @param {number} page - Page number (1-indexed)
     * @param {number} limit - Items per page
     * @returns {Promise<{items: Array, total: number, page: number}>}
     */
    async function fetchActivity(page = 1, limit = 20) {
        const params = new URLSearchParams({
            page: page.toString(),
            limit: limit.toString(),
        });
        return request(`/api/activity?${params}`);
    }

    /**
     * Fetch system statistics
     * @returns {Promise<{facts_count: number, sources_count: number, queries_today: number, uptime: string}>}
     */
    async function fetchStats() {
        return request('/api/stats');
    }

    /**
     * Send a question to the agent
     * @param {string} question - User's question
     * @returns {Promise<{answer: string, sources: Array}>}
     */
    async function askAgent(question) {
        return request('/api/ask', {
            method: 'POST',
            body: JSON.stringify({ question }),
        });
    }

    /**
     * Connect to the activity stream via Server-Sent Events
     * @param {Object} callbacks - Event handlers
     * @param {Function} callbacks.onActivity - Called when new activity arrives
     * @param {Function} callbacks.onConnect - Called when connection established
     * @param {Function} callbacks.onDisconnect - Called when connection lost
     * @param {Function} callbacks.onError - Called on error
     * @returns {EventSource} The EventSource instance for cleanup
     */
    function connectActivityStream(callbacks = {}) {
        const {
            onActivity = () => {},
            onConnect = () => {},
            onDisconnect = () => {},
            onError = () => {},
        } = callbacks;

        const eventSource = new EventSource(`${BASE_URL}/api/activity/stream`);

        eventSource.onopen = function () {
            onConnect();
        };

        eventSource.onmessage = function (event) {
            try {
                const data = JSON.parse(event.data);
                onActivity(data);
            } catch (err) {
                console.error('Failed to parse activity event:', err);
            }
        };

        eventSource.onerror = function (event) {
            if (eventSource.readyState === EventSource.CLOSED) {
                onDisconnect();
            } else {
                onError(new Error('SSE connection error'));
            }
        };

        // Handle specific event types if the server sends them
        eventSource.addEventListener('activity', function (event) {
            try {
                const data = JSON.parse(event.data);
                onActivity(data);
            } catch (err) {
                console.error('Failed to parse activity event:', err);
            }
        });

        eventSource.addEventListener('heartbeat', function () {
            // Keep-alive, no action needed
        });

        return eventSource;
    }

    /**
     * Check if the server is healthy
     * @returns {Promise<{status: string, services: Object}>}
     */
    async function checkHealth() {
        return request('/health');
    }

    /**
     * Fetch knowledge graph data (placeholder for future implementation)
     * @returns {Promise<{nodes: Array, edges: Array}>}
     */
    async function fetchKnowledgeGraph() {
        return request('/api/knowledge/graph');
    }

    // Public API
    return {
        fetchActivity,
        fetchStats,
        askAgent,
        connectActivityStream,
        checkHealth,
        fetchKnowledgeGraph,
        BASE_URL,
    };
})();

// Export for module systems if available
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ObservatoryAPI;
}
