"""
Management command to setup Chart Bot
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from chart_bot.models import BotConfiguration


class Command(BaseCommand):
    help = 'Setup Chart Bot configuration'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--llm-endpoint',
            type=str,
            default='http://125.18.84.108:11434/api/generate',
            help='LLM endpoint URL'
        )
        parser.add_argument(
            '--llm-model',
            type=str,
            default='mistral',
            help='LLM model name'
        )
        parser.add_argument(
            '--bot-name',
            type=str,
            default='Chart Bot',
            help='Bot name'
        )
        parser.add_argument(
            '--enable',
            action='store_true',
            help='Enable the bot'
        )
    
    def handle(self, *args, **options):
        self.stdout.write('Setting up Chart Bot...')
        
        # Create or update bot configuration
        config, created = BotConfiguration.objects.get_or_create(
            defaults={
                'name': options['bot_name'],
                'llm_endpoint': options['llm_endpoint'],
                'llm_model': options['llm_model'],
                'is_enabled': options['enable'],
                'max_context_length': 10,
                'response_timeout': 30
            }
        )
        
        if not created:
            config.name = options['bot_name']
            config.llm_endpoint = options['llm_endpoint']
            config.llm_model = options['llm_model']
            config.is_enabled = options['enable']
            config.save()
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'Created Chart Bot configuration: {config.name}')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f'Updated Chart Bot configuration: {config.name}')
            )
        
        self.stdout.write(f'LLM Endpoint: {config.llm_endpoint}')
        self.stdout.write(f'LLM Model: {config.llm_model}')
        self.stdout.write(f'Enabled: {config.is_enabled}')
        
        self.stdout.write(
            self.style.SUCCESS('Chart Bot setup completed successfully!')
        )
