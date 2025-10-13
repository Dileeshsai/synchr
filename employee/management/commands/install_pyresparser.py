"""
Django management command to install pyresparser dependencies
"""

import subprocess
import sys
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Install pyresparser and its dependencies for enhanced resume parsing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force reinstall even if already installed',
        )
        parser.add_argument(
            '--skip-models',
            action='store_true',
            help='Skip downloading spaCy and NLTK models',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Installing pyresparser dependencies...')
        )
        
        # List of packages to install
        packages = [
            'pyresparser>=1.0.6',
            'spacy>=3.4.0',
            'nltk>=3.8.0'
        ]
        
        # Install Python packages
        for package in packages:
            try:
                self.stdout.write(f'📦 Installing {package}...')
                cmd = [sys.executable, '-m', 'pip', 'install', package]
                if options['force']:
                    cmd.append('--force-reinstall')
                
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ {package} installed successfully')
                    )
                else:
                    self.stdout.write(
                        self.style.ERROR(f'❌ Failed to install {package}: {result.stderr}')
                    )
                    raise CommandError(f'Failed to install {package}')
                    
            except Exception as e:
                raise CommandError(f'Error installing {package}: {str(e)}')
        
        # Download spaCy model
        if not options['skip_models']:
            try:
                self.stdout.write('🧠 Downloading spaCy English model...')
                result = subprocess.run(
                    [sys.executable, '-m', 'spacy', 'download', 'en_core_web_sm'],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    self.stdout.write(
                        self.style.SUCCESS('✅ spaCy English model downloaded successfully')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️  spaCy model download failed: {result.stderr}')
                    )
                    self.stdout.write('   You can download it manually: python -m spacy download en_core_web_sm')
                    
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Error downloading spaCy model: {str(e)}')
                )
        
        # Download NLTK data
        if not options['skip_models']:
            try:
                self.stdout.write('📚 Downloading NLTK words corpus...')
                result = subprocess.run(
                    [sys.executable, '-m', 'nltk.downloader', 'words'],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    self.stdout.write(
                        self.style.SUCCESS('✅ NLTK words corpus downloaded successfully')
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(f'⚠️  NLTK data download failed: {result.stderr}')
                    )
                    self.stdout.write('   You can download it manually: python -m nltk.downloader words')
                    
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Error downloading NLTK data: {str(e)}')
                )
        
        # Test the installation
        self.stdout.write('\n🧪 Testing installation...')
        try:
            from pyresparser import ResumeParser
            import spacy
            import nltk
            
            # Test spaCy model
            try:
                nlp = spacy.load("en_core_web_sm")
                self.stdout.write(self.style.SUCCESS('✅ spaCy model test passed'))
            except OSError:
                self.stdout.write(self.style.WARNING('⚠️  spaCy model not found - please download manually'))
            
            # Test NLTK
            try:
                nltk.data.find('corpora/words')
                self.stdout.write(self.style.SUCCESS('✅ NLTK words corpus test passed'))
            except LookupError:
                self.stdout.write(self.style.WARNING('⚠️  NLTK words corpus not found - please download manually'))
            
            self.stdout.write(
                self.style.SUCCESS('\n🎉 pyresparser installation completed successfully!')
            )
            self.stdout.write('\n📋 Next steps:')
            self.stdout.write('1. Test the integration: python test_pyresparser_integration.py')
            self.stdout.write('2. Upload a resume to test the enhanced parsing')
            self.stdout.write('3. Check the AI processing logs in the admin panel')
            
        except ImportError as e:
            raise CommandError(f'Installation test failed: {str(e)}')
