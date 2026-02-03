/**
 * AGENT-33 Observatory - Main Application
 *
 * Handles UI interactions, state management, and API integration.
 */

(function () {
    'use strict';

    // Application state
    const state = {
        connected: false,
        currentPage: 1,
        totalPages: 1,
        itemsPerPage: 15,
        eventSource: null,
        statsInterval: null,
        chatHistory: [],
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
    }

    /**
     * Update connection status indicator
     * @param {string} status - 'connected', 'disconnected', or 'connecting'
     */
    function updateConnectionStatus(status) {
        if (!elements.statusIndicator) return;

        elements.statusIndicator.classList.remove('connected', 'disconnected');

        switch (status) {
            case 'connected':
                elements.statusIndicator.classList.add('connected');
                elements.statusText.textContent = 'Connected';
                state.connected = true;
                break;
            case 'disconnected':
                elements.statusIndicator.classList.add('disconnected');
                elements.statusText.textContent = 'Disconnected';
                state.connected = false;
                break;
            default:
                elements.statusText.textContent = 'Connecting...';
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

        // Less than a minute ago
        if (diff < 60000) {
            return 'Just now';
        }

        // Less than an hour ago
        if (diff < 3600000) {
            const minutes = Math.floor(diff / 60000);
            return `${minutes}m ago`;
        }

        // Less than a day ago
        if (diff < 86400000) {
            const hours = Math.floor(diff / 3600000);
            return `${hours}h ago`;
        }

        // Show full date
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    /**
     * Get icon class for activity type
     * @param {string} type - Activity type
     * @returns {string} Icon class name
     */
    function getActivityIcon(type) {
        const icons = {
            query: 'Q',
            ingest: 'I',
            workflow: 'W',
            error: '!',
            chat: 'C',
            agent: 'A',
        };
        return icons[type] || '?';
    }

    /**
     * Render a single activity item
     * @param {Object} activity - Activity data
     * @returns {HTMLElement} Activity item element
     */
    function renderActivityItem(activity) {
        const item = document.createElement('div');
        item.className = 'activity-item';

        const iconClass = activity.type || 'query';
        const icon = getActivityIcon(activity.type);
        const timestamp = formatTimestamp(activity.timestamp || new Date());

        item.innerHTML = `
            <div class="activity-icon ${iconClass}">${icon}</div>
            <div class="activity-content">
                <div class="activity-message">${escapeHtml(activity.message || activity.content || 'Unknown activity')}</div>
                <div class="activity-meta">
                    <span class="activity-timestamp">${timestamp}</span>
                    ${activity.agent ? `<span class="activity-agent">${escapeHtml(activity.agent)}</span>` : ''}
                </div>
            </div>
        `;

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
        activities.forEach(activity => {
            elements.activityFeed.appendChild(renderActivityItem(activity));
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
                // API not available, show mock data for demo
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
            { type: 'workflow', message: 'Workflow "research-pipeline" completed successfully', timestamp: new Date(Date.now() - 600000) },
            { type: 'agent', message: 'Agent "researcher" spawned for task analysis', timestamp: new Date(Date.now() - 900000) },
            { type: 'chat', message: 'New chat session started', timestamp: new Date(Date.now() - 1200000) },
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
                // Show mock stats for demo
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
     * Update stats display
     * @param {Object} stats - Stats data
     */
    function updateStatsDisplay(stats) {
        const factEl = document.getElementById('stat-facts');
        const sourcesEl = document.getElementById('stat-sources');
        const queriesEl = document.getElementById('stat-queries');
        const uptimeEl = document.getElementById('stat-uptime');

        if (factEl) factEl.textContent = formatNumber(stats.facts_count);
        if (sourcesEl) sourcesEl.textContent = formatNumber(stats.sources_count);
        if (queriesEl) queriesEl.textContent = formatNumber(stats.queries_today);
        if (uptimeEl) uptimeEl.textContent = stats.uptime || '--';
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
     * Connect to activity stream
     */
    function connectActivityStream() {
        if (state.eventSource) {
            state.eventSource.close();
        }

        state.eventSource = ObservatoryAPI.connectActivityStream({
            onActivity: (activity) => {
                // Prepend new activity to feed
                if (elements.activityFeed && state.currentPage === 1) {
                    const item = renderActivityItem(activity);
                    const placeholder = elements.activityFeed.querySelector('.activity-placeholder');
                    if (placeholder) {
                        elements.activityFeed.innerHTML = '';
                    }
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
            },
            onDisconnect: () => {
                updateConnectionStatus('disconnected');
                // Attempt reconnect after delay
                setTimeout(connectActivityStream, 5000);
            },
            onError: (error) => {
                console.error('Activity stream error:', error);
            },
        });
    }

    /**
     * Add a chat message to the display
     * @param {string} role - 'user' or 'agent'
     * @param {string} content - Message content
     * @param {Array} sources - Optional sources array
     */
    function addChatMessage(role, content, sources = []) {
        if (!elements.chatMessages) return;

        // Remove welcome message if present
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
                    ${sources.map(s => `<a class="chat-source-item" href="${escapeHtml(s.url || '#')}" target="_blank">${escapeHtml(s.title || s)}</a>`).join('')}
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
     * Handle chat form submission
     * @param {Event} event - Form submit event
     */
    async function handleChatSubmit(event) {
        event.preventDefault();

        const question = elements.chatInput?.value.trim();
        if (!question) return;

        // Disable input while processing
        elements.chatInput.disabled = true;
        elements.chatSubmit.disabled = true;
        elements.chatInput.value = '';

        // Add user message
        addChatMessage('user', question);

        try {
            const response = await ObservatoryAPI.askAgent(question);
            addChatMessage('agent', response.answer, response.sources);
        } catch (error) {
            console.error('Failed to get response:', error);
            if (error.isNetworkError || error.status === 404) {
                // Mock response for demo
                addChatMessage('agent', 'The Observatory API is not yet connected. This is a placeholder response demonstrating the chat interface. Once the backend is running, you will receive real answers from the AGENT-33 knowledge base.');
            } else {
                addChatMessage('agent', `Sorry, I encountered an error: ${error.message}`);
            }
        } finally {
            elements.chatInput.disabled = false;
            elements.chatSubmit.disabled = false;
            elements.chatInput.focus();
        }
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

        // Handle visibility change to reconnect if needed
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden && !state.connected) {
                connectActivityStream();
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
     * Start periodic stats polling
     */
    function startStatsPolling() {
        // Initial load
        loadStats();

        // Poll every 30 seconds
        state.statsInterval = setInterval(loadStats, 30000);
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
        startStatsPolling();

        // Connect to live stream
        connectActivityStream();

        console.log('AGENT-33 Observatory initialized');
    }

    // Start when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
