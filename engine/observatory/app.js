/**
 * AGENT-33 Observatory - Main Application Controller
 *
 * Handles UI interactions, state management, and component orchestration.
 * Features: SSE with auto-reconnect, stats polling, graph refresh, connection status
 */

(function () {
    'use strict';

    // Configuration
    const CONFIG = {
        statsPollingInterval: 30000,      // 30 seconds
        graphRefreshInterval: 60000,      // 60 seconds
        activityPageSize: 15,
        graphNodeLimit: 100,
    };

    // Application state
    const state = {
        connected: false,
        reconnecting: false,
        currentPage: 1,
        totalPages: 1,
        itemsPerPage: CONFIG.activityPageSize,
        streamController: null,
        statsInterval: null,
        graphInterval: null,
        chatHistory: [],
        chatLoading: false,
        graphFilter: {
            type: 'all',
            search: '',
        },
    };

    // DOM element references
    const elements = {
        statusIndicator: null,
        statusText: null,
        statsGrid: null,
        activityFeed: null,
        pageInfo: null,
        prevPage: null,
        nextPage: null,
        refreshActivity: null,
        chatMessages: null,
        chatForm: null,
        chatInput: null,
        chatSubmit: null,
        lastUpdate: null,
        graphContainer: null,
        graphSearch: null,
        graphTypeFilter: null,
        graphDetails: null,
        graphZoomIn: null,
        graphZoomOut: null,
        graphReset: null,
        graphRefresh: null,
    };

    /**
     * Initialize DOM element references
     */
    function initElements() {
        elements.statusIndicator = document.getElementById('status-indicator');
        elements.statusText = elements.statusIndicator?.querySelector('.status-text');
        elements.statsGrid = document.getElementById('stats-grid');
        elements.activityFeed = document.getElementById('activity-feed');
        elements.pageInfo = document.getElementById('page-info');
        elements.prevPage = document.getElementById('prev-page');
        elements.nextPage = document.getElementById('next-page');
        elements.refreshActivity = document.getElementById('refresh-activity');
        elements.chatMessages = document.getElementById('chat-messages');
        elements.chatForm = document.getElementById('chat-form');
        elements.chatInput = document.getElementById('chat-input');
        elements.chatSubmit = document.getElementById('chat-submit');
        elements.lastUpdate = document.getElementById('last-update');
        elements.graphContainer = document.getElementById('graph-container');
        elements.graphSearch = document.getElementById('graph-search');
        elements.graphTypeFilter = document.getElementById('graph-type-filter');
        elements.graphDetails = document.getElementById('graph-details');
        elements.graphZoomIn = document.getElementById('graph-zoom-in');
        elements.graphZoomOut = document.getElementById('graph-zoom-out');
        elements.graphReset = document.getElementById('graph-reset');
        elements.graphRefresh = document.getElementById('graph-refresh');
    }

    /**
     * Update connection status indicator
     * @param {string} status - 'connected', 'disconnected', 'connecting', or 'reconnecting'
     * @param {Object} data - Optional additional data (for reconnecting status)
     */
    function updateConnectionStatus(status, data = {}) {
        if (!elements.statusIndicator) return;

        elements.statusIndicator.classList.remove('connected', 'disconnected', 'reconnecting');

        switch (status) {
            case 'connected':
                elements.statusIndicator.classList.add('connected');
                elements.statusText.textContent = 'Connected';
                state.connected = true;
                state.reconnecting = false;
                break;
            case 'disconnected':
                elements.statusIndicator.classList.add('disconnected');
                elements.statusText.textContent = 'Disconnected';
                state.connected = false;
                state.reconnecting = false;
                break;
            case 'reconnecting':
                elements.statusIndicator.classList.add('reconnecting');
                elements.statusText.textContent = `Reconnecting (${data.attempt}/${data.maxAttempts})...`;
                state.reconnecting = true;
                break;
            default:
                elements.statusText.textContent = 'Connecting...';
                state.connected = false;
        }
    }

    /**
     * Format a timestamp for display
     * @param {string|Date} timestamp - ISO timestamp or Date object
     * @returns {string} Formatted time string
     */
    function formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        const now = new Date();
        const diff = now - date;

        if (diff < 60000) return 'Just now';
        if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
        if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;

        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    /**
     * Get icon for activity type
     * @param {string} type - Activity type
     * @returns {Object} Icon info with symbol and class
     */
    function getActivityIcon(type) {
        const icons = {
            query: { symbol: 'Q', class: 'query' },
            ingest: { symbol: 'I', class: 'ingest' },
            workflow: { symbol: 'W', class: 'workflow' },
            error: { symbol: '!', class: 'error' },
            chat: { symbol: 'C', class: 'chat' },
            agent: { symbol: 'A', class: 'agent' },
            system: { symbol: 'S', class: 'system' },
        };
        return icons[type] || { symbol: '?', class: 'default' };
    }

    /**
     * Render a single activity item
     * @param {Object} activity - Activity data
     * @returns {HTMLElement} Activity item element
     */
    function renderActivityItem(activity) {
        const item = document.createElement('div');
        item.className = 'activity-item';
        item.dataset.id = activity.id || '';

        const icon = getActivityIcon(activity.type);
        const timestamp = formatTimestamp(activity.timestamp || new Date());

        item.innerHTML = `
            <div class="activity-icon ${icon.class}">
                <span>${icon.symbol}</span>
            </div>
            <div class="activity-content">
                <div class="activity-message">${escapeHtml(activity.message || activity.content || 'Unknown activity')}</div>
                <div class="activity-meta">
                    <span class="activity-timestamp">${timestamp}</span>
                    ${activity.agent ? `<span class="activity-agent">${escapeHtml(activity.agent)}</span>` : ''}
                    ${activity.duration ? `<span class="activity-duration">${activity.duration}ms</span>` : ''}
                </div>
            </div>
        `;

        // Add entrance animation
        item.style.animation = 'slideInRight 0.3s ease-out';

        return item;
    }

    /**
     * Escape HTML to prevent XSS
     * @param {string} text - Text to escape
     * @returns {string} Escaped HTML
     */
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Sanitize URL to prevent XSS via javascript: protocol
     * @param {string} url - URL to sanitize
     * @returns {string} Sanitized URL or '#' if invalid
     */
    function sanitizeUrl(url) {
        if (!url || typeof url !== 'string') return '#';

        // Trim whitespace
        url = url.trim();

        // Only allow http, https, and relative URLs
        if (url.startsWith('http://') || url.startsWith('https://') || url.startsWith('/')) {
            return url;
        }

        // Block javascript:, data:, vbscript:, etc.
        const protocol = url.split(':')[0].toLowerCase();
        if (['javascript', 'data', 'vbscript', 'file'].includes(protocol)) {
            return '#';
        }

        // For other URLs (like relative paths without /), prefix with ./
        if (!url.includes(':')) {
            return './' + url;
        }

        // Default: block unknown protocols
        return '#';
    }

    /**
     * Render activity feed
     * @param {Array} activities - Array of activity items
     */
    function renderActivityFeed(activities) {
        if (!elements.activityFeed) return;

        if (!activities || activities.length === 0) {
            elements.activityFeed.innerHTML = `
                <div class="activity-placeholder">
                    <p>No activity recorded yet</p>
                </div>
            `;
            return;
        }

        elements.activityFeed.innerHTML = '';
        activities.forEach((activity, index) => {
            const item = renderActivityItem(activity);
            item.style.animationDelay = `${index * 50}ms`;
            elements.activityFeed.appendChild(item);
        });
    }

    /**
     * Update pagination controls
     */
    function updatePagination() {
        if (elements.pageInfo) {
            elements.pageInfo.textContent = `Page ${state.currentPage} of ${state.totalPages}`;
        }
        if (elements.prevPage) {
            elements.prevPage.disabled = state.currentPage <= 1;
        }
        if (elements.nextPage) {
            elements.nextPage.disabled = state.currentPage >= state.totalPages;
        }
    }

    /**
     * Load activity feed from API
     */
    async function loadActivity() {
        try {
            const data = await ObservatoryAPI.fetchActivity(state.currentPage, state.itemsPerPage);
            renderActivityFeed(data.items);
            state.totalPages = Math.ceil(data.total / state.itemsPerPage) || 1;
            updatePagination();
            updateLastUpdateTime();
        } catch (error) {
            console.error('Failed to load activity:', error);
            if (error.isNetworkError || error.status === 404) {
                renderMockActivity();
            } else {
                elements.activityFeed.innerHTML = `
                    <div class="error-message">
                        Failed to load activity: ${escapeHtml(error.message)}
                    </div>
                `;
            }
        }
    }

    /**
     * Render mock activity for demo purposes
     */
    function renderMockActivity() {
        const mockActivities = [
            { type: 'query', message: 'User queried: "What are the main components of AGENT-33?"', timestamp: new Date(Date.now() - 120000) },
            { type: 'ingest', message: 'Ingested 15 documents from collected/docs/', timestamp: new Date(Date.now() - 300000) },
            { type: 'workflow', message: 'Workflow "research-pipeline" completed successfully', timestamp: new Date(Date.now() - 600000), duration: 2340 },
            { type: 'agent', message: 'Agent "researcher" spawned for task analysis', timestamp: new Date(Date.now() - 900000) },
            { type: 'chat', message: 'New chat session started', timestamp: new Date(Date.now() - 1200000) },
            { type: 'system', message: 'Knowledge graph updated with 42 new nodes', timestamp: new Date(Date.now() - 1800000) },
        ];
        renderActivityFeed(mockActivities);
        state.totalPages = 1;
        updatePagination();
    }

    /**
     * Load stats from API
     */
    async function loadStats() {
        try {
            const stats = await ObservatoryAPI.fetchStats();
            updateStatsDisplay(stats);
        } catch (error) {
            console.error('Failed to load stats:', error);
            if (error.isNetworkError || error.status === 404) {
                updateStatsDisplay({
                    facts_count: 1247,
                    sources_count: 42,
                    queries_today: 156,
                    uptime: '3d 14h',
                });
            }
        }
    }

    /**
     * Update stats display with animation
     * @param {Object} stats - Stats data
     */
    function updateStatsDisplay(stats) {
        const elements = {
            facts: document.getElementById('stat-facts'),
            sources: document.getElementById('stat-sources'),
            queries: document.getElementById('stat-queries'),
            uptime: document.getElementById('stat-uptime'),
        };

        if (elements.facts) animateValue(elements.facts, stats.facts_count);
        if (elements.sources) animateValue(elements.sources, stats.sources_count);
        if (elements.queries) animateValue(elements.queries, stats.queries_today);
        if (elements.uptime) elements.uptime.textContent = stats.uptime || '--';
    }

    /**
     * Animate a numeric value change
     * @param {HTMLElement} element - Element to update
     * @param {number} newValue - New value
     */
    function animateValue(element, newValue) {
        const formatted = formatNumber(newValue);
        if (element.textContent !== formatted) {
            element.classList.add('updating');
            element.textContent = formatted;
            setTimeout(() => element.classList.remove('updating'), 300);
        }
    }

    /**
     * Format large numbers with abbreviations
     * @param {number} num - Number to format
     * @returns {string} Formatted number
     */
    function formatNumber(num) {
        if (num === undefined || num === null) return '--';
        if (num >= 1000000) return (num / 1000000).toFixed(1) + 'M';
        if (num >= 1000) return (num / 1000).toFixed(1) + 'K';
        return num.toString();
    }

    /**
     * Update last update timestamp
     */
    function updateLastUpdateTime() {
        if (elements.lastUpdate) {
            elements.lastUpdate.textContent = 'Last update: ' + new Date().toLocaleTimeString();
        }
    }

    /**
     * Connect to activity stream with enhanced callbacks
     */
    function connectActivityStream() {
        if (state.streamController) {
            state.streamController.close();
        }

        state.streamController = ObservatoryAPI.connectActivityStream({
            onActivity: (activity) => {
                if (elements.activityFeed && state.currentPage === 1) {
                    const placeholder = elements.activityFeed.querySelector('.activity-placeholder');
                    if (placeholder) {
                        elements.activityFeed.innerHTML = '';
                    }

                    const item = renderActivityItem(activity);
                    elements.activityFeed.insertBefore(item, elements.activityFeed.firstChild);

                    // Keep feed size manageable
                    while (elements.activityFeed.children.length > state.itemsPerPage) {
                        elements.activityFeed.removeChild(elements.activityFeed.lastChild);
                    }
                }
                updateLastUpdateTime();
            },
            onConnect: () => {
                updateConnectionStatus('connected');
                console.log('Activity stream connected');
            },
            onDisconnect: () => {
                updateConnectionStatus('disconnected');
                console.log('Activity stream disconnected');
            },
            onReconnecting: (data) => {
                updateConnectionStatus('reconnecting', data);
                console.log(`Reconnecting attempt ${data.attempt}/${data.maxAttempts}, delay: ${data.delay}ms`);
            },
            onError: (error) => {
                console.error('Activity stream error:', error);
                if (error.message === 'Max reconnection attempts reached') {
                    updateConnectionStatus('disconnected');
                    showNotification('Connection lost. Please refresh the page.', 'error');
                }
            },
            onStats: (stats) => {
                updateStatsDisplay(stats);
            },
        });
    }

    /**
     * Show a notification message
     * @param {string} message - Message to display
     * @param {string} type - Notification type (info, success, warning, error)
     */
    function showNotification(message, type = 'info') {
        let container = document.getElementById('notification-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'notification-container';
            container.className = 'notification-container';
            document.body.appendChild(container);
        }

        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <span class="notification-message">${escapeHtml(message)}</span>
            <button class="notification-close">&times;</button>
        `;

        notification.querySelector('.notification-close').addEventListener('click', () => {
            notification.remove();
        });

        container.appendChild(notification);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            notification.classList.add('fade-out');
            setTimeout(() => notification.remove(), 300);
        }, 5000);
    }

    /**
     * Add a chat message to the display
     * @param {string} role - 'user' or 'agent'
     * @param {string} content - Message content
     * @param {Array} sources - Optional sources array
     */
    function addChatMessage(role, content, sources = []) {
        if (!elements.chatMessages) return;

        const welcome = elements.chatMessages.querySelector('.chat-welcome');
        if (welcome) {
            welcome.remove();
        }

        const message = document.createElement('div');
        message.className = `chat-message ${role}`;

        let sourcesHtml = '';
        if (sources && sources.length > 0) {
            sourcesHtml = `
                <div class="chat-sources">
                    <div class="chat-sources-title">Sources:</div>
                    ${sources.map(s => `
                        <a class="chat-source-item" href="${sanitizeUrl(s.url || s.source_url || '#')}" target="_blank" rel="noopener noreferrer">
                            ${escapeHtml(s.title || s.text || s)}
                        </a>
                    `).join('')}
                </div>
            `;
        }

        message.innerHTML = `
            <div class="chat-bubble">
                ${escapeHtml(content)}
                ${sourcesHtml}
            </div>
        `;

        elements.chatMessages.appendChild(message);
        elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;

        state.chatHistory.push({ role, content, sources });
    }

    /**
     * Add a loading indicator to chat
     * @returns {HTMLElement} Loading element
     */
    function addChatLoading() {
        const loading = document.createElement('div');
        loading.className = 'chat-message agent chat-loading';
        loading.innerHTML = `
            <div class="chat-bubble">
                <div class="typing-indicator">
                    <span></span><span></span><span></span>
                </div>
            </div>
        `;
        elements.chatMessages.appendChild(loading);
        elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
        return loading;
    }

    /**
     * Handle chat form submission
     * @param {Event} event - Form submit event
     */
    async function handleChatSubmit(event) {
        event.preventDefault();

        const question = elements.chatInput?.value.trim();
        if (!question || state.chatLoading) return;

        state.chatLoading = true;
        elements.chatInput.disabled = true;
        elements.chatSubmit.disabled = true;
        elements.chatInput.value = '';

        addChatMessage('user', question);
        const loadingEl = addChatLoading();

        try {
            const response = await ObservatoryAPI.askAgent(question);
            loadingEl.remove();
            addChatMessage('agent', response.answer, response.sources);
        } catch (error) {
            console.error('Failed to get response:', error);
            loadingEl.remove();

            if (error.isNetworkError || error.status === 404) {
                addChatMessage('agent', 'The Observatory API is not yet connected. This is a placeholder response demonstrating the chat interface. Once the backend is running, you will receive real answers from the AGENT-33 knowledge base.');
            } else {
                addChatMessage('agent', `Sorry, I encountered an error: ${error.message}`);
            }
        } finally {
            state.chatLoading = false;
            elements.chatInput.disabled = false;
            elements.chatSubmit.disabled = false;
            elements.chatInput.focus();
        }
    }

    /**
     * Initialize knowledge graph
     */
    function initKnowledgeGraph() {
        if (typeof KnowledgeGraph === 'undefined') {
            console.warn('KnowledgeGraph module not loaded');
            return;
        }

        KnowledgeGraph.init('graph-container', {
            searchInputId: 'graph-search',
            typeFilterId: 'graph-type-filter',
            detailsPanelId: 'graph-details',
        });

        loadKnowledgeGraph();
    }

    /**
     * Load knowledge graph data
     */
    async function loadKnowledgeGraph() {
        if (typeof KnowledgeGraph === 'undefined') return;

        try {
            const data = await ObservatoryAPI.fetchKnowledgeGraph(
                CONFIG.graphNodeLimit,
                state.graphFilter
            );
            KnowledgeGraph.loadData(data);
        } catch (error) {
            console.error('Failed to load knowledge graph:', error);

            if (error.isNetworkError || error.status === 404) {
                // Load mock data for demo
                KnowledgeGraph.loadData(getMockGraphData());
            }
        }
    }

    /**
     * Get mock graph data for demo
     * @returns {Object} Mock graph data
     */
    function getMockGraphData() {
        return {
            nodes: [
                { id: 'agent33', label: 'AGENT-33', type: 'entity', description: 'Multi-agent orchestration framework' },
                { id: 'orchestrator', label: 'Orchestrator', type: 'entity', description: 'Central coordination component' },
                { id: 'knowledge', label: 'Knowledge Base', type: 'entity', description: 'Facts and relationships storage' },
                { id: 'workflows', label: 'Workflows', type: 'entity', description: 'Task execution pipelines' },
                { id: 'agents', label: 'Agent Pool', type: 'entity', description: 'Specialized AI agents' },
                { id: 'rag', label: 'RAG System', type: 'entity', description: 'Retrieval-augmented generation' },
                { id: 'memory', label: 'Memory Layer', type: 'entity', description: 'Persistent context storage' },
                { id: 'intake', label: 'Intake Process', type: 'event', description: 'Document ingestion workflow' },
                { id: 'research', label: 'Research Agent', type: 'entity', description: 'Information gathering agent' },
                { id: 'analyst', label: 'Analyst Agent', type: 'entity', description: 'Data analysis agent' },
                { id: 'coordinator', label: 'Coordinator Agent', type: 'entity', description: 'Task delegation agent' },
                { id: 'manages', label: 'manages', type: 'relationship' },
                { id: 'uses', label: 'uses', type: 'relationship' },
                { id: 'produces', label: 'produces', type: 'relationship' },
            ],
            edges: [
                { source: 'agent33', target: 'orchestrator', label: 'contains' },
                { source: 'orchestrator', target: 'workflows', label: 'executes' },
                { source: 'orchestrator', target: 'agents', label: 'manages' },
                { source: 'orchestrator', target: 'knowledge', label: 'queries' },
                { source: 'knowledge', target: 'rag', label: 'powers' },
                { source: 'knowledge', target: 'memory', label: 'includes' },
                { source: 'agents', target: 'research', label: 'includes' },
                { source: 'agents', target: 'analyst', label: 'includes' },
                { source: 'agents', target: 'coordinator', label: 'includes' },
                { source: 'intake', target: 'knowledge', label: 'populates' },
                { source: 'research', target: 'knowledge', label: 'reads' },
                { source: 'analyst', target: 'knowledge', label: 'analyzes' },
            ],
        };
    }

    /**
     * Set up event listeners
     */
    function setupEventListeners() {
        // Pagination
        elements.prevPage?.addEventListener('click', () => {
            if (state.currentPage > 1) {
                state.currentPage--;
                loadActivity();
            }
        });

        elements.nextPage?.addEventListener('click', () => {
            if (state.currentPage < state.totalPages) {
                state.currentPage++;
                loadActivity();
            }
        });

        // Refresh button
        elements.refreshActivity?.addEventListener('click', loadActivity);

        // Chat form
        elements.chatForm?.addEventListener('submit', handleChatSubmit);

        // Graph controls
        elements.graphZoomIn?.addEventListener('click', () => KnowledgeGraph?.zoomIn());
        elements.graphZoomOut?.addEventListener('click', () => KnowledgeGraph?.zoomOut());
        elements.graphReset?.addEventListener('click', () => KnowledgeGraph?.resetZoom());
        elements.graphRefresh?.addEventListener('click', loadKnowledgeGraph);

        // Handle visibility change to reconnect if needed
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden && !state.connected && !state.reconnecting) {
                connectActivityStream();
            }
        });

        // Keyboard shortcuts
        document.addEventListener('keydown', (event) => {
            // Escape to close details panel
            if (event.key === 'Escape') {
                KnowledgeGraph?.hideNodeDetails();
            }

            // Ctrl/Cmd + Enter to send chat
            if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
                if (document.activeElement === elements.chatInput) {
                    elements.chatForm?.dispatchEvent(new Event('submit'));
                }
            }
        });

        // Click outside graph details to close
        document.addEventListener('click', (event) => {
            if (elements.graphDetails &&
                elements.graphDetails.classList.contains('visible') &&
                !elements.graphDetails.contains(event.target) &&
                !event.target.closest('.graph-node')) {
                KnowledgeGraph?.hideNodeDetails();
            }
        });
    }

    /**
     * Check server health and update status
     */
    async function checkHealth() {
        try {
            await ObservatoryAPI.checkHealth();
            updateConnectionStatus('connected');
        } catch (error) {
            console.warn('Health check failed:', error);
            updateConnectionStatus('disconnected');
        }
    }

    /**
     * Start periodic polling intervals
     */
    function startPolling() {
        // Stats polling every 30 seconds
        loadStats();
        state.statsInterval = setInterval(loadStats, CONFIG.statsPollingInterval);

        // Graph refresh every 60 seconds
        state.graphInterval = setInterval(loadKnowledgeGraph, CONFIG.graphRefreshInterval);
    }

    /**
     * Stop polling intervals
     */
    function stopPolling() {
        if (state.statsInterval) {
            clearInterval(state.statsInterval);
            state.statsInterval = null;
        }
        if (state.graphInterval) {
            clearInterval(state.graphInterval);
            state.graphInterval = null;
        }
    }

    /**
     * Initialize the application
     */
    function init() {
        initElements();
        setupEventListeners();

        // Initial data load
        checkHealth();
        loadActivity();
        startPolling();

        // Initialize knowledge graph
        initKnowledgeGraph();

        // Connect to live stream
        connectActivityStream();

        console.log('AGENT-33 Observatory initialized');
    }

    /**
     * Cleanup on page unload
     */
    function cleanup() {
        stopPolling();

        if (state.streamController) {
            state.streamController.close();
        }

        if (typeof KnowledgeGraph !== 'undefined') {
            KnowledgeGraph.destroy();
        }
    }

    // Handle cleanup on page unload
    window.addEventListener('beforeunload', cleanup);

    // Start when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Expose for debugging
    window.ObservatoryApp = {
        state,
        loadActivity,
        loadStats,
        loadKnowledgeGraph,
        connectActivityStream,
        showNotification,
    };
})();
