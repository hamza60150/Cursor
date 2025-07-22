#!/usr/bin/env python3
"""
Demo script for Enhanced LinkedIn Job Application Bot features
Demonstrates LLM integration and GitHub tracking capabilities.
"""

import asyncio
import json
import logging
from llm_integration import LLMIntegration, load_llm_config, JobAnalysis
from github_integration import GitHubIntegration, load_github_config

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def demo_llm_integration():
    """Demonstrate LLM integration features"""
    print("\n" + "="*50)
    print("🤖 LLM INTEGRATION DEMO")
    print("="*50)
    
    try:
        # Load configuration
        llm_config = load_llm_config()
        print(f"LLM Provider: {llm_config.provider.value}")
        print(f"Model: {llm_config.model}")
        
        # Initialize LLM integration
        llm = LLMIntegration(llm_config)
        
        # Sample job data
        job_data = {
            "title": "Senior Python Developer",
            "companyName": "TechCorp Inc.",
            "location": "San Francisco, CA",
            "description": "We are looking for an experienced Python developer to join our team. Requirements include 3+ years of Python experience, knowledge of Django/Flask, and experience with cloud platforms.",
            "requirements": [
                "3+ years Python experience",
                "Django or Flask framework",
                "Cloud platforms (AWS/GCP)",
                "RESTful API development",
                "Database design"
            ]
        }
        
        # Sample profile data
        profile_data = {
            "first_name": "John",
            "last_name": "Doe",
            "skills": ["Python", "Django", "AWS", "PostgreSQL", "REST APIs"],
            "experience": "5 years of Python development experience with Django and cloud platforms",
            "education": "BS Computer Science"
        }
        
        print("\n📋 Job Analysis:")
        print(f"Job: {job_data['title']} at {job_data['companyName']}")
        
        # Analyze job compatibility
        analysis = await llm.analyze_job_compatibility(job_data, profile_data)
        
        print(f"\n🎯 Relevance Score: {analysis.relevance_score}/100")
        print(f"�� Match Reasons:")
        for reason in analysis.match_reasons:
            print(f"  • {reason}")
        
        if analysis.concerns:
            print(f"⚠️  Concerns:")
            for concern in analysis.concerns:
                print(f"  • {concern}")
        
        print(f"\n💡 Suggested Skills to Highlight:")
        for skill in analysis.suggested_skills_to_highlight:
            print(f"  • {skill}")
        
        print(f"\n📋 Application Strategy:")
        print(f"  {analysis.application_strategy}")
        
        if analysis.custom_cover_letter:
            print(f"\n✉️  Custom Cover Letter Preview:")
            preview = analysis.custom_cover_letter[:200] + "..." if len(analysis.custom_cover_letter) > 200 else analysis.custom_cover_letter
            print(f"  {preview}")
        
        print("\n✅ LLM integration demo completed successfully!")
        
    except Exception as e:
        print(f"❌ LLM integration demo failed: {e}")
        print("💡 Make sure you have configured LLM_PROVIDER and API keys in .env file")
        print("💡 For local testing, install Ollama and run: ollama pull llama2")

async def demo_github_integration():
    """Demonstrate GitHub integration features"""
    print("\n" + "="*50)
    print("🐙 GITHUB INTEGRATION DEMO")
    print("="*50)
    
    try:
        # Load configuration
        github_config = load_github_config()
        print(f"Repository: {github_config.repo_owner}/{github_config.repo_name}")
        
        if not github_config.token:
            print("⚠️  GitHub token not configured. Skipping GitHub integration demo.")
            print("💡 Add GITHUB_TOKEN to .env file to enable GitHub features")
            return
        
        # Initialize GitHub integration
        github = GitHubIntegration(github_config)
        
        # Sample application data
        job_data = {
            "title": "Senior Python Developer",
            "companyName": "TechCorp Inc.",
            "location": "San Francisco, CA",
            "platform": "LinkedIn",
            "link": ["https://linkedin.com/jobs/view/123456"]
        }
        
        application_result = {
            "success": True,
            "status": "applied",
            "message": "Application submitted successfully",
            "timestamp": "2024-01-15T10:30:00Z"
        }
        
        print("\n📊 Getting Application Statistics:")
        stats = await github.get_application_statistics()
        
        if stats:
            print(f"Total Applications: {stats.get('total_applications', 0)}")
            print(f"Success Rate: {stats.get('success_rate', 0):.1f}%")
            
            status_breakdown = stats.get('status_breakdown', {})
            if status_breakdown:
                print("Status Breakdown:")
                for status, count in status_breakdown.items():
                    print(f"  • {status.title()}: {count}")
        else:
            print("No application statistics available yet")
        
        print("\n📝 Demo: Creating Job Application Issue")
        print("(This would create a real GitHub issue in your repository)")
        print(f"Title: Job Application: {job_data['title']} at {job_data['companyName']}")
        print(f"Labels: job-application, status-applied, platform-linkedin")
        
        # Uncomment the following lines to create a real issue:
        # issue_number = await github.create_job_application_issue(job_data, application_result)
        # if issue_number:
        #     print(f"✅ Created GitHub issue #{issue_number}")
        #     
        #     # Demo status update
        #     await github.update_application_status(issue_number, "interview", "Scheduled for next week")
        #     print(f"✅ Updated issue status to 'interview'")
        
        print("\n✅ GitHub integration demo completed successfully!")
        
    except Exception as e:
        print(f"❌ GitHub integration demo failed: {e}")
        print("💡 Make sure you have configured GITHUB_TOKEN and repository details in .env file")

def demo_configuration():
    """Show current configuration"""
    print("\n" + "="*50)
    print("⚙️  CONFIGURATION OVERVIEW")
    print("="*50)
    
    # Check .env file
    env_file = ".env"
    try:
        with open(env_file, 'r') as f:
            env_content = f.read()
        
        print("✅ .env file found")
        
        # Check key configurations
        configs_to_check = [
            "LLM_PROVIDER",
            "LLM_MODEL", 
            "GITHUB_TOKEN",
            "GITHUB_REPO_OWNER",
            "GITHUB_REPO_NAME"
        ]
        
        for config in configs_to_check:
            if f"{config}=" in env_content:
                # Don't show actual values for security
                print(f"✅ {config} is configured")
            else:
                print(f"❌ {config} is not configured")
        
    except FileNotFoundError:
        print("❌ .env file not found")
        print("💡 Run: python3 setup_enhanced_bot.py to create configuration")
    
    # Check required files
    files_to_check = [
        "profile.json",
        "jobs.json",
        "requirements.txt"
    ]
    
    print("\n📁 Required Files:")
    for file_name in files_to_check:
        try:
            with open(file_name, 'r') as f:
                content = f.read()
            print(f"✅ {file_name} exists ({len(content)} bytes)")
        except FileNotFoundError:
            print(f"❌ {file_name} not found")

async def main():
    """Main demo function"""
    print("🚀 ENHANCED LINKEDIN JOB APPLICATION BOT DEMO")
    print("This demo showcases the new AI and GitHub integration features")
    
    # Show configuration
    demo_configuration()
    
    # Demo LLM integration
    await demo_llm_integration()
    
    # Demo GitHub integration
    await demo_github_integration()
    
    print("\n" + "="*50)
    print("🎉 DEMO COMPLETED")
    print("="*50)
    print("\n📚 Next Steps:")
    print("1. Configure your .env file with API keys")
    print("2. Update profile.json with your information")
    print("3. Add job listings to jobs.json")
    print("4. Run: ./run_enhanced_bot.sh")
    print("\n💡 For full setup, run: python3 setup_enhanced_bot.py")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n❌ Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demo failed: {e}")
        logger.error(f"Demo error: {e}")
