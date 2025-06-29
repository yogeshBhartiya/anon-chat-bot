// Dashboard JavaScript for real-time updates and interactions

class DashboardManager {
    constructor() {
        this.updateInterval = 5000; // Update every 5 seconds
        this.intervalId = null;
        this.init();
    }

    init() {
        this.startRealTimeUpdates();
        this.bindEvents();
        this.loadInitialData();
    }

    bindEvents() {
        // Auto-refresh toggle (future enhancement)
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.stopRealTimeUpdates();
            } else {
                this.startRealTimeUpdates();
            }
        });
    }

    startRealTimeUpdates() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
        }
        
        this.intervalId = setInterval(() => {
            this.updateStats();
            this.updateActivity();
        }, this.updateInterval);
    }

    stopRealTimeUpdates() {
        if (this.intervalId) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    }

    async loadInitialData() {
        await this.updateStats();
        await this.updateActivity();
        await this.updateRecentMessages();
    }

    async updateStats() {
        try {
            const response = await fetch('/api/stats');
            if (!response.ok) throw new Error('Failed to fetch stats');
            
            const data = await response.json();
            
            // Update statistics cards
            this.updateElement('total-users', data.total_users);
            this.updateElement('active-conversations', data.active_conversations);
            this.updateElement('waiting-users', data.waiting_users);
            this.updateElement('active-count', data.active_conversations);
            this.updateElement('waiting-count', data.waiting_users);
            
            // Update active conversations list
            this.updateActiveConversations(data.active_conversations_data);
            
            // Update waiting users list
            this.updateWaitingUsers(data.waiting_users_data);
            
        } catch (error) {
            console.error('Error updating stats:', error);
            this.showError('Failed to update statistics');
        }
    }

    async updateActivity() {
        // Activity updates are handled in updateStats for efficiency
    }

    async updateRecentMessages() {
        try {
            const response = await fetch('/api/recent-activity');
            if (!response.ok) throw new Error('Failed to fetch recent activity');
            
            const data = await response.json();
            this.updateRecentMessagesList(data.recent_messages);
            
        } catch (error) {
            console.error('Error updating recent messages:', error);
            this.showError('Failed to update recent messages');
        }
    }

    updateElement(id, value) {
        const element = document.getElementById(id);
        if (element) {
            // Add animation effect
            element.style.transition = 'all 0.3s ease';
            element.textContent = value;
            
            // Brief highlight effect for changes
            if (element.textContent !== value.toString()) {
                element.style.backgroundColor = 'rgba(var(--bs-primary-rgb), 0.2)';
                setTimeout(() => {
                    element.style.backgroundColor = '';
                }, 500);
            }
        }
    }

    updateActiveConversations(conversations) {
        const container = document.getElementById('active-conversations-list');
        if (!container) return;

        if (conversations.length === 0) {
            container.innerHTML = `
                <div class="text-center py-4">
                    <i data-feather="message-circle" class="text-muted mb-2"></i>
                    <p class="text-muted mb-0">No active conversations</p>
                </div>
            `;
        } else {
            container.innerHTML = conversations.map(conv => `
                <div class="activity-item active mb-3">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <h6 class="mb-1">
                                <span class="live-indicator me-2"></span>
                                Conversation #${conv.id}
                            </h6>
                            <small class="text-muted">
                                <i data-feather="clock" width="12" height="12" class="me-1"></i>
                                ${conv.duration_minutes} minutes
                                <span class="ms-2">
                                    <i data-feather="message-square" width="12" height="12" class="me-1"></i>
                                    ${conv.message_count} messages
                                </span>
                            </small>
                        </div>
                        <small class="text-muted">
                            ${this.formatTime(conv.started_at)}
                        </small>
                    </div>
                </div>
            `).join('');
        }

        // Re-initialize Feather icons
        feather.replace();
    }

    updateWaitingUsers(waitingUsers) {
        const container = document.getElementById('waiting-users-list');
        if (!container) return;

        if (waitingUsers.length === 0) {
            container.innerHTML = `
                <div class="text-center py-4">
                    <i data-feather="users" class="text-muted mb-2"></i>
                    <p class="text-muted mb-0">No users waiting</p>
                </div>
            `;
        } else {
            container.innerHTML = waitingUsers.map(user => `
                <div class="activity-item waiting mb-3">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <h6 class="mb-1">
                                <i data-feather="clock" width="14" height="14" class="me-2"></i>
                                User #${user.id}
                            </h6>
                            <small class="text-muted">
                                Waiting for ${user.wait_time_minutes} minutes
                            </small>
                        </div>
                        <small class="text-muted">
                            ${this.formatTime(user.joined_at)}
                        </small>
                    </div>
                </div>
            `).join('');
        }

        // Re-initialize Feather icons
        feather.replace();
    }

    updateRecentMessagesList(messages) {
        const container = document.getElementById('recent-messages-list');
        if (!container) return;

        if (messages.length === 0) {
            container.innerHTML = `
                <div class="text-center py-4">
                    <i data-feather="message-square" class="text-muted mb-2"></i>
                    <p class="text-muted mb-0">No recent messages</p>
                </div>
            `;
        } else {
            container.innerHTML = messages.slice(0, 10).map(msg => `
                <div class="message-preview mb-3">
                    <div class="d-flex justify-content-between align-items-start mb-2">
                        <small class="text-muted">
                            <i data-feather="hash" width="12" height="12" class="me-1"></i>
                            Conversation ${msg.conversation_id}
                        </small>
                        <small class="text-muted">
                            ${this.formatTime(msg.sent_at)}
                        </small>
                    </div>
                    <p class="mb-0 small">${this.escapeHtml(msg.message_preview)}</p>
                </div>
            `).join('');
        }

        // Re-initialize Feather icons
        feather.replace();
    }

    formatTime(isoString) {
        const date = new Date(isoString);
        return date.toLocaleString('en-US', {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    showError(message) {
        // Simple error notification
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-warning alert-dismissible fade show position-fixed';
        alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 1050; min-width: 300px;';
        alertDiv.innerHTML = `
            <i data-feather="alert-triangle" class="me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alertDiv);
        feather.replace();
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }
}

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new DashboardManager();
});

// Handle page unload
window.addEventListener('beforeunload', () => {
    if (window.dashboardManager) {
        window.dashboardManager.stopRealTimeUpdates();
    }
});
