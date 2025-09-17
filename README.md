# 🏢 Sync HRMS - Complete Human Resource Management System

[![Django](https://img.shields.io/badge/Django-4.2.21-green.svg)](https://djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org/)
[![License](https://img.shields.io/badge/License-Open%20Source-orange.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-brightgreen.svg)]()

**Sync HRMS** is a comprehensive, open-source Human Resource Management System (HRMS) built with Django. It provides a complete solution for managing all aspects of human resources, from recruitment to offboarding, with modern AI-powered features and advanced analytics.

## 🌟 Key Features

### 📋 Core HR Modules
- **👥 Employee Management** - Complete employee lifecycle management
- **📅 Attendance Tracking** - Multiple attendance methods including face recognition
- **🏖️ Leave Management** - Comprehensive leave request and approval system
- **💰 Payroll System** - Automated salary calculation and payslip generation
- **📊 Performance Management** - OKR-based performance tracking
- **🎯 Project Management** - Task and project tracking with team collaboration
- **📦 Asset Management** - Company asset tracking and management
- **🎫 Helpdesk System** - Internal support ticket management

### 🤖 AI-Powered Features
- **Chart Bot** - AI assistant for HR data analysis and insights
- **Face Recognition** - Biometric attendance using facial recognition
- **Smart Analytics** - Advanced reporting and data visualization
- **Automated Workflows** - Intelligent process automation

### 🔧 Advanced Capabilities
- **Multi-Company Support** - Manage multiple companies from single instance
- **Role-Based Access Control** - Granular permissions and security
- **Multi-Language Support** - Internationalization ready
- **REST API** - Complete API for integrations
- **Real-time Notifications** - Instant updates and alerts
- **Audit Logging** - Complete activity tracking
- **Backup & Recovery** - Automated data protection

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- PostgreSQL (recommended) or SQLite
- Node.js (for frontend assets)
- CMake (for face recognition)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/sync-hrms.git
   cd sync-hrms
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Setup database**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

5. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

6. **Load sample data (optional)**
   ```bash
   python manage.py loaddata load_data/*.json
   ```

7. **Run development server**
   ```bash
   python manage.py runserver
   ```

8. **Access the application**
   - Open your browser and go to `http://127.0.0.1:8000`
   - Login with your superuser credentials

## 📱 Modules Overview

### 👤 Employee Management
- Employee profiles and personal information
- Work information and organizational structure
- Document management and file storage
- Employee self-service portal
- Bulk operations and data import/export

### ⏰ Attendance Management
- Multiple clock-in/out methods
- Face recognition attendance
- Biometric device integration
- Shift management and scheduling
- Overtime calculation and tracking
- Attendance reports and analytics

### 🏖️ Leave Management
- Leave type configuration
- Leave request and approval workflow
- Leave balance tracking
- Holiday calendar management
- Leave reports and analytics
- Integration with attendance system

### 💰 Payroll System
- Automated salary calculation
- Multiple pay components (basic, allowances, deductions)
- Tax calculation and compliance
- Payslip generation and distribution
- Payroll reports and analytics
- Integration with attendance and leave

### 🎯 Performance Management
- OKR (Objectives and Key Results) framework
- Performance review cycles
- 360-degree feedback
- Goal setting and tracking
- Performance analytics and reporting

### 🎫 Recruitment
- Job posting and application management
- Candidate screening and evaluation
- Interview scheduling and feedback
- Offer management and onboarding
- Recruitment analytics and reporting

### 📦 Asset Management
- Asset registration and tracking
- Asset allocation and return
- Maintenance scheduling
- Asset depreciation calculation
- Asset reports and analytics

### 🎫 Helpdesk
- Ticket creation and management
- Priority and category assignment
- Assignment and escalation
- Knowledge base integration
- SLA tracking and reporting

## 🤖 AI Features

### Chart Bot - AI HR Assistant
The Chart Bot is an intelligent AI assistant that helps users analyze HR data and get insights through natural language queries.

**Features:**
- Natural language query processing
- Role-based data access
- Real-time data analysis
- Interactive charts and visualizations
- Conversation history and context

**Setup:**
```bash
python manage.py setup_chart_bot --enable
```

### Face Recognition System
Advanced biometric attendance system using facial recognition technology.

**Features:**
- Employee face registration
- Real-time face recognition
- Attendance automation
- Security and privacy protection

**Setup:**
```bash
# Install face recognition dependencies
pip install face_recognition opencv-python dlib

# Run migrations
python manage.py makemigrations facedetection
python manage.py migrate
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the project root:

```env
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/horilla_db

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Face Recognition
FACE_RECOGNITION_ENABLED=True
FACE_RECOGNITION_TOLERANCE=0.6

# Chart Bot
CHART_BOT_ENABLED=True
LLM_ENDPOINT=http://your-llm-endpoint:11434/api/generate
```

### Database Configuration
The system supports multiple databases:
- **PostgreSQL** (recommended for production)
- **MySQL**
- **SQLite** (for development)

### Email Configuration
Configure email settings for notifications and communications:
- SMTP server configuration
- Email templates
- Notification preferences

## 📊 API Documentation

The system provides a comprehensive REST API for all modules:

### Base URL
```
http://your-domain.com/api/v1/
```

### Authentication
```bash
# Get authentication token
curl -X POST http://your-domain.com/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your-username", "password": "your-password"}'
```

### Available Endpoints
- **Employee API**: `/api/v1/employee/`
- **Attendance API**: `/api/v1/attendance/`
- **Leave API**: `/api/v1/leave/`
- **Payroll API**: `/api/v1/payroll/`
- **Face Detection API**: `/api/facedetection/`
- **Chart Bot API**: `/chart-bot/api/`

## 🎨 Customization

### Themes and Styling
- Custom CSS and SCSS support
- Responsive design
- Dark mode support
- Brand customization

### Workflows
- Custom approval workflows
- Automated notifications
- Business rule configuration
- Integration with external systems

### Reports
- Custom report builder
- Scheduled report generation
- Export to multiple formats (PDF, Excel, CSV)
- Dashboard customization

## 🔒 Security Features

- **Role-Based Access Control** - Granular permissions
- **Data Encryption** - Sensitive data protection
- **Audit Logging** - Complete activity tracking
- **Session Management** - Secure user sessions
- **CSRF Protection** - Cross-site request forgery protection
- **SQL Injection Prevention** - Parameterized queries
- **XSS Protection** - Cross-site scripting prevention

## 📈 Performance Optimization

- **Database Optimization** - Query optimization and indexing
- **Caching** - Redis and memory caching
- **CDN Support** - Content delivery network integration
- **Image Optimization** - Automatic image compression
- **Lazy Loading** - Efficient data loading

## 🧪 Testing

### Run Tests
```bash
# Run all tests
python manage.py test

# Run specific module tests
python manage.py test employee
python manage.py test attendance
python manage.py test chart_bot
```

### Test Coverage
```bash
# Install coverage
pip install coverage

# Run tests with coverage
coverage run --source='.' manage.py test
coverage report
coverage html
```

## 🚀 Deployment

### Production Deployment
1. **Configure production settings**
2. **Setup web server (Nginx/Apache)**
3. **Configure database**
4. **Setup SSL certificates**
5. **Configure email services**
6. **Setup monitoring and logging**

### Docker Deployment
```bash
# Build Docker image
docker build -t horilla-hrms .

# Run with Docker Compose
docker-compose up -d
```

### Cloud Deployment
- **AWS** - EC2, RDS, S3
- **Google Cloud** - Compute Engine, Cloud SQL
- **Azure** - Virtual Machines, SQL Database
- **DigitalOcean** - Droplets, Managed Databases

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Development Setup
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Code Style
- Follow PEP 8 for Python code
- Use meaningful variable names
- Add docstrings to functions and classes
- Write comprehensive tests

## 📚 Documentation

- **User Guide**: [User Documentation](docs/user-guide.md)
- **Developer Guide**: [Developer Documentation](docs/developer-guide.md)
- **API Reference**: [API Documentation](docs/api-reference.md)
- **Deployment Guide**: [Deployment Documentation](docs/deployment.md)

## 🐛 Bug Reports

Found a bug? Please report it on our [Issue Tracker](https://github.com/your-org/sync-hrms/issues).

## 💡 Feature Requests

Have an idea for a new feature? Submit it on our [Feature Request Board](https://github.com/your-org/sync-hrms/discussions).

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Django community for the excellent framework
- All contributors who have helped improve this project
- Open source libraries and tools used in this project

## 📞 Support

- **Documentation**: [docs.sync-hrms.com](https://docs.sync-hrms.com)
- **Community Forum**: [community.sync-hrms.com](https://community.sync-hrms.com)
- **Email Support**: support@sync-hrms.com
- **GitHub Issues**: [github.com/your-org/sync-hrms/issues](https://github.com/your-org/sync-hrms/issues)

## 🔄 Changelog

See [CHANGELOG.md](CHANGELOG.md) for a list of changes and version history.

---

**Made with ❤️ by the Sync HRMS Team**

*Empowering organizations with intelligent HR management solutions*
