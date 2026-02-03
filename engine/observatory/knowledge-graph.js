/**
 * AGENT-33 Observatory - Knowledge Graph Visualization
 *
 * D3.js force-directed graph for visualizing knowledge relationships.
 * Features: zoom/pan, drag behavior, node filtering, search, detail panel
 */

const KnowledgeGraph = (function () {
    'use strict';

    // Configuration
    const CONFIG = {
        nodeRadius: {
            entity: 12,
            relationship: 8,
            event: 10,
            default: 10,
        },
        colors: {
            entity: '#3fb950',      // Green
            relationship: '#58a6ff', // Blue
            event: '#a371f7',        // Purple
            default: '#8b949e',      // Gray
        },
        simulation: {
            linkDistance: 80,
            linkStrength: 0.5,
            chargeStrength: -300,
            collisionRadius: 20,
            centerStrength: 0.1,
            alphaDecay: 0.02,
        },
        animation: {
            duration: 300,
        },
    };

    // State
    let svg = null;
    let container = null;
    let simulation = null;
    let nodes = [];
    let links = [];
    let nodeElements = null;
    let linkElements = null;
    let labelElements = null;
    let zoom = null;
    let selectedNode = null;
    let filterType = 'all';
    let searchQuery = '';

    // DOM references
    let graphContainer = null;
    let detailsPanel = null;
    let searchInput = null;
    let typeFilter = null;

    /**
     * Initialize the knowledge graph
     * @param {string} containerId - ID of the container element
     * @param {Object} options - Configuration options
     */
    function init(containerId, options = {}) {
        graphContainer = document.getElementById(containerId);
        if (!graphContainer) {
            console.error('Knowledge graph container not found:', containerId);
            return;
        }

        // Clear any existing content
        graphContainer.innerHTML = '';

        // Create SVG
        const rect = graphContainer.getBoundingClientRect();
        const width = rect.width || 800;
        const height = rect.height || 500;

        svg = d3.select(`#${containerId}`)
            .append('svg')
            .attr('class', 'knowledge-graph-svg')
            .attr('width', '100%')
            .attr('height', '100%')
            .attr('viewBox', `0 0 ${width} ${height}`);

        // Add gradient definitions for visual polish
        const defs = svg.append('defs');

        // Glow filter for selected nodes
        const filter = defs.append('filter')
            .attr('id', 'glow')
            .attr('x', '-50%')
            .attr('y', '-50%')
            .attr('width', '200%')
            .attr('height', '200%');

        filter.append('feGaussianBlur')
            .attr('stdDeviation', '3')
            .attr('result', 'coloredBlur');

        const feMerge = filter.append('feMerge');
        feMerge.append('feMergeNode').attr('in', 'coloredBlur');
        feMerge.append('feMergeNode').attr('in', 'SourceGraphic');

        // Arrow marker for directed edges
        defs.append('marker')
            .attr('id', 'arrowhead')
            .attr('viewBox', '0 -5 10 10')
            .attr('refX', 20)
            .attr('refY', 0)
            .attr('markerWidth', 6)
            .attr('markerHeight', 6)
            .attr('orient', 'auto')
            .append('path')
            .attr('d', 'M0,-5L10,0L0,5')
            .attr('fill', '#6e7681');

        // Create main container group for zoom/pan
        container = svg.append('g').attr('class', 'graph-container');

        // Create groups for links (below) and nodes (above)
        container.append('g').attr('class', 'links-layer');
        container.append('g').attr('class', 'nodes-layer');
        container.append('g').attr('class', 'labels-layer');

        // Initialize zoom behavior
        zoom = d3.zoom()
            .scaleExtent([0.1, 4])
            .on('zoom', (event) => {
                container.attr('transform', event.transform);
            });

        svg.call(zoom);

        // Initialize force simulation
        simulation = d3.forceSimulation()
            .force('link', d3.forceLink()
                .id(d => d.id)
                .distance(CONFIG.simulation.linkDistance)
                .strength(CONFIG.simulation.linkStrength))
            .force('charge', d3.forceManyBody()
                .strength(CONFIG.simulation.chargeStrength))
            .force('center', d3.forceCenter(width / 2, height / 2)
                .strength(CONFIG.simulation.centerStrength))
            .force('collision', d3.forceCollide()
                .radius(CONFIG.simulation.collisionRadius))
            .alphaDecay(CONFIG.simulation.alphaDecay)
            .on('tick', ticked);

        // Set up resize handler
        window.addEventListener('resize', handleResize);

        // Initialize UI controls if provided
        if (options.searchInputId) {
            searchInput = document.getElementById(options.searchInputId);
            if (searchInput) {
                searchInput.addEventListener('input', debounce(handleSearch, 300));
            }
        }

        if (options.typeFilterId) {
            typeFilter = document.getElementById(options.typeFilterId);
            if (typeFilter) {
                typeFilter.addEventListener('change', handleTypeFilter);
            }
        }

        if (options.detailsPanelId) {
            detailsPanel = document.getElementById(options.detailsPanelId);
        }

        console.log('Knowledge graph initialized');
    }

    /**
     * Load and render graph data
     * @param {Object} data - Graph data with nodes and edges
     */
    function loadData(data) {
        if (!data || !data.nodes) {
            console.warn('No graph data provided');
            showEmptyState();
            return;
        }

        nodes = data.nodes.map(n => ({
            ...n,
            x: n.x || undefined,
            y: n.y || undefined,
        }));
        links = (data.edges || data.links || []).map(e => ({
            ...e,
            source: e.source,
            target: e.target,
        }));

        render();
    }

    /**
     * Render the graph
     */
    function render() {
        if (!svg) return;

        // Filter nodes based on current filters
        const filteredNodes = filterNodes(nodes);
        const nodeIds = new Set(filteredNodes.map(n => n.id));
        const filteredLinks = links.filter(l => {
            const sourceId = typeof l.source === 'object' ? l.source.id : l.source;
            const targetId = typeof l.target === 'object' ? l.target.id : l.target;
            return nodeIds.has(sourceId) && nodeIds.has(targetId);
        });

        // Update links
        const linksLayer = container.select('.links-layer');
        linkElements = linksLayer.selectAll('.graph-link')
            .data(filteredLinks, d => `${d.source.id || d.source}-${d.target.id || d.target}`);

        linkElements.exit()
            .transition()
            .duration(CONFIG.animation.duration)
            .style('opacity', 0)
            .remove();

        const linkEnter = linkElements.enter()
            .append('line')
            .attr('class', 'graph-link')
            .style('opacity', 0)
            .attr('marker-end', 'url(#arrowhead)');

        linkElements = linkEnter.merge(linkElements);

        linkElements.transition()
            .duration(CONFIG.animation.duration)
            .style('opacity', 1);

        // Update nodes
        const nodesLayer = container.select('.nodes-layer');
        nodeElements = nodesLayer.selectAll('.graph-node')
            .data(filteredNodes, d => d.id);

        nodeElements.exit()
            .transition()
            .duration(CONFIG.animation.duration)
            .attr('r', 0)
            .remove();

        const nodeEnter = nodeElements.enter()
            .append('circle')
            .attr('class', 'graph-node')
            .attr('r', 0)
            .call(drag(simulation))
            .on('click', handleNodeClick)
            .on('mouseenter', handleNodeHover)
            .on('mouseleave', handleNodeLeave);

        nodeElements = nodeEnter.merge(nodeElements);

        nodeElements
            .attr('fill', d => getNodeColor(d))
            .attr('data-type', d => d.type || 'default')
            .classed('selected', d => selectedNode && d.id === selectedNode.id)
            .transition()
            .duration(CONFIG.animation.duration)
            .attr('r', d => getNodeRadius(d));

        // Update labels
        const labelsLayer = container.select('.labels-layer');
        labelElements = labelsLayer.selectAll('.graph-label')
            .data(filteredNodes, d => d.id);

        labelElements.exit()
            .transition()
            .duration(CONFIG.animation.duration)
            .style('opacity', 0)
            .remove();

        const labelEnter = labelElements.enter()
            .append('text')
            .attr('class', 'graph-label')
            .style('opacity', 0);

        labelElements = labelEnter.merge(labelElements);

        labelElements
            .text(d => truncateLabel(d.label || d.name || d.id, 15))
            .transition()
            .duration(CONFIG.animation.duration)
            .style('opacity', 1);

        // Update simulation
        simulation.nodes(filteredNodes);
        simulation.force('link').links(filteredLinks);
        simulation.alpha(0.5).restart();

        // Hide empty state if we have nodes
        if (filteredNodes.length > 0) {
            hideEmptyState();
        } else {
            showEmptyState('No matching nodes found');
        }
    }

    /**
     * Tick handler for force simulation
     */
    function ticked() {
        if (linkElements) {
            linkElements
                .attr('x1', d => d.source.x)
                .attr('y1', d => d.source.y)
                .attr('x2', d => d.target.x)
                .attr('y2', d => d.target.y);
        }

        if (nodeElements) {
            nodeElements
                .attr('cx', d => d.x)
                .attr('cy', d => d.y);
        }

        if (labelElements) {
            labelElements
                .attr('x', d => d.x)
                .attr('y', d => d.y + getNodeRadius(d) + 14);
        }
    }

    /**
     * Create drag behavior
     * @param {Object} simulation - D3 force simulation
     * @returns {Function} Drag behavior
     */
    function drag(simulation) {
        function dragstarted(event, d) {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
        }

        function dragged(event, d) {
            d.fx = event.x;
            d.fy = event.y;
        }

        function dragended(event, d) {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
        }

        return d3.drag()
            .on('start', dragstarted)
            .on('drag', dragged)
            .on('end', dragended);
    }

    /**
     * Handle node click
     * @param {Event} event - Click event
     * @param {Object} d - Node data
     */
    function handleNodeClick(event, d) {
        event.stopPropagation();

        // Toggle selection
        if (selectedNode && selectedNode.id === d.id) {
            selectedNode = null;
            hideNodeDetails();
        } else {
            selectedNode = d;
            showNodeDetails(d);
        }

        // Update visual state
        nodeElements.classed('selected', n => selectedNode && n.id === selectedNode.id);

        // Highlight connected nodes and links
        highlightConnections(selectedNode);
    }

    /**
     * Handle node hover
     * @param {Event} event - Mouse event
     * @param {Object} d - Node data
     */
    function handleNodeHover(event, d) {
        d3.select(event.target)
            .classed('hovered', true)
            .attr('r', getNodeRadius(d) * 1.3);

        // Show tooltip
        showTooltip(event, d);
    }

    /**
     * Handle node mouse leave
     * @param {Event} event - Mouse event
     * @param {Object} d - Node data
     */
    function handleNodeLeave(event, d) {
        d3.select(event.target)
            .classed('hovered', false)
            .attr('r', getNodeRadius(d));

        hideTooltip();
    }

    /**
     * Show tooltip for a node
     * @param {Event} event - Mouse event
     * @param {Object} d - Node data
     */
    function showTooltip(event, d) {
        let tooltip = document.getElementById('graph-tooltip');
        if (!tooltip) {
            tooltip = document.createElement('div');
            tooltip.id = 'graph-tooltip';
            tooltip.className = 'graph-tooltip';
            document.body.appendChild(tooltip);
        }

        tooltip.innerHTML = `
            <div class="tooltip-title">${escapeHtml(d.label || d.name || d.id)}</div>
            <div class="tooltip-type">${escapeHtml(d.type || 'Unknown')}</div>
            ${d.description ? `<div class="tooltip-desc">${escapeHtml(truncateLabel(d.description, 100))}</div>` : ''}
        `;

        tooltip.style.left = (event.pageX + 10) + 'px';
        tooltip.style.top = (event.pageY + 10) + 'px';
        tooltip.classList.add('visible');
    }

    /**
     * Hide tooltip
     */
    function hideTooltip() {
        const tooltip = document.getElementById('graph-tooltip');
        if (tooltip) {
            tooltip.classList.remove('visible');
        }
    }

    /**
     * Show node details panel
     * @param {Object} node - Node data
     */
    function showNodeDetails(node) {
        if (!detailsPanel) return;

        const connections = getNodeConnections(node);

        detailsPanel.innerHTML = `
            <div class="details-header">
                <span class="details-type-badge" style="background-color: ${getNodeColor(node)}20; color: ${getNodeColor(node)}">
                    ${escapeHtml(node.type || 'Node')}
                </span>
                <button class="details-close" onclick="KnowledgeGraph.hideNodeDetails()">&times;</button>
            </div>
            <h3 class="details-title">${escapeHtml(node.label || node.name || node.id)}</h3>
            ${node.description ? `<p class="details-description">${escapeHtml(node.description)}</p>` : ''}

            <div class="details-section">
                <h4>Properties</h4>
                <dl class="details-properties">
                    <dt>ID</dt><dd>${escapeHtml(node.id)}</dd>
                    ${node.source ? `<dt>Source</dt><dd>${escapeHtml(node.source)}</dd>` : ''}
                    ${node.created ? `<dt>Created</dt><dd>${formatDate(node.created)}</dd>` : ''}
                    ${node.confidence ? `<dt>Confidence</dt><dd>${(node.confidence * 100).toFixed(0)}%</dd>` : ''}
                </dl>
            </div>

            ${connections.length > 0 ? `
                <div class="details-section">
                    <h4>Connections (${connections.length})</h4>
                    <ul class="details-connections">
                        ${connections.slice(0, 10).map(c => `
                            <li class="connection-item" onclick="KnowledgeGraph.focusNode('${escapeHtml(c.id)}')">
                                <span class="connection-rel">${escapeHtml(c.relationship)}</span>
                                <span class="connection-node">${escapeHtml(c.label)}</span>
                            </li>
                        `).join('')}
                        ${connections.length > 10 ? `<li class="connection-more">+${connections.length - 10} more</li>` : ''}
                    </ul>
                </div>
            ` : ''}
        `;

        detailsPanel.classList.add('visible');
    }

    /**
     * Hide node details panel
     */
    function hideNodeDetails() {
        if (detailsPanel) {
            detailsPanel.classList.remove('visible');
        }
        selectedNode = null;
        if (nodeElements) {
            nodeElements.classed('selected', false);
        }
        highlightConnections(null);
    }

    /**
     * Get connections for a node
     * @param {Object} node - Node to get connections for
     * @returns {Array} Array of connection objects
     */
    function getNodeConnections(node) {
        if (!node) return [];

        const connections = [];

        links.forEach(link => {
            const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
            const targetId = typeof link.target === 'object' ? link.target.id : link.target;

            if (sourceId === node.id) {
                const targetNode = nodes.find(n => n.id === targetId);
                if (targetNode) {
                    connections.push({
                        id: targetNode.id,
                        label: targetNode.label || targetNode.name || targetNode.id,
                        relationship: link.label || link.type || 'connected to',
                        direction: 'outgoing',
                    });
                }
            } else if (targetId === node.id) {
                const sourceNode = nodes.find(n => n.id === sourceId);
                if (sourceNode) {
                    connections.push({
                        id: sourceNode.id,
                        label: sourceNode.label || sourceNode.name || sourceNode.id,
                        relationship: link.label || link.type || 'connected from',
                        direction: 'incoming',
                    });
                }
            }
        });

        return connections;
    }

    /**
     * Highlight connections for a selected node
     * @param {Object|null} node - Selected node or null to clear
     */
    function highlightConnections(node) {
        if (!linkElements || !nodeElements) return;

        if (!node) {
            // Reset all to normal state
            linkElements.classed('dimmed', false).classed('highlighted', false);
            nodeElements.classed('dimmed', false).classed('highlighted', false);
            return;
        }

        const connectedIds = new Set([node.id]);
        links.forEach(link => {
            const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
            const targetId = typeof link.target === 'object' ? link.target.id : link.target;
            if (sourceId === node.id) connectedIds.add(targetId);
            if (targetId === node.id) connectedIds.add(sourceId);
        });

        nodeElements
            .classed('dimmed', d => !connectedIds.has(d.id))
            .classed('highlighted', d => connectedIds.has(d.id) && d.id !== node.id);

        linkElements
            .classed('dimmed', link => {
                const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
                const targetId = typeof link.target === 'object' ? link.target.id : link.target;
                return sourceId !== node.id && targetId !== node.id;
            })
            .classed('highlighted', link => {
                const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
                const targetId = typeof link.target === 'object' ? link.target.id : link.target;
                return sourceId === node.id || targetId === node.id;
            });
    }

    /**
     * Focus on a specific node
     * @param {string} nodeId - ID of node to focus
     */
    function focusNode(nodeId) {
        const node = nodes.find(n => n.id === nodeId);
        if (!node || !svg) return;

        // Center view on node
        const rect = graphContainer.getBoundingClientRect();
        const width = rect.width;
        const height = rect.height;

        const transform = d3.zoomIdentity
            .translate(width / 2, height / 2)
            .scale(1.5)
            .translate(-node.x, -node.y);

        svg.transition()
            .duration(750)
            .call(zoom.transform, transform);

        // Select the node
        selectedNode = node;
        showNodeDetails(node);
        nodeElements.classed('selected', n => n.id === nodeId);
        highlightConnections(node);
    }

    /**
     * Handle search input
     * @param {Event} event - Input event
     */
    function handleSearch(event) {
        searchQuery = event.target.value.toLowerCase().trim();
        render();
    }

    /**
     * Handle type filter change
     * @param {Event} event - Change event
     */
    function handleTypeFilter(event) {
        filterType = event.target.value;
        render();
    }

    /**
     * Filter nodes based on current search and type filters
     * @param {Array} nodes - All nodes
     * @returns {Array} Filtered nodes
     */
    function filterNodes(allNodes) {
        return allNodes.filter(node => {
            // Type filter
            if (filterType !== 'all' && node.type !== filterType) {
                return false;
            }

            // Search filter
            if (searchQuery) {
                const searchFields = [
                    node.label,
                    node.name,
                    node.id,
                    node.description,
                ].filter(Boolean).join(' ').toLowerCase();

                return searchFields.includes(searchQuery);
            }

            return true;
        });
    }

    /**
     * Get node color based on type
     * @param {Object} node - Node data
     * @returns {string} Color hex value
     */
    function getNodeColor(node) {
        return CONFIG.colors[node.type] || CONFIG.colors.default;
    }

    /**
     * Get node radius based on type
     * @param {Object} node - Node data
     * @returns {number} Radius in pixels
     */
    function getNodeRadius(node) {
        return CONFIG.nodeRadius[node.type] || CONFIG.nodeRadius.default;
    }

    /**
     * Handle window resize
     */
    function handleResize() {
        if (!graphContainer || !svg) return;

        const rect = graphContainer.getBoundingClientRect();
        svg.attr('viewBox', `0 0 ${rect.width} ${rect.height}`);

        // Update center force
        if (simulation) {
            simulation.force('center', d3.forceCenter(rect.width / 2, rect.height / 2));
            simulation.alpha(0.1).restart();
        }
    }

    /**
     * Show empty state message
     * @param {string} message - Message to display
     */
    function showEmptyState(message = 'No knowledge graph data available') {
        if (!graphContainer) return;

        let emptyState = graphContainer.querySelector('.graph-empty-state');
        if (!emptyState) {
            emptyState = document.createElement('div');
            emptyState.className = 'graph-empty-state';
            graphContainer.appendChild(emptyState);
        }

        emptyState.innerHTML = `
            <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <circle cx="12" cy="12" r="3"/>
                <circle cx="19" cy="5" r="2"/>
                <circle cx="5" cy="5" r="2"/>
                <circle cx="5" cy="19" r="2"/>
                <circle cx="19" cy="19" r="2"/>
                <line x1="12" y1="9" x2="12" y2="7"/>
                <line x1="9.5" y1="13.5" x2="6.5" y2="16.5"/>
                <line x1="14.5" y1="13.5" x2="17.5" y2="16.5"/>
            </svg>
            <p>${escapeHtml(message)}</p>
        `;

        emptyState.style.display = 'flex';
    }

    /**
     * Hide empty state
     */
    function hideEmptyState() {
        if (!graphContainer) return;

        const emptyState = graphContainer.querySelector('.graph-empty-state');
        if (emptyState) {
            emptyState.style.display = 'none';
        }
    }

    /**
     * Reset zoom to default view
     */
    function resetZoom() {
        if (!svg || !graphContainer) return;

        const rect = graphContainer.getBoundingClientRect();
        svg.transition()
            .duration(750)
            .call(zoom.transform, d3.zoomIdentity.translate(0, 0).scale(1));
    }

    /**
     * Zoom in
     */
    function zoomIn() {
        if (!svg) return;
        svg.transition().duration(300).call(zoom.scaleBy, 1.3);
    }

    /**
     * Zoom out
     */
    function zoomOut() {
        if (!svg) return;
        svg.transition().duration(300).call(zoom.scaleBy, 0.7);
    }

    /**
     * Destroy the graph and clean up
     */
    function destroy() {
        window.removeEventListener('resize', handleResize);

        if (simulation) {
            simulation.stop();
        }

        if (graphContainer) {
            graphContainer.innerHTML = '';
        }

        hideTooltip();

        svg = null;
        container = null;
        simulation = null;
        nodes = [];
        links = [];
        nodeElements = null;
        linkElements = null;
        labelElements = null;
        zoom = null;
        selectedNode = null;
    }

    // Utility functions

    /**
     * Escape HTML to prevent XSS
     * @param {string} text - Text to escape
     * @returns {string} Escaped HTML
     */
    function escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Truncate label with ellipsis
     * @param {string} text - Text to truncate
     * @param {number} maxLength - Maximum length
     * @returns {string} Truncated text
     */
    function truncateLabel(text, maxLength) {
        if (!text || text.length <= maxLength) return text || '';
        return text.substring(0, maxLength - 3) + '...';
    }

    /**
     * Format date for display
     * @param {string|Date} date - Date to format
     * @returns {string} Formatted date
     */
    function formatDate(date) {
        return new Date(date).toLocaleDateString();
    }

    /**
     * Debounce function
     * @param {Function} func - Function to debounce
     * @param {number} wait - Wait time in ms
     * @returns {Function} Debounced function
     */
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    // Public API
    return {
        init,
        loadData,
        render,
        focusNode,
        hideNodeDetails,
        resetZoom,
        zoomIn,
        zoomOut,
        destroy,
        setFilter: (type) => {
            filterType = type;
            render();
        },
        setSearch: (query) => {
            searchQuery = query.toLowerCase().trim();
            render();
        },
        getNodes: () => nodes,
        getLinks: () => links,
        getSelectedNode: () => selectedNode,
    };
})();

// Export for module systems if available
if (typeof module !== 'undefined' && module.exports) {
    module.exports = KnowledgeGraph;
}
