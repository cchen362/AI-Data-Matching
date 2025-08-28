#!/usr/bin/env python3
"""
Simple health check script for AI Data Matching Tool.
Verifies core functionality and dependencies.
"""

import sys
import os
import importlib.util
from pathlib import Path

def check_dependencies():
    """Check if core dependencies are installed."""
    required_packages = [
        'streamlit',
        'pandas', 
        'rapidfuzz',
        'plotly',
        'openpyxl',
        'jinja2',
        'requests',
        'openai'
    ]
    
    missing_packages = []
    for package in required_packages:
        spec = importlib.util.find_spec(package)
        if spec is None:
            missing_packages.append(package)
    
    return missing_packages

def check_environment():
    """Check environment configuration."""
    issues = []
    
    # Check OpenAI API key
    if not os.getenv('OPENAI_API_KEY'):
        issues.append("OPENAI_API_KEY environment variable not set")
    
    # Check source files exist
    src_path = Path(__file__).parent / 'src'
    required_files = [
        'config.py',
        'data_processor.py', 
        'matching_engine.py',
        'currency_converter.py',
        'export_manager.py'
    ]
    
    for file in required_files:
        if not (src_path / file).exists():
            issues.append(f"Missing required file: src/{file}")
    
    return issues

def main():
    """Run health checks."""
    print("🏥 AI Data Matching Tool - Health Check")
    print("=" * 50)
    
    # Check dependencies
    print("🔍 Checking dependencies...")
    missing = check_dependencies()
    if missing:
        print(f"❌ Missing packages: {', '.join(missing)}")
        print("Run: pip install -r requirements.txt")
        return 1
    else:
        print("✅ All dependencies installed")
    
    # Check environment
    print("\n🔍 Checking environment...")
    issues = check_environment()
    if issues:
        print("❌ Environment issues found:")
        for issue in issues:
            print(f"   - {issue}")
        return 1
    else:
        print("✅ Environment configured correctly")
    
    # Test imports
    print("\n🔍 Testing core imports...")
    try:
        from src.data_processor import DataProcessor
        from src.matching_engine import MatchingEngine
        from src.currency_converter import CurrencyConverter
        print("✅ Core modules imported successfully")
    except Exception as e:
        print(f"❌ Import error: {e}")
        return 1
    
    print("\n🎉 Health check passed! Application ready to run.")
    print("\nTo start the application:")
    print("  streamlit run app.py")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())