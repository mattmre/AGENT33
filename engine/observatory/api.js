/**
 * AGENT-33 Observatory - Enhanced API Client
 *
 * Handles all communication with the backend API endpoints.
 * Features: error handling, loading states, SSE with auto-reconnect
 */

const ObservatoryAPI = (function () {
    // Base URL for API calls - adjust based on deployment
    const BASE_URL = window.location.origin;

    // Connection state for SSE
    let reconnectAttempts = 0;
    const MAX_RECONNECT_ATTEMPTS = 10;
    const BASE_RECONNECT_DELAY = 1000; // 1 second

    /**
     * Calculate exponential backoff delay
     * @param {number} attempt - Current attempt number
     * @returns {number} Delay in milliseconds
     */
    function getReconnectDelay(attempt) {
        // Exponential backoff: 1s, 2s, 4s, 8s, 16s, 32s (max)
        const delay = Math.min(BASE_RECONNECT_DELAY * Math.pow(2, attempt), 32000);
        // Add jitter (0-1000ms) to prevent thundering herd
        return delay + Math.random() * 1000;
    }

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
     * Send a question to the agent with loading state management
     * @param {string} question - User's question
     * @param {Object} options - Additional options
     * @param {Function} options.onLoadingChange - Callback for loading state changes
     * @returns {Promise<{answer: string, sources: Array}>}
     */
    async function askAgent(question, options = {}) {
        const { onLoadingChange = () => {} } = options;

        onLoadingChange(true);

        try {
            const result = await request('/api/ask', {
                method: 'POST',
                body: JSON.stringify({ question }),
            });
            return result;
        } finally {
            onLoadingChange(false);
        }
    }

    /**
     * Fetch knowledge graph data
     * @param {number} limit - Maximum number of nodes to return
     * @param {Object} filter - Filter options
     * @param {string} filter.type - Node type filter (entity, relationship, event)
     * @param {string} filter.search - Search query for node labels
     * @returns {Promise<{nodes: Array, edges: Array, metadata: Object}>}
     */
    async function fetchKnowledgeGraph(limit = 100, filter = {}) {
        const params = new URLSearchParams({
            limit: limit.toString(),
        });

        if (filter.type && filter.type !== 'all') {
            params.append('type', filter.type);
        }

        if (filter.search) {
            params.append('search', filter.search);
        }

        return request(`/api/knowledge/graph?${params}`);
    }

    /**
     * Connect to the activity stream via Server-Sent Events with auto-reconnect
     * @param {Object} callbacks - Event handlers
     * @param {Function} callbacks.onActivity - Called when new activity arrives
     * @param {Function} callbacks.onConnect - Called when connection established
     * @param {Function} callbacks.onDisconnect - Called when connection lost
     * @param {Function} callbacks.onError - Called on error
     * @param {Function} callbacks.onReconnecting - Called when attempting to reconnect
     * @returns {Object} Controller object with close() method
     */
    function connectActivityStream(callbacks = {}) {
        const {
            onActivity = () => {},
            onConnect = () => {},
            onDisconnect = () => {},
            onError = () => {},
            onReconnecting = () => {},
        } = callbacks;

        let eventSource = null;
        let reconnectTimeout = null;
        let isManualClose = false;

        function connect() {
            if (eventSource) {
                eventSource.close();
            }

            eventSource = new EventSource(`${BASE_URL}/api/activity/stream`);

            eventSource.onopen = function () {
                reconnectAttempts = 0;
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
                if (isManualClose) {
                    return;
                }

                if (eventSource.readyState === EventSource.CLOSED) {
                    onDisconnect();
                    scheduleReconnect();
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

            eventSource.addEventListener('stats', function (event) {
                try {
                    const data = JSON.parse(event.data);
                    if (callbacks.onStats) {
                        callbacks.onStats(data);
                    }
                } catch (err) {
                    console.error('Failed to parse stats event:', err);
                }
            });
        }

        function scheduleReconnect() {
            if (isManualClose || reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
                if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
                    onError(new Error('Max reconnection attempts reached'));
                }
                return;
            }

            const delay = getReconnectDelay(reconnectAttempts);
            reconnectAttempts++;

            onReconnecting({ attempt: reconnectAttempts, delay, maxAttempts: MAX_RECONNECT_ATTEMPTS });

            reconnectTimeout = setTimeout(connect, delay);
        }

        // Initial connection
        connect();

        // Return controller object
        return {
            close: function () {
                isManualClose = true;
                if (reconnectTimeout) {
                    clearTimeout(reconnectTimeout);
                }
                if (eventSource) {
                    eventSource.close();
                }
            },
            reconnect: function () {
                isManualClose = false;
                reconnectAttempts = 0;
                connect();
            },
            getEventSource: function () {
                return eventSource;
            },
        };
    }

    /**
     * Check if the server is healthy
     * @returns {Promise<{status: string, services: Object}>}
     */
    async function checkHealth() {
        return request('/health');
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
        // Expose for testing
        _getReconnectDelay: getReconnectDelay,
    };
})();

// Export for module systems if available
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ObservatoryAPI;
}
