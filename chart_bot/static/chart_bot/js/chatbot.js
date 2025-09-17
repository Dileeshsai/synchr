/**
 * Chart Bot Chat Widget JavaScript
 */
class ChartBot {
    constructor(options = {}) {
        this.options = {
            apiEndpoint: options.apiEndpoint || '/chart-bot/api/chat/',
            historyEndpoint: options.historyEndpoint || '/chart-bot/api/history/',
            statusEndpoint: options.statusEndpoint || '/chart-bot/api/status/',
            sessionsEndpoint: options.sessionsEndpoint || '/chart-bot/api/sessions/',
            sessionId: options.sessionId || null,
            autoStart: options.autoStart !== false,
            position: options.position || 'bottom-right',
            theme: options.theme || 'light',
            ...options
        };
        
        this.isMinimized = false;
        this.isLoading = false;
        this.sessionId = this.options.sessionId;
        this.messageHistory = [];
        this.maxHistoryLength = 50;
        
        this.init();
    }
    
    init() {
        this.createWidget();
        this.bindEvents();
        this.loadBotStatus();
        
        if (this.options.autoStart) {
            this.show();
        }
    }
    
    createWidget() {
        // Create widget container
        this.widget = document.createElement('div');
        this.widget.className = 'chart-bot-widget';
        this.widget.innerHTML = `
            <div class="chart-bot-header" id="chart-bot-header">
                <div class="chart-bot-title">
                    <div class="chart-bot-avatar">🤖</div>
                    <span>Chart Bot</span>
                    <div class="chart-bot-status" id="chart-bot-status"></div>
                </div>
                <div class="chart-bot-controls">
                    <button class="chart-bot-btn" id="chart-bot-minimize" title="Minimize">−</button>
                    <button class="chart-bot-btn" id="chart-bot-close" title="Close">×</button>
                </div>
            </div>
            <div class="chart-bot-body" id="chart-bot-body">
                <div class="chart-bot-messages" id="chart-bot-messages">
                    <div class="chart-bot-welcome">
                        <h4>👋 Hi! I'm Chart Bot</h4>
                        <p>Your AI-powered HR Assistant. I can help you with:</p>
                        <ul style="text-align: left; margin: 10px 0;">
                            <li>📊 Attendance & Leave queries</li>
                            <li>💰 Payroll information</li>
                            <li>👤 Profile details</li>
                            <li>📈 Team reports (if you're a manager)</li>
                        </ul>
                        <p>Just ask me anything!</p>
                    </div>
                </div>
                <div class="chart-bot-input-container">
                    <div class="chart-bot-input-wrapper">
                        <textarea 
                            class="chart-bot-input" 
                            id="chart-bot-input" 
                            placeholder="Ask me anything about HR..."
                            rows="1"
                        ></textarea>
                        <button class="chart-bot-send-btn" id="chart-bot-send" title="Send">
                            ➤
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(this.widget);
        
        // Get references to elements
        this.header = this.widget.querySelector('#chart-bot-header');
        this.body = this.widget.querySelector('#chart-bot-body');
        this.messagesContainer = this.widget.querySelector('#chart-bot-messages');
        this.input = this.widget.querySelector('#chart-bot-input');
        this.sendBtn = this.widget.querySelector('#chart-bot-send');
        this.statusIndicator = this.widget.querySelector('#chart-bot-status');
    }
    
    bindEvents() {
        // Header click to toggle minimize
        this.header.addEventListener('click', (e) => {
            if (e.target.closest('.chart-bot-controls')) return;
            this.toggleMinimize();
        });
        
        // Minimize button
        this.widget.querySelector('#chart-bot-minimize').addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleMinimize();
        });
        
        // Close button
        this.widget.querySelector('#chart-bot-close').addEventListener('click', (e) => {
            e.stopPropagation();
            this.hide();
        });
        
        // Send button
        this.sendBtn.addEventListener('click', () => {
            this.sendMessage();
        });
        
        // Input events
        this.input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        // Auto-resize textarea
        this.input.addEventListener('input', () => {
            this.autoResizeTextarea();
        });
        
        // Focus input when widget is shown
        this.widget.addEventListener('click', () => {
            if (!this.isMinimized) {
                this.input.focus();
            }
        });
    }
    
    toggleMinimize() {
        this.isMinimized = !this.isMinimized;
        
        if (this.isMinimized) {
            this.widget.classList.add('minimized');
            this.header.classList.add('minimized');
            this.body.style.display = 'none';
        } else {
            this.widget.classList.remove('minimized');
            this.header.classList.remove('minimized');
            this.body.style.display = 'flex';
            this.input.focus();
        }
    }
    
    show() {
        this.widget.style.display = 'flex';
        if (!this.isMinimized) {
            this.input.focus();
        }
    }
    
    hide() {
        this.widget.style.display = 'none';
    }
    
    async sendMessage() {
        const message = this.input.value.trim();
        if (!message || this.isLoading) return;
        
        // Add user message to UI
        this.addMessage('user', message);
        
        // Clear input
        this.input.value = '';
        this.autoResizeTextarea();
        
        // Show typing indicator
        this.showTyping();
        
        // Disable input
        this.setLoading(true);
        
        try {
            // Send to API
            console.log('Sending message to API:', message);
            const response = await this.callAPI('POST', this.options.apiEndpoint, {
                message: message,
                session_id: this.sessionId
            });
            console.log('API response:', response);
            
            // Hide typing indicator
            this.hideTyping();
            
            if (response.success) {
                // Update session ID
                if (response.session_id) {
                    this.sessionId = response.session_id;
                }
                
                // Add bot response
                this.addMessage('bot', response.response);
                
                // Store in history
                this.messageHistory.push({
                    type: 'user',
                    content: message,
                    timestamp: new Date()
                });
                this.messageHistory.push({
                    type: 'bot',
                    content: response.response,
                    timestamp: new Date()
                });
                
                // Trim history if too long
                if (this.messageHistory.length > this.maxHistoryLength) {
                    this.messageHistory = this.messageHistory.slice(-this.maxHistoryLength);
                }
            } else {
                this.addMessage('bot', response.response || 'Sorry, I encountered an error. Please try again.');
            }
        } catch (error) {
            console.error('Chart Bot API Error:', error);
            this.hideTyping();
            
            // Provide more specific error messages
            if (error.message.includes('Authentication required')) {
                this.addMessage('bot', 'Please log in to use Chart Bot. You need to be authenticated to access HR information.');
            } else if (error.message.includes('Access denied')) {
                this.addMessage('bot', 'You don\'t have permission to access this information. Please contact your administrator.');
            } else if (error.message.includes('timeout') || error.message.includes('network')) {
                this.addMessage('bot', 'Network connection issue. Please check your internet connection and try again.');
            } else {
                this.addMessage('bot', 'Sorry, I\'m having trouble connecting right now. Please try again later.');
            }
        } finally {
            this.setLoading(false);
        }
    }
    
    addMessage(type, content, timestamp = null) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chart-bot-message ${type}`;
        
        const time = timestamp || new Date();
        const timeStr = time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        
        messageDiv.innerHTML = `
            <div>${this.formatMessage(content)}</div>
            <div class="chart-bot-message-time">${timeStr}</div>
        `;
        
        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();
    }
    
    formatMessage(content) {
        // Convert line breaks to <br>
        content = content.replace(/\n/g, '<br>');
        
        // Convert bullet points
        content = content.replace(/^[\s]*[-•]\s+/gm, '• ');
        
        // Convert numbered lists
        content = content.replace(/^[\s]*(\d+)\.\s+/gm, '$1. ');
        
        return content;
    }
    
    showTyping() {
        const typingDiv = document.createElement('div');
        typingDiv.className = 'chart-bot-typing';
        typingDiv.id = 'chart-bot-typing';
        typingDiv.innerHTML = `
            <div class="chart-bot-typing-dot"></div>
            <div class="chart-bot-typing-dot"></div>
            <div class="chart-bot-typing-dot"></div>
        `;
        
        this.messagesContainer.appendChild(typingDiv);
        this.scrollToBottom();
    }
    
    hideTyping() {
        const typingDiv = this.messagesContainer.querySelector('#chart-bot-typing');
        if (typingDiv) {
            typingDiv.remove();
        }
    }
    
    setLoading(loading) {
        this.isLoading = loading;
        this.sendBtn.disabled = loading;
        this.input.disabled = loading;
        
        if (loading) {
            this.sendBtn.innerHTML = '⏳';
        } else {
            this.sendBtn.innerHTML = '➤';
        }
    }
    
    autoResizeTextarea() {
        this.input.style.height = 'auto';
        this.input.style.height = Math.min(this.input.scrollHeight, 100) + 'px';
    }
    
    scrollToBottom() {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }
    
    async loadBotStatus() {
        try {
            // First test authentication
            console.log('Testing authentication...');
            const authResponse = await this.callAPI('GET', this.options.statusEndpoint.replace('/status/', '/test-auth/'));
            console.log('Authentication test result:', authResponse);
            
            if (!authResponse.authenticated) {
                this.statusIndicator.className = 'chart-bot-status offline';
                this.addMessage('system', 'Please log in to use Chart Bot.');
                console.log('Authentication failed:', authResponse);
                return;
            }
            
            console.log('Authentication successful, loading bot status...');
            
            // Then get bot status
            const response = await this.callAPI('GET', this.options.statusEndpoint);
            console.log('Bot status response:', response);
            
            if (response.bot_enabled) {
                this.statusIndicator.className = 'chart-bot-status';
                this.updateBotName(response.bot_name);
                console.log('Bot status loaded successfully:', response);
            } else {
                this.statusIndicator.className = 'chart-bot-status offline';
                this.addMessage('system', 'Chart Bot is currently offline. Please try again later.');
            }
        } catch (error) {
            console.error('Failed to load bot status:', error);
            this.statusIndicator.className = 'chart-bot-status offline';
            
            if (error.message.includes('Authentication required')) {
                this.addMessage('system', 'Please log in to use Chart Bot.');
            } else {
                this.addMessage('system', 'Unable to connect to Chart Bot. Please try again later.');
            }
        }
    }
    
    updateBotName(name) {
        const titleElement = this.widget.querySelector('.chart-bot-title span');
        if (titleElement && name) {
            titleElement.textContent = name;
        }
    }
    
    async callAPI(method, url, data = null) {
        const options = {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCSRFToken(),
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin'  // Include cookies for authentication
        };
        
        if (data) {
            options.body = JSON.stringify(data);
        }
        
        const response = await fetch(url, options);
        
        if (!response.ok) {
            if (response.status === 401) {
                throw new Error('Authentication required. Please log in.');
            } else if (response.status === 403) {
                throw new Error('Access denied. You don\'t have permission to access this resource.');
            } else {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
        }
        
        return await response.json();
    }
    
    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }
    
    // Public methods
    open() {
        this.show();
        this.toggleMinimize();
    }
    
    close() {
        this.hide();
    }
    
    clearHistory() {
        this.messageHistory = [];
        this.messagesContainer.innerHTML = `
            <div class="chart-bot-welcome">
                <h4>👋 Hi! I'm Chart Bot</h4>
                <p>Your AI-powered HR Assistant. How can I help you today?</p>
            </div>
        `;
    }
    
    destroy() {
        if (this.widget && this.widget.parentNode) {
            this.widget.parentNode.removeChild(this.widget);
        }
    }
}

// Auto-initialize if script is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Check if Chart Bot should be auto-initialized
    if (window.chartBotConfig) {
        window.chartBot = new ChartBot(window.chartBotConfig);
    }
});

// Export for manual initialization
window.ChartBot = ChartBot;
