# Chart Bot - AI-Powered HR Assistant

Chart Bot is an intelligent HR assistant integrated with Horilla HRMS that uses LangGraph and your custom LLM to provide secure, role-based HR information access.

## 🚀 Features

- **AI-Powered Conversations**: Uses LangGraph with React agent pattern for intelligent query processing
- **Role-Based Security**: Strict permission system for Employee, HR Manager, and Admin roles
- **Memory & Context**: Maintains conversation history and context across sessions
- **Real-time Data**: Fetches live data from HRMS database
- **Custom LLM Integration**: Uses your deployed Mistral model
- **Responsive UI**: Modern chat widget that appears on every page
- **Human-in-the-Loop**: Supports confirmation for sensitive operations

## 🏗️ Architecture

### LangGraph Workflow
```
User Query → Query Analysis → Permission Check → Data Fetching → LLM Response → UI Display
```

### Components
- **Query Analyzer**: Understands user intent and extracts parameters
- **Security Manager**: Enforces role-based access control
- **Data Fetcher**: Retrieves data from HRMS database
- **LLM Client**: Communicates with your custom LLM endpoint
- **LangGraph Agent**: Orchestrates the entire workflow

## 📋 Installation

### 1. Install Dependencies
```bash
pip install -r chart_bot/requirements.txt
```

### 2. Run Migrations
```bash
python manage.py makemigrations chart_bot
python manage.py migrate
```

### 3. Setup Chart Bot
```bash
python manage.py setup_chart_bot --enable
```

### 4. Test Installation
```bash
python manage.py test_chart_bot --query "What is my attendance for this month?"
```

## ⚙️ Configuration

### LLM Endpoint
The bot is configured to use your LLM endpoint:
- **URL**: `http://125.18.84.108:11434/api/generate`
- **Model**: `mistral`

### Admin Configuration
Access the admin panel to configure:
- Bot name and settings
- LLM endpoint and model
- Response timeout and context length
- Enable/disable the bot

## 🔐 Security & Permissions

### Role-Based Access Control

#### Employee
- ✅ Own profile information
- ✅ Own attendance records
- ✅ Own leave balance and requests
- ✅ Own payroll information
- ❌ Other employees' data
- ❌ Team information
- ❌ Company-wide reports

#### HR Manager
- ✅ Own data (same as Employee)
- ✅ Subordinates' data
- ✅ Team attendance and leave reports
- ✅ Team payroll information
- ❌ Unrelated employees' data
- ❌ Company-wide financial data

#### Admin
- ✅ All employee data
- ✅ Company-wide reports
- ✅ Payroll summaries
- ✅ Attendance analytics
- ✅ Leave statistics
- ⚠️ Confirmation prompts for large data exports

### Security Features
- **Permission Validation**: Every query is validated against user permissions
- **Data Filtering**: Database queries are automatically filtered based on user role
- **Audit Logging**: All conversations are logged for security monitoring
- **Session Management**: Secure session handling with automatic cleanup

## 💬 Usage Examples

### Employee Queries
```
"What is my attendance for this month?"
"Show me my leave balance"
"What is my salary for August?"
"Am I on leave today?"
```

### HR Manager Queries
```
"Show attendance of my team this month"
"List pending leave requests in my team"
"Who is absent today in my department?"
"Generate team attendance report"
```

### Admin Queries
```
"Show company-wide attendance summary"
"List all employees with pending leave requests"
"Generate payroll report for August"
"Show department-wise employee count"
```

## 🛠️ API Endpoints

### Chat API
```http
POST /chart-bot/api/chat/
Content-Type: application/json

{
    "message": "What is my attendance for this month?",
    "session_id": "optional-session-id"
}
```

### Chat History
```http
GET /chart-bot/api/history/?session_id=session-id&limit=10
```

### Bot Status
```http
GET /chart-bot/api/status/
```

### Session Management
```http
GET /chart-bot/api/sessions/
POST /chart-bot/api/sessions/
DELETE /chart-bot/api/sessions/
```

## 🎨 Frontend Integration

The chat widget automatically appears on every page for authenticated users. It includes:

- **Minimizable Interface**: Click to minimize/maximize
- **Real-time Typing Indicators**: Shows when bot is processing
- **Message History**: Maintains conversation context
- **Responsive Design**: Works on desktop and mobile
- **Dark Mode Support**: Adapts to system preferences

### Manual Integration
If you want to manually include the widget:

```html
{% load chart_bot_tags %}
{% chart_bot_widget %}
```

## 🔧 Management Commands

### Setup Chart Bot
```bash
python manage.py setup_chart_bot \
    --llm-endpoint "http://125.18.84.108:11434/api/generate" \
    --llm-model "mistral" \
    --bot-name "Chart Bot" \
    --enable
```

### Test Chart Bot
```bash
python manage.py test_chart_bot \
    --user "admin" \
    --query "Show me company statistics"
```

## 📊 Monitoring & Analytics

### Admin Interface
Access `/admin/chart_bot/` to monitor:
- Chat sessions and messages
- Bot configuration
- User interactions
- Performance metrics

### Logging
Chart Bot logs all activities:
- Query analysis results
- Permission checks
- Data fetching operations
- LLM responses
- Error conditions

## 🚨 Troubleshooting

### Common Issues

#### Bot Not Appearing
1. Check if user is authenticated
2. Verify bot is enabled in admin
3. Check middleware is properly configured
4. Ensure static files are collected

#### LLM Connection Issues
1. Verify LLM endpoint is accessible
2. Check network connectivity
3. Validate LLM model name
4. Review response timeout settings

#### Permission Errors
1. Verify user has proper role assignments
2. Check employee-work information relationships
3. Review permission configurations
4. Validate security manager logic

### Debug Mode
Enable debug logging:
```python
LOGGING = {
    'loggers': {
        'chart_bot': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
    },
}
```

## 🔄 Updates & Maintenance

### Regular Maintenance
- Monitor chat session cleanup
- Review permission configurations
- Update LLM endpoint if needed
- Backup conversation data

### Performance Optimization
- Adjust context length based on usage
- Optimize database queries
- Monitor LLM response times
- Cache frequently accessed data

## 📝 Development

### Adding New Query Types
1. Update `QueryAnalyzer` with new intent patterns
2. Add data fetching logic in `DataFetcher`
3. Update permission validation in `SecurityManager`
4. Test with various user roles

### Customizing LLM Prompts
Modify the system instructions in `LLMClient._prepare_prompt()` to customize bot behavior.

### Extending Security
Add new permission types in `SecurityManager.validate_query_permissions()`.

## 📄 License

This Chart Bot implementation is part of the Horilla HRMS project and follows the same licensing terms.

## 🤝 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the logs for error details
3. Test with the management commands
4. Contact the development team

---

**Chart Bot** - Making HR data accessible through intelligent conversations! 🤖✨
