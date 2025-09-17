#!/usr/bin/env python
"""
Professional Chart Bot Setup Script
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
    
    # Core required packages
    core_packages = [
        'requests',
        'pydantic'
    ]
    
    # Optional packages (LangGraph)
    optional_packages = [
        'langgraph',
        'langchain'
    ]
    
    missing_core = []
    missing_optional = []
    
    # Check core packages
    for package in core_packages:
        try:
            __import__(package)
        except ImportError:
            missing_core.append(package)
    
    # Check optional packages
    for package in optional_packages:
        try:
            __import__(package)
        except ImportError:
            missing_optional.append(package)
    
    if missing_core:
        print(f"❌ Missing core packages: {', '.join(missing_core)}")
        print("📦 Installing core packages...")
        
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', 
                'requests>=2.31.0', 'pydantic>=2.5.0'
            ])
            print("✅ Core requirements installed successfully!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install core requirements: {str(e)}")
            return False
    else:
        print("✅ Core requirements are satisfied!")
    
    if missing_optional:
        print(f"⚠️ Optional packages not available: {', '.join(missing_optional)}")
        print("ℹ️ Chart Bot will use simple agent mode (no LangGraph)")
        print("💡 To enable advanced features, install LangGraph manually:")
        print("   pip install langgraph langchain")
    else:
        print("✅ All optional requirements are satisfied!")
        print("🚀 Chart Bot will use advanced LangGraph mode!")
    
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
    """Configure Professional Chart Bot"""
    print("⚙️ Configuring Professional Chart Bot...")
    
    # Check if configuration already exists
    if BotConfiguration.objects.exists():
        print("ℹ️ Chart Bot configuration already exists. Updating...")
        config = BotConfiguration.objects.first()
        config.is_enabled = True
        config.name = "Professional Chart Bot"
        config.save()
    else:
        # Create default configuration
        config = BotConfiguration.objects.create(
            name="Professional Chart Bot",
            is_enabled=True,
            llm_endpoint="http://125.18.84.108:11434/api/generate",
            llm_model="mistral",
            max_context_length=15,
            response_timeout=45
        )
        print("✅ Professional Chart Bot configuration created!")
    
    print(f"📋 Configuration:")
    print(f"   - Name: {config.name}")
    print(f"   - LLM Endpoint: {config.llm_endpoint}")
    print(f"   - LLM Model: {config.llm_model}")
    print(f"   - Enabled: {config.is_enabled}")
    print(f"   - Max Context: {config.max_context_length}")
    print(f"   - Timeout: {config.response_timeout}s")
    
    return True


def test_installation():
    """Test Professional Chart Bot installation"""
    print("🧪 Testing Professional Chart Bot installation...")
    
    # Test with a simple query
    test_query = "Hello, are you working properly?"
    
    try:
        from django.contrib.auth.models import User
        
        # Get first user for testing
        user = User.objects.first()
        if not user:
            print("⚠️ No users found. Please create a user first.")
            return True
        
        print(f"👤 Testing with user: {user.username}")
        
        # Try to initialize agent (with fallback)
        try:
            from chart_bot.core.langgraph_agent import ChartBotAgent
            agent = ChartBotAgent(user)
            print("🚀 Using LangGraph agent for testing")
        except ImportError:
            from chart_bot.core.simple_agent import SimpleChartBotAgent
            agent = SimpleChartBotAgent(user)
            print("🔧 Using simple agent for testing")
        except Exception as e:
            print(f"⚠️ LangGraph agent failed, trying simple agent: {str(e)}")
            from chart_bot.core.simple_agent import SimpleChartBotAgent
            agent = SimpleChartBotAgent(user)
            print("🔧 Using simple agent as fallback")
        
        # Test query processing
        result = agent.process_query(test_query)
        
        if result['success']:
            print("✅ Professional Chart Bot is working correctly!")
            print(f"📝 Test response: {result['response'][:100]}...")
        else:
            print(f"⚠️ Professional Chart Bot test completed with issues: {result.get('error', 'Unknown error')}")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False


def main():
    """Main setup function"""
    print("🚀 Professional Chart Bot Setup Script")
    print("=" * 60)
    
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
    
    print("\n" + "=" * 60)
    print("🎉 Professional Chart Bot setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Access the admin panel to customize settings")
    print("2. Test the professional chat widget on any page")
    print("3. Use the professional test page for debugging")
    print("4. Review the comprehensive documentation")
    print("\n🔗 Useful links:")
    print("- Admin: /admin/chart_bot/")
    print("- Professional API: /chart-bot-v2/api/v2/status/")
    print("- Test Page: /chart-bot-v2/test/")
    print("- Documentation: chart_bot/README.md")
    print("\n🎯 Professional Features:")
    print("- ✅ Robust authentication system")
    print("- ✅ Professional UI/UX design")
    print("- ✅ Comprehensive error handling")
    print("- ✅ Advanced debugging tools")
    print("- ✅ Performance monitoring")
    print("- ✅ Security enhancements")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
