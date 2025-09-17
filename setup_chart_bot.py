#!/usr/bin/env python
"""
Chart Bot Setup Script
Automates the installation and configuration of Chart Bot
"""
import os
import sys
import subprocess
import django
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'horilla.settings')
django.setup()

from django.core.management import execute_from_command_line
from chart_bot.models import BotConfiguration


def run_command(command, description):
    """Run a Django management command"""
    print(f"🔄 {description}...")
    try:
        execute_from_command_line(command.split())
        print(f"✅ {description} completed successfully!")
        return True
    except Exception as e:
        print(f"❌ {description} failed: {str(e)}")
        return False


def check_requirements():
    """Check if required packages are installed"""
    print("🔍 Checking requirements...")
    
    required_packages = [
        'langgraph',
        'langchain',
        'requests',
        'pydantic'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("📦 Installing missing packages...")
        
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', 
                '-r', 'chart_bot/requirements.txt'
            ])
            print("✅ Requirements installed successfully!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install requirements: {str(e)}")
            return False
    else:
        print("✅ All requirements are satisfied!")
    
    return True


def setup_database():
    """Setup database tables"""
    print("🗄️ Setting up database...")
    
    # Create migrations
    if not run_command("makemigrations chart_bot", "Creating migrations"):
        return False
    
    # Apply migrations
    if not run_command("migrate", "Applying migrations"):
        return False
    
    return True


def configure_bot():
    """Configure Chart Bot"""
    print("⚙️ Configuring Chart Bot...")
    
    # Check if configuration already exists
    if BotConfiguration.objects.exists():
        print("ℹ️ Chart Bot configuration already exists. Updating...")
        config = BotConfiguration.objects.first()
        config.is_enabled = True
        config.save()
    else:
        # Create default configuration
        config = BotConfiguration.objects.create(
            name="Chart Bot",
            is_enabled=True,
            llm_endpoint="http://125.18.84.108:11434/api/generate",
            llm_model="mistral",
            max_context_length=10,
            response_timeout=30
        )
        print("✅ Chart Bot configuration created!")
    
    print(f"📋 Configuration:")
    print(f"   - Name: {config.name}")
    print(f"   - LLM Endpoint: {config.llm_endpoint}")
    print(f"   - LLM Model: {config.llm_model}")
    print(f"   - Enabled: {config.is_enabled}")
    
    return True


def test_installation():
    """Test Chart Bot installation"""
    print("🧪 Testing Chart Bot installation...")
    
    # Test with a simple query
    test_query = "Hello, are you working?"
    
    try:
        from django.contrib.auth.models import User
        from chart_bot.core.langgraph_agent import ChartBotAgent
        
        # Get first user for testing
        user = User.objects.first()
        if not user:
            print("⚠️ No users found. Please create a user first.")
            return True
        
        print(f"👤 Testing with user: {user.username}")
        
        # Initialize agent
        agent = ChartBotAgent(user)
        
        # Test query processing
        result = agent.process_query(test_query)
        
        if result['success']:
            print("✅ Chart Bot is working correctly!")
            print(f"📝 Test response: {result['response'][:100]}...")
        else:
            print(f"⚠️ Chart Bot test completed with issues: {result.get('error', 'Unknown error')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False


def main():
    """Main setup function"""
    print("🚀 Chart Bot Setup Script")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        print("❌ Setup failed at requirements check")
        return False
    
    # Setup database
    if not setup_database():
        print("❌ Setup failed at database setup")
        return False
    
    # Configure bot
    if not configure_bot():
        print("❌ Setup failed at bot configuration")
        return False
    
    # Test installation
    if not test_installation():
        print("❌ Setup failed at testing")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 Chart Bot setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Access the admin panel to customize settings")
    print("2. Test the chat widget on any page")
    print("3. Review the README for usage examples")
    print("\n🔗 Useful links:")
    print("- Admin: /admin/chart_bot/")
    print("- API: /chart-bot/api/status/")
    print("- Documentation: chart_bot/README.md")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
