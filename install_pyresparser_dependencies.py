#!/usr/bin/env python3
"""
Installation script for pyresparser dependencies
Run this script to install pyresparser and its dependencies
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"📦 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e.stderr}")
        return False

def main():
    print("🚀 Installing pyresparser dependencies for Sync HRMS")
    print("=" * 60)
    
    # Check if we're in a virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Virtual environment detected")
    else:
        print("⚠️  No virtual environment detected. Consider using a virtual environment.")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("Installation cancelled.")
            return
    
    # Install Python packages
    packages = [
        "pyresparser>=1.0.6",
        "spacy>=3.4.0", 
        "nltk>=3.8.0"
    ]
    
    print("\n📦 Installing Python packages...")
    for package in packages:
        if not run_command(f"pip install {package}", f"Installing {package}"):
            print(f"❌ Failed to install {package}")
            return
    
    # Download spaCy model
    print("\n🧠 Downloading spaCy English model...")
    if not run_command("python -m spacy download en_core_web_sm", "Downloading spaCy English model"):
        print("⚠️  spaCy model download failed. You can download it manually later:")
        print("   python -m spacy download en_core_web_sm")
    
    # Download NLTK data
    print("\n📚 Downloading NLTK words corpus...")
    if not run_command("python -m nltk.downloader words", "Downloading NLTK words corpus"):
        print("⚠️  NLTK data download failed. You can download it manually later:")
        print("   python -m nltk.downloader words")
    
    # Test the installation
    print("\n🧪 Testing installation...")
    try:
        import pyresparser
        print("✅ pyresparser imported successfully")
        
        import spacy
        try:
            nlp = spacy.load("en_core_web_sm")
            print("✅ spaCy English model loaded successfully")
        except OSError:
            print("⚠️  spaCy model not found - please download manually")
        
        import nltk
        try:
            nltk.data.find('corpora/words')
            print("✅ NLTK words corpus found")
        except LookupError:
            print("⚠️  NLTK words corpus not found - please download manually")
        
        print("\n🎉 Installation completed successfully!")
        print("\n📋 Next steps:")
        print("1. Test the integration: python test_pyresparser_integration.py")
        print("2. Upload a resume to test the enhanced parsing")
        print("3. Check the AI processing logs in the admin panel")
        
    except ImportError as e:
        print(f"❌ Installation test failed: {e}")
        print("Please check the error messages above and try again.")

if __name__ == "__main__":
    main()
