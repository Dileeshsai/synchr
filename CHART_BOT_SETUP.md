# Chart Bot Setup Guide

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r chart_bot/requirements.txt
```

### 2. Run Setup Script
```bash
python setup_chart_bot.py
```

### 3. Test Installation
```bash
python test_chart_bot_integration.py
```

## 📋 Manual Setup (Alternative)

### 1. Database Setup
```bash
python manage.py makemigrations chart_bot
python manage.py migrate
```

### 2. Configure Bot
```bash
python manage.py setup_chart_bot --enable
```

### 3. Test Bot
```bash
python manage.py test_chart_bot --query "What is my attendance for this month?"
```

## ✅ Verification

After setup, you should see:
- ✅ Chart Bot widget on every page (bottom-right corner)
- ✅ Admin interface at `/admin/chart_bot/`
- ✅ API endpoints at `/chart-bot/api/`
- ✅ Bot responds to HR queries

## 🔧 Configuration

### LLM Endpoint
- **URL**: `http://125.18.84.108:11434/api/generate`
- **Model**: `mistral`
- **Timeout**: 30 seconds

### Security Features
- ✅ Role-based access control
- ✅ Permission validation
- ✅ Data filtering
- ✅ Audit logging

## 🎯 Usage Examples

### Employee Queries
- "What is my attendance for this month?"
- "Show me my leave balance"
- "What is my salary for August?"

### HR Manager Queries
- "Show attendance of my team this month"
- "List pending leave requests in my team"
- "Who is absent today in my department?"

### Admin Queries
- "Show company-wide attendance summary"
- "Generate payroll report for August"
- "Show department-wise employee count"

## 🛠️ Troubleshooting

### Bot Not Appearing
1. Check if user is authenticated
2. Verify bot is enabled in admin
3. Check middleware configuration
4. Ensure static files are collected

### LLM Connection Issues
1. Verify LLM endpoint accessibility
2. Check network connectivity
3. Validate model name
4. Review timeout settings

### Permission Errors
1. Verify user role assignments
2. Check employee relationships
3. Review permission configurations

## 📞 Support

For issues:
1. Check logs for error details
2. Run test scripts
3. Review configuration
4. Contact development team

---

**Chart Bot is now ready to assist your HR team!** 🤖✨
