"""
Management command to test Chart Bot
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from chart_bot.core.langgraph_agent import ChartBotAgent
from chart_bot.models import BotConfiguration


class Command(BaseCommand):
    help = 'Test Chart Bot functionality'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Username to test with'
        )
        parser.add_argument(
            '--query',
            type=str,
            default='What is my attendance for this month?',
            help='Test query to send'
        )
    
    def handle(self, *args, **options):
        self.stdout.write('Testing Chart Bot...')
        
        # Check if bot is configured
        try:
            config = BotConfiguration.objects.first()
            if not config:
                self.stdout.write(
                    self.style.ERROR('Chart Bot is not configured. Run setup_chart_bot first.')
                )
                return
            
            if not config.is_enabled:
                self.stdout.write(
                    self.style.WARNING('Chart Bot is disabled. Enable it in admin or use --enable flag.')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error checking bot configuration: {str(e)}')
            )
            return
        
        # Get test user
        username = options.get('user')
        if not username:
            # Try to get first superuser
            user = User.objects.filter(is_superuser=True).first()
            if not user:
                user = User.objects.first()
        else:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User "{username}" not found.')
                )
                return
        
        if not user:
            self.stdout.write(
                self.style.ERROR('No users found in the system.')
            )
            return
        
        self.stdout.write(f'Testing with user: {user.username}')
        
        # Test the agent
        try:
            agent = ChartBotAgent(user)
            result = agent.process_query(options['query'])
            
            self.stdout.write(f'Query: {options["query"]}')
            self.stdout.write(f'Response: {result["response"]}')
            self.stdout.write(f'Success: {result["success"]}')
            
            if result.get('error'):
                self.stdout.write(
                    self.style.ERROR(f'Error: {result["error"]}')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS('Chart Bot test completed successfully!')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error testing Chart Bot: {str(e)}')
            )
