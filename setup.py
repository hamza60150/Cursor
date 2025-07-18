#!/usr/bin/env python3
"""
Setup script for LinkedIn Job Application Bot
"""

import os
import sys
import json
import subprocess
from pathlib import Path

def print_banner():
    """Print setup banner"""
    print("=" * 60)
    print("  LinkedIn Job Application Bot - Setup")
    print("=" * 60)
    print()

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print("❌ Error: Python 3.7 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def install_dependencies():
    """Install required dependencies"""
    print("\n📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    directories = ["logs", "screenshots", "data", "cookies", "backups"]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"   Created: {directory}/")
    
    print("✅ Directories created successfully")

def setup_profile():
    """Setup user profile"""
    print("\n👤 Setting up profile...")
    
    if os.path.exists("profile.json"):
        response = input("   Profile already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("   Keeping existing profile")
            return True
    
    profile = {
        "email": input("   Email address: "),
        "first_name": input("   First name: "),
        "last_name": input("   Last name: "),
        "phone": input("   Phone number (optional): ") or "",
        "address": input("   Address (optional): ") or "",
        "city": input("   City (optional): ") or "",
        "state": input("   State (optional): ") or "",
        "zip": input("   ZIP code (optional): ") or "",
        "country": input("   Country (optional): ") or "",
        "linkedin": input("   LinkedIn URL (optional): ") or "",
        "website": input("   Website URL (optional): ") or "",
        "resume_path": input("   Resume file path (optional): ") or "",
        "cover_letter": input("   Cover letter text (optional): ") or ""
    }
    
    try:
        with open("profile.json", "w") as f:
            json.dump(profile, f, indent=2)
        print("✅ Profile saved to profile.json")
        return True
    except Exception as e:
        print(f"❌ Failed to save profile: {e}")
        return False

def setup_environment():
    """Setup environment file"""
    print("\n🔧 Setting up environment...")
    
    if os.path.exists(".env"):
        response = input("   .env file already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("   Keeping existing .env file")
            return True
    
    try:
        # Copy example file
        if os.path.exists(".env.example"):
            import shutil
            shutil.copy(".env.example", ".env")
            print("✅ Environment file created from template")
            print("   Edit .env file to customize settings")
        else:
            print("   .env.example not found, skipping environment setup")
        return True
    except Exception as e:
        print(f"❌ Failed to create environment file: {e}")
        return False

def make_executable():
    """Make shell script executable"""
    print("\n🔧 Making scripts executable...")
    
    scripts = ["run_bot.sh"]
    for script in scripts:
        if os.path.exists(script):
            try:
                os.chmod(script, 0o755)
                print(f"   Made {script} executable")
            except Exception as e:
                print(f"   Warning: Could not make {script} executable: {e}")
    
    print("✅ Scripts setup complete")

def validate_setup():
    """Validate the setup"""
    print("\n✅ Validating setup...")
    
    required_files = ["linkedin_apply_bot.py", "requirements.txt", "profile.json"]
    missing_files = []
    
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing required files: {', '.join(missing_files)}")
        return False
    
    print("✅ All required files present")
    
    # Test imports
    try:
        import undetected_chromedriver
        import selenium
        print("✅ Required packages installed")
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        return False
    
    return True

def show_next_steps():
    """Show next steps to user"""
    print("\n🎉 Setup Complete!")
    print("\nNext steps:")
    print("1. Edit profile.json with your information")
    print("2. Place your resume file in the project directory")
    print("3. Create a jobs.json file with job listings")
    print("4. Run the bot:")
    print("   ./run_bot.sh")
    print("   OR")
    print("   python linkedin_apply_bot.py --jobs-file jobs.json --profile-file profile.json")
    print("\nFor more information, see README.md")

def main():
    """Main setup function"""
    print_banner()
    
    if not check_python_version():
        return 1
    
    steps = [
        ("Installing dependencies", install_dependencies),
        ("Creating directories", create_directories),
        ("Setting up profile", setup_profile),
        ("Setting up environment", setup_environment),
        ("Making scripts executable", make_executable),
        ("Validating setup", validate_setup)
    ]
    
    for step_name, step_func in steps:
        try:
            if not step_func():
                print(f"\n❌ Setup failed at: {step_name}")
                return 1
        except KeyboardInterrupt:
            print("\n\n⚠️ Setup interrupted by user")
            return 1
        except Exception as e:
            print(f"\n❌ Unexpected error during {step_name}: {e}")
            return 1
    
    show_next_steps()
    return 0

if __name__ == "__main__":
    sys.exit(main())