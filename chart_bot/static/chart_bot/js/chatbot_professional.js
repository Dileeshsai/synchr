/**
 * Professional Chart Bot Implementation
 * Robust, production-ready chat widget
 */
class ProfessionalChartBot {
    constructor(options = {}) {
        this.config = {
            apiEndpoint: options.apiEndpoint || '/chart-bot/api/v2/chat/',
            statusEndpoint: options.statusEndpoint || '/chart-bot/api/v2/status/',
            testAuthEndpoint: options.testAuthEndpoint || '/chart-bot/api/v2/test-auth/',
            sessionId: options.sessionId || null,
            autoStart: options.autoStart !== false,
            position: options.position || 'bottom-right',
            theme: options.theme || 'light',
            maxRetries: 3,
            retryDelay: 1000,
            timeout: 30000,
            debug: options.debug || false,
            ...options
        };
        
        this.state = {
            isMinimized: false,
            isLoading: false,
            isConnected: false,
            isAuthenticated: false,
            retryCount: 0,
            lastError: null
        };
        
        this.sessionId = this.config.sessionId;
        this.messageHistory = [];
        this.maxHistoryLength = 100;
        this.connectionCheckInterval = null;
        
        this.init();
    }
    
    init() {
        this.log('Initializing Professional Chart Bot...');
        this.createWidget();
        this.bindEvents();
        this.startConnectionCheck();
        
        if (this.config.autoStart) {
            this.show();
        }
    }
    
    log(message, data = null) {
        if (this.config.debug) {
            console.log(`[ChartBot] ${message}`, data || '');
        }
    }
    
    error(message, error = null) {
        console.error(`[ChartBot] ${message}`, error || '');
    }
    
    createWidget() {
        // Create widget container
        this.widget = document.createElement('div');
        this.widget.className = 'chart-bot-widget professional';
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
        
        this.log('Widget created successfully');
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
            if (!this.state.isMinimized) {
                this.input.focus();
            }
        });
        
        this.log('Events bound successfully');
    }
    
    async startConnectionCheck() {
        this.log('Starting connection check...');
        await this.checkConnection();
        
        // Check connection every 30 seconds
        this.connectionCheckInterval = setInterval(() => {
            this.checkConnection();
        }, 30000);
    }
    
    async checkConnection() {
        try {
            const response = await this.callAPI('GET', this.config.testAuthEndpoint);
            
            if (response.authenticated) {
                this.state.isAuthenticated = true;
                this.state.isConnected = true;
                this.state.retryCount = 0;
                this.updateStatus('online');
                this.log('Connection check successful', response);
                
                // Load bot status if not already loaded
                if (!this.state.botStatusLoaded) {
                    await this.loadBotStatus();
                }
            } else {
                this.state.isAuthenticated = false;
                this.state.isConnected = false;
                this.updateStatus('offline');
                this.log('Authentication failed', response);
            }
        } catch (error) {
            this.state.isConnected = false;
            this.state.retryCount++;
            this.updateStatus('offline');
            this.error('Connection check failed', error);
            
            if (this.state.retryCount >= this.config.maxRetries) {
                this.addMessage('system', 'Connection lost. Please refresh the page to reconnect.');
            }
        }
    }
    
    async loadBotStatus() {
        try {
            const response = await this.callAPI('GET', this.config.statusEndpoint);
            
            if (response.authenticated && response.bot_enabled) {
                this.updateBotName(response.bot_name);
                this.state.botStatusLoaded = true;
                this.log('Bot status loaded successfully', response);
            } else {
                this.addMessage('system', 'Chart Bot is currently offline. Please try again later.');
                this.log('Bot is disabled or authentication failed', response);
            }
        } catch (error) {
            this.error('Failed to load bot status', error);
        }
    }
    
    async sendMessage() {
        const message = this.input.value.trim();
        if (!message || this.state.isLoading) return;
        
        this.log('Sending message', message);
        
        // Add user message to UI
        this.addMessage('user', message);
        
        // Clear input
        this.input.value = '';
        this.autoResizeTextarea();
        
        // Show typing indicator
        this.showTyping();
        
        // Set loading state
        this.setState({ isLoading: true });
        
        try {
            // Send to API with retry logic
            const response = await this.callAPIWithRetry('POST', this.config.apiEndpoint, {
                message: message,
                session_id: this.sessionId
            });
            
            this.log('API response received', response);
            
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
                
                this.state.retryCount = 0;
            } else {
                this.addMessage('bot', response.response || 'Sorry, I encountered an error. Please try again.');
            }
        } catch (error) {
            this.error('Failed to send message', error);
            this.hideTyping();
            
            // Provide specific error messages
            if (error.message.includes('Authentication required')) {
                this.addMessage('bot', 'Please log in to use Chart Bot. You need to be authenticated to access HR information.');
            } else if (error.message.includes('timeout')) {
                this.addMessage('bot', 'Request timed out. Please try again.');
            } else if (error.message.includes('network')) {
                this.addMessage('bot', 'Network error. Please check your connection and try again.');
            } else {
                this.addMessage('bot', 'Sorry, I\'m having trouble connecting right now. Please try again later.');
            }
        } finally {
            this.setState({ isLoading: false });
        }
    }
    
    async callAPIWithRetry(method, url, data = null, retries = this.config.maxRetries) {
        for (let i = 0; i < retries; i++) {
            try {
                return await this.callAPI(method, url, data);
            } catch (error) {
                if (i === retries - 1) throw error;
                
                this.log(`API call failed, retrying... (${i + 1}/${retries})`, error);
                await this.delay(this.config.retryDelay * (i + 1));
            }
        }
    }
    
    async callAPI(method, url, data = null) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.config.timeout);
        
        try {
            const options = {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken(),
                    'X-Requested-With': 'XMLHttpRequest'
                },
                credentials: 'same-origin',
                signal: controller.signal
            };
            
            if (data) {
                options.body = JSON.stringify(data);
            }
            
            this.log(`Making API call: ${method} ${url}`, data);
            
            const response = await fetch(url, options);
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                const errorText = await response.text();
                let errorMessage = `HTTP error! status: ${response.status}`;
                
                if (response.status === 401) {
                    errorMessage = 'Authentication required. Please log in.';
                } else if (response.status === 403) {
                    errorMessage = 'Access denied. You don\'t have permission.';
                } else if (response.status === 500) {
                    errorMessage = 'Server error. Please try again later.';
                }
                
                throw new Error(errorMessage);
            }
            
            const result = await response.json();
            this.log('API call successful', result);
            return result;
            
        } catch (error) {
            clearTimeout(timeoutId);
            
            if (error.name === 'AbortError') {
                throw new Error('Request timeout');
            }
            
            throw error;
        }
    }
    
    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]');
        return token ? token.value : '';
    }
    
    delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    setState(newState) {
        this.state = { ...this.state, ...newState };
        this.updateUI();
    }
    
    updateUI() {
        // Update send button state
        this.sendBtn.disabled = this.state.isLoading;
        this.input.disabled = this.state.isLoading;
        
        if (this.state.isLoading) {
            this.sendBtn.innerHTML = '⏳';
        } else {
            this.sendBtn.innerHTML = '➤';
        }
    }
    
    updateStatus(status) {
        this.statusIndicator.className = `chart-bot-status ${status}`;
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
    
    autoResizeTextarea() {
        this.input.style.height = 'auto';
        this.input.style.height = Math.min(this.input.scrollHeight, 100) + 'px';
    }
    
    scrollToBottom() {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }
    
    toggleMinimize() {
        this.state.isMinimized = !this.state.isMinimized;
        
        if (this.state.isMinimized) {
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
        if (!this.state.isMinimized) {
            this.input.focus();
        }
    }
    
    hide() {
        this.widget.style.display = 'none';
    }
    
    updateBotName(name) {
        const titleElement = this.widget.querySelector('.chart-bot-title span');
        if (titleElement && name) {
            titleElement.textContent = name;
        }
    }
    
    destroy() {
        if (this.connectionCheckInterval) {
            clearInterval(this.connectionCheckInterval);
        }
        
        if (this.widget && this.widget.parentNode) {
            this.widget.parentNode.removeChild(this.widget);
        }
    }
}

// Auto-initialize if script is loaded
document.addEventListener('DOMContentLoaded', function() {
    if (window.chartBotConfig) {
        window.chartBot = new ProfessionalChartBot(window.chartBotConfig);
    }
});

// Export for manual initialization
window.ProfessionalChartBot = ProfessionalChartBot;
