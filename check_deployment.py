#!/usr/bin/env python
"""
Pre-Deployment Checklist Script for Railway
Run this before deploying to catch common issues
"""

import os
import sys
from pathlib import Path

# Colors for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def check_file_exists(filepath, required=True):
    """Check if a file exists"""
    exists = Path(filepath).exists()
    status = f"{GREEN}✓{RESET}" if exists else f"{RED}✗{RESET}"
    req_label = "(Required)" if required else "(Optional)"
    print(f"{status} {filepath} {req_label}")
    return exists if required else True

def check_env_example():
    """Check if env.example has all required variables"""
    required_vars = [
        'SECRET_KEY',
        'DATABASE_URL',
        'DJANGO_SETTINGS_MODULE',
        'ALLOWED_HOSTS',
        'CORS_ALLOWED_ORIGINS',
        'JWT_ACCESS_TOKEN_LIFETIME_MINUTES',
        'JWT_REFRESH_TOKEN_LIFETIME_DAYS',
        'KOLOSAL_API_KEY',
        'SUPABASE_URL',
        'SUPABASE_ANON_KEY',
    ]
    
    try:
        with open('env.example', 'r') as f:
            content = f.read()
        
        missing = []
        for var in required_vars:
            if var not in content:
                missing.append(var)
        
        if missing:
            print(f"{RED}✗{RESET} env.example missing variables: {', '.join(missing)}")
            return False
        else:
            print(f"{GREEN}✓{RESET} env.example has all required variables")
            return True
    except FileNotFoundError:
        print(f"{RED}✗{RESET} env.example not found")
        return False

def check_requirements():
    """Check if production requirements include necessary packages"""
    required_packages = [
        'gunicorn',
        'whitenoise',
        'psycopg2-binary',
        'dj-database-url',
    ]
    
    try:
        with open('requirements/production.txt', 'r') as f:
            content = f.read().lower()
        
        missing = []
        for package in required_packages:
            if package.lower() not in content:
                missing.append(package)
        
        if missing:
            print(f"{RED}✗{RESET} production.txt missing packages: {', '.join(missing)}")
            return False
        else:
            print(f"{GREEN}✓{RESET} production.txt has all required packages")
            return True
    except FileNotFoundError:
        print(f"{RED}✗{RESET} requirements/production.txt not found")
        return False

def check_settings():
    """Check production settings configuration"""
    try:
        with open('config/settings/production.py', 'r') as f:
            content = f.read()
        
        checks = {
            'dj_database_url imported': 'dj_database_url' in content,
            'WhiteNoise configured': 'whitenoise' in content.lower(),
            'SECURE_SSL_REDIRECT': 'SECURE_SSL_REDIRECT' in content,
            'SECURE_PROXY_SSL_HEADER': 'SECURE_PROXY_SSL_HEADER' in content,
        }
        
        all_good = True
        for check, result in checks.items():
            status = f"{GREEN}✓{RESET}" if result else f"{RED}✗{RESET}"
            print(f"{status} Production settings: {check}")
            if not result:
                all_good = False
        
        return all_good
    except FileNotFoundError:
        print(f"{RED}✗{RESET} config/settings/production.py not found")
        return False

def main():
    """Run all checks"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Railway Pre-Deployment Checklist{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")
    
    all_checks_passed = True
    
    # Check Railway configuration files
    print(f"{YELLOW}Checking Railway Configuration Files:{RESET}")
    all_checks_passed &= check_file_exists('railway.json', required=True)
    all_checks_passed &= check_file_exists('Procfile', required=True)
    all_checks_passed &= check_file_exists('nixpacks.toml', required=True)
    all_checks_passed &= check_file_exists('runtime.txt', required=True)
    all_checks_passed &= check_file_exists('.railwayignore', required=False)
    
    # Check documentation
    print(f"\n{YELLOW}Checking Documentation:{RESET}")
    check_file_exists('RAILWAY_DEPLOYMENT_GUIDE.md', required=False)
    check_file_exists('RAILWAY_QUICK_START.md', required=False)
    
    # Check environment configuration
    print(f"\n{YELLOW}Checking Environment Configuration:{RESET}")
    all_checks_passed &= check_env_example()
    
    # Check requirements
    print(f"\n{YELLOW}Checking Requirements:{RESET}")
    all_checks_passed &= check_requirements()
    
    # Check settings
    print(f"\n{YELLOW}Checking Django Settings:{RESET}")
    all_checks_passed &= check_settings()
    
    # Check middleware
    print(f"\n{YELLOW}Checking Middleware Configuration:{RESET}")
    try:
        with open('config/settings/base.py', 'r') as f:
            content = f.read()
        
        if 'whitenoise.middleware.WhiteNoiseMiddleware' in content:
            print(f"{GREEN}✓{RESET} WhiteNoise middleware configured in base.py")
        else:
            print(f"{RED}✗{RESET} WhiteNoise middleware not found in base.py")
            all_checks_passed = False
    except FileNotFoundError:
        print(f"{RED}✗{RESET} config/settings/base.py not found")
        all_checks_passed = False
    
    # Final result
    print(f"\n{BLUE}{'='*60}{RESET}")
    if all_checks_passed:
        print(f"{GREEN}✓ All required checks passed! Ready to deploy.{RESET}")
        print(f"\n{YELLOW}Next steps:{RESET}")
        print("1. Push to GitHub: git push origin main")
        print("2. Deploy on Railway: https://railway.app")
        print("3. Configure environment variables")
        print("4. Monitor deployment logs")
        print(f"\n{BLUE}See RAILWAY_DEPLOYMENT_GUIDE.md for detailed instructions.{RESET}")
        return 0
    else:
        print(f"{RED}✗ Some checks failed. Please fix issues before deploying.{RESET}")
        print(f"\n{YELLOW}Tip: Review RAILWAY_DEPLOYMENT_GUIDE.md for help.{RESET}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
