#!/usr/bin/env python3
"""
Setup script for Enhanced LinkedIn Job Application Bot
Configures LLM integration, GitHub integration, and all necessary components.
"""

import os
import sys
import json
import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Optional

def print_banner():
    """Print setup banner"""
    banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║    Enhanced LinkedIn Job Application Bot Setup              ║
║    ═══════════════════════════════════════════════════════   ║
║                                                              ║
║    Features:                                                 ║
║    • LLM-powered job analysis and cover letter generation    ║
║    • GitHub integration for application tracking            ║
║    • Automated webhook handling                             ║
║    • Intelligent job filtering                              ║
║    • Comprehensive reporting                                ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 8):
        print("❌ Error: Python 3.8 or higher is required")
        print(f"Current version: {sys.version}")
        sys.exit(1)
    print(f"✅ Python version: {sys.version.split()[0]}")

def install_dependencies():
    """Install required Python packages"""
    print("\n📦 Installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing dependencies: {e}")
        sys.exit(1)

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    directories = [
        "logs",
        "reports",
        "screenshots",
        "backups",
        "cookies",
        "data"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")

def setup_environment_file():
    """Setup .env file from template"""
    print("\n⚙️  Setting up environment configuration...")
    
    if os.path.exists('.env'):
        print("⚠️  .env file already exists. Backing up as .env.backup")
        shutil.copy('.env', '.env.backup')
    
    # Copy template
    shutil.copy('.env.example', '.env')
    print("✅ Created .env file from template")
    print("📝 Please edit .env file with your actual configuration values")

def setup_profile_template():
    """Create profile template if it doesn't exist"""
    print("\n👤 Setting up profile template...")
    
    profile_file = "profile.json"
    if os.path.exists(profile_file):
        print(f"⚠️  {profile_file} already exists. Skipping template creation.")
        return
    
    profile_template = {
        "email": "your.email@example.com",
        "first_name": "Your",
        "last_name": "Name",
        "phone": "+1-555-123-4567",
        "address": "123 Main Street",
        "city": "Your City",
        "state": "ST",
        "zip": "12345",
        "country": "United States",
        "linkedin": "https://linkedin.com/in/yourprofile",
        "website": "https://yourwebsite.com",
        "resume_path": "./resume.pdf",
        "cover_letter": "Dear Hiring Manager,\n\nI am writing to express my interest in the position...",
        "skills": [
            "Python",
            "JavaScript",
            "React",
            "Node.js",
            "SQL",
            "Git"
        ],
        "experience": "Software Developer with 3+ years of experience...",
        "education": "Bachelor's in Computer Science"
    }
    
    with open(profile_file, 'w') as f:
        json.dump(profile_template, f, indent=2)
    
    print(f"✅ Created {profile_file} template")
    print("📝 Please update the profile.json file with your actual information")

def setup_jobs_template():
    """Create jobs template if it doesn't exist"""
    print("\n💼 Setting up jobs template...")
    
    jobs_file = "jobs.json"
    if os.path.exists(jobs_file):
        print(f"⚠️  {jobs_file} already exists. Using existing file.")
        return
    
    # Check if jobs_sample.json exists and use it
    if os.path.exists("jobs_sample.json"):
        shutil.copy("jobs_sample.json", jobs_file)
        print(f"✅ Copied jobs_sample.json to {jobs_file}")
    else:
        # Create a minimal template
        jobs_template = [
            {
                "title": "Software Engineer",
                "companyName": "Example Company",
                "location": "San Francisco, CA",
                "description": "We are looking for a talented software engineer...",
                "applyLinksDetails": [
                    {
                        "platform": "LinkedIn",
                        "url": "https://www.linkedin.com/jobs/view/1234567890"
                    }
                ],
                "link": ["https://www.linkedin.com/jobs/view/1234567890"]
            }
        ]
        
        with open(jobs_file, 'w') as f:
            json.dump(jobs_template, f, indent=2)
        
        print(f"✅ Created {jobs_file} template")
    
    print("📝 Please update the jobs.json file with actual job listings")

def check_ollama_installation():
    """Check if Ollama is installed for local LLM"""
    print("\n🤖 Checking Ollama installation...")
    
    try:
        result = subprocess.run(['ollama', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ Ollama is installed")
            print("💡 You can use local LLM models with Ollama")
            
            # Check if any models are installed
            try:
                models_result = subprocess.run(['ollama', 'list'], capture_output=True, text=True)
                if 'llama2' in models_result.stdout:
                    print("✅ Llama2 model is available")
                else:
                    print("💡 Consider installing Llama2: ollama pull llama2")
            except:
                pass
        else:
            print("⚠️  Ollama not found")
    except FileNotFoundError:
        print("⚠️  Ollama not installed")
        print("💡 Install Ollama from https://ollama.ai for local LLM support")
        print("💡 Or configure OpenAI/Anthropic API keys in .env file")

def setup_github_integration():
    """Provide GitHub integration setup instructions"""
    print("\n🐙 GitHub Integration Setup:")
    print("1. Create a GitHub Personal Access Token:")
    print("   - Go to GitHub Settings > Developer settings > Personal access tokens")
    print("   - Create a token with 'repo' and 'issues' permissions")
    print("   - Add the token to GITHUB_TOKEN in .env file")
    print("")
    print("2. Configure repository settings:")
    print("   - Set GITHUB_REPO_OWNER to your GitHub username")
    print("   - Set GITHUB_REPO_NAME to your repository name")
    print("")
    print("3. Optional: Setup webhook for automation:")
    print("   - Go to your repository Settings > Webhooks")
    print("   - Add webhook URL: http://your-server:5000/webhook/github")
    print("   - Select 'Issues' and 'Issue comments' events")

def create_startup_scripts():
    """Create startup scripts for different components"""
    print("\n🚀 Creating startup scripts...")
    
    # Enhanced bot script
    enhanced_bot_script = """#!/bin/bash
# Enhanced LinkedIn Job Application Bot Startup Script

echo "Starting Enhanced LinkedIn Job Application Bot..."

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Run the enhanced bot
python3 enhanced_bot.py \\
    --jobs-file jobs.json \\
    --profile-file profile.json \\
    --max-applications ${MAX_APPLICATIONS:-5} \\
    --verbose \\
    --log-file logs/bot_$(date +%Y%m%d_%H%M%S).log

echo "Bot execution completed. Check logs for details."
"""
    
    with open('run_enhanced_bot.sh', 'w') as f:
        f.write(enhanced_bot_script)
    os.chmod('run_enhanced_bot.sh', 0o755)
    
    # Webhook server script
    webhook_script = """#!/bin/bash
# GitHub Webhook Server Startup Script

echo "Starting GitHub Webhook Server..."

# Load environment variables
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# Run the webhook server
python3 webhook_handler.py

echo "Webhook server stopped."
"""
    
    with open('run_webhook_server.sh', 'w') as f:
        f.write(webhook_script)
    os.chmod('run_webhook_server.sh', 0o755)
    
    print("✅ Created run_enhanced_bot.sh")
    print("✅ Created run_webhook_server.sh")

def display_next_steps():
    """Display next steps for the user"""
    print("\n" + "="*60)
    print("🎉 SETUP COMPLETED SUCCESSFULLY!")
    print("="*60)
    print("\n📋 Next Steps:")
    print("1. Edit .env file with your configuration:")
    print("   - Add your GitHub token")
    print("   - Configure LLM provider (OpenAI/Anthropic API key or use Ollama)")
    print("   - Set your repository details")
    print("")
    print("2. Update profile.json with your personal information")
    print("")
    print("3. Add job listings to jobs.json")
    print("")
    print("4. Test the setup:")
    print("   ./run_enhanced_bot.sh")
    print("")
    print("5. Optional: Start webhook server for GitHub automation:")
    print("   ./run_webhook_server.sh")
    print("")
    print("📚 Documentation:")
    print("- Check README.md for detailed usage instructions")
    print("- See example files for configuration templates")
    print("- Review logs/ directory for execution details")
    print("")
    print("🆘 Need help? Check the GitHub repository for support")

def main():
    """Main setup function"""
    print_banner()
    
    print("🔍 Checking system requirements...")
    check_python_version()
    
    install_dependencies()
    create_directories()
    setup_environment_file()
    setup_profile_template()
    setup_jobs_template()
    check_ollama_installation()
    setup_github_integration()
    create_startup_scripts()
    
    display_next_steps()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Setup failed: {e}")
        sys.exit(1)
