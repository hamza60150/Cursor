#!/usr/bin/env python3
"""
Enhanced LinkedIn Job Application Bot with LLM and GitHub Integration
Main controller that orchestrates the LLM analysis and GitHub tracking.
"""

import json
import time
import random
import os
import sys
import argparse
import signal
import traceback
import logging
import asyncio
from urllib.parse import urlparse
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

# Import existing modules
from linkedin_apply_bot import LinkedInJobBot
from llm_integration import LLMIntegration, load_llm_config
from github_integration import GitHubIntegration, load_github_config
from config import DEFAULT_CONFIG

class EnhancedJobBot:
    """Enhanced job application bot with LLM and GitHub integration"""
    
    def __init__(self, jobs_file: str, profile_file: str, **kwargs):
        self.jobs_file = jobs_file
        self.profile_file = profile_file
        self.config = DEFAULT_CONFIG
        
        # Setup logging
        self.setup_logging(kwargs.get('log_file'), kwargs.get('verbose', False))
        self.logger = logging.getLogger(__name__)
        
        # Load configurations
        self.llm_config = load_llm_config()
        self.github_config = load_github_config()
        
        # Initialize integrations
        self.llm_integration = LLMIntegration(self.llm_config) if self.llm_config.api_key or self.llm_config.provider.value == 'ollama' else None
        self.github_integration = GitHubIntegration(self.github_config) if self.github_config.token else None
        
        # Initialize base bot
        self.base_bot = None
        
        # Application tracking
        self.application_results = []
        self.session_stats = {
            'total_jobs': 0,
            'analyzed_jobs': 0,
            'applied_jobs': 0,
            'skipped_jobs': 0,
            'failed_jobs': 0,
            'start_time': datetime.now()
        }
        
        self.logger.info("Enhanced Job Bot initialized")
        if self.llm_integration:
            self.logger.info(f"LLM integration enabled: {self.llm_config.provider.value}")
        if self.github_integration:
            self.logger.info("GitHub integration enabled")
    
    def setup_logging(self, log_file: Optional[str], verbose: bool):
        """Setup logging configuration"""
        level = logging.DEBUG if verbose else logging.INFO
        format_str = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(logging.Formatter(format_str))
        
        # Configure root logger
        logging.basicConfig(level=level, format=format_str, handlers=[console_handler])
        
        # File handler if specified
        if log_file:
            file_handler = logging.FileHandler(log_file)
            file_handler.setLevel(level)
            file_handler.setFormatter(logging.Formatter(format_str))
            logging.getLogger().addHandler(file_handler)
    
    async def run(self, **kwargs):
        """Main execution method"""
        try:
            self.logger.info("Starting enhanced job application bot")
            
            # Load jobs and profile data
            jobs_data = self.load_jobs_data()
            profile_data = self.load_profile_data()
            
            if not jobs_data or not profile_data:
                self.logger.error("Failed to load required data files")
                return False
            
            self.session_stats['total_jobs'] = len(jobs_data)
            self.logger.info(f"Loaded {len(jobs_data)} jobs and profile data")
            
            # Process jobs
            max_applications = kwargs.get('max_applications', self.config.MAX_APPLICATIONS_PER_RUN)
            applications_made = 0
            
            for i, job in enumerate(jobs_data):
                if applications_made >= max_applications:
                    self.logger.info(f"Reached maximum applications limit: {max_applications}")
                    break
                
                self.logger.info(f"Processing job {i+1}/{len(jobs_data)}: {job.get('title', 'Unknown')} at {job.get('companyName', 'Unknown')}")
                
                # Analyze job with LLM if available
                job_analysis = None
                if self.llm_integration:
                    try:
                        job_analysis = await self.llm_integration.analyze_job_compatibility(job, profile_data)
                        self.session_stats['analyzed_jobs'] += 1
                        self.logger.info(f"Job relevance score: {job_analysis.relevance_score}/100")
                        
                        # Skip job if relevance is too low
                        if job_analysis.relevance_score < 60:
                            self.logger.info(f"Skipping job due to low relevance score: {job_analysis.relevance_score}")
                            self.session_stats['skipped_jobs'] += 1
                            continue
                            
                    except Exception as e:
                        self.logger.error(f"LLM analysis failed: {e}")
                
                # Apply to job
                application_result = await self.apply_to_job(job, profile_data, job_analysis)
                
                if application_result.get('success', False):
                    applications_made += 1
                    self.session_stats['applied_jobs'] += 1
                    
                    # Create GitHub issue for tracking
                    if self.github_integration:
                        try:
                            issue_number = await self.github_integration.create_job_application_issue(job, application_result)
                            if issue_number:
                                application_result['github_issue'] = issue_number
                        except Exception as e:
                            self.logger.error(f"Failed to create GitHub issue: {e}")
                else:
                    self.session_stats['failed_jobs'] += 1
                
                # Store result
                self.application_results.append({
                    'job': job,
                    'result': application_result,
                    'analysis': job_analysis.__dict__ if job_analysis else None,
                    'timestamp': datetime.now().isoformat()
                })
                
                # Random delay between applications
                delay = random.uniform(self.config.MIN_DELAY, self.config.MAX_DELAY)
                self.logger.info(f"Waiting {delay:.1f} seconds before next application...")
                time.sleep(delay)
            
            # Generate final report
            await self.generate_session_report()
            
            # Backup data to GitHub
            if self.github_integration:
                try:
                    await self.github_integration.backup_application_data(self.application_results)
                except Exception as e:
                    self.logger.error(f"Failed to backup data: {e}")
            
            self.logger.info("Enhanced job application bot completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Fatal error in bot execution: {e}")
            self.logger.error(traceback.format_exc())
            return False
        finally:
            if self.base_bot:
                try:
                    self.base_bot.cleanup()
                except:
                    pass
    
    async def apply_to_job(self, job: Dict, profile: Dict, analysis=None) -> Dict:
        """Apply to a single job with enhanced features"""
        try:
            # Use custom cover letter from LLM analysis if available
            if analysis and analysis.custom_cover_letter:
                profile = profile.copy()
                profile['cover_letter'] = analysis.custom_cover_letter
                self.logger.info("Using LLM-generated custom cover letter")
            
            # Initialize base bot if needed
            if not self.base_bot:
                # Import and initialize the existing bot
                # This is a simplified version - you might need to adapt based on your existing bot structure
                self.base_bot = LinkedInJobBot(profile, self.config)
            
            # Apply to job using existing bot logic
            result = await self.base_bot.apply_to_job(job)
            
            # Enhance result with analysis data
            if analysis:
                result['llm_analysis'] = {
                    'relevance_score': analysis.relevance_score,
                    'match_reasons': analysis.match_reasons,
                    'application_strategy': analysis.application_strategy
                }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error applying to job: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def load_jobs_data(self) -> List[Dict]:
        """Load jobs data from file"""
        try:
            with open(self.jobs_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading jobs file: {e}")
            return []
    
    def load_profile_data(self) -> Dict:
        """Load profile data from file"""
        try:
            with open(self.profile_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Error loading profile file: {e}")
            return {}
    
    async def generate_session_report(self):
        """Generate and log session report"""
        end_time = datetime.now()
        duration = end_time - self.session_stats['start_time']
        
        report = f"""
=== ENHANCED JOB APPLICATION BOT SESSION REPORT ===
Start Time: {self.session_stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')}
End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}
Duration: {duration}

Job Statistics:
- Total Jobs: {self.session_stats['total_jobs']}
- Analyzed Jobs: {self.session_stats['analyzed_jobs']}
- Applied Jobs: {self.session_stats['applied_jobs']}
- Skipped Jobs: {self.session_stats['skipped_jobs']}
- Failed Jobs: {self.session_stats['failed_jobs']}

Success Rate: {(self.session_stats['applied_jobs'] / max(1, self.session_stats['total_jobs']) * 100):.1f}%

Integrations:
- LLM Integration: {'✅' if self.llm_integration else '❌'}
- GitHub Integration: {'✅' if self.github_integration else '❌'}
        """
        
        self.logger.info(report)
        
        # Save detailed report to file
        report_file = f"reports/session_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        
        detailed_report = {
            'session_stats': self.session_stats,
            'application_results': self.application_results,
            'config': {
                'llm_enabled': self.llm_integration is not None,
                'github_enabled': self.github_integration is not None,
                'llm_provider': self.llm_config.provider.value if self.llm_integration else None
            }
        }
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(detailed_report, f, indent=2, default=str)
            self.logger.info(f"Detailed report saved to: {report_file}")
        except Exception as e:
            self.logger.error(f"Failed to save detailed report: {e}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Enhanced LinkedIn Job Application Bot with LLM and GitHub Integration')
    parser.add_argument('--jobs-file', required=True, help='Path to jobs JSON file')
    parser.add_argument('--profile-file', required=True, help='Path to profile JSON file')
    parser.add_argument('--max-applications', type=int, default=5, help='Maximum number of applications to submit')
    parser.add_argument('--log-file', help='Path to log file')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--headless', action='store_true', help='Run browser in headless mode')
    
    args = parser.parse_args()
    
    # Create bot instance
    bot = EnhancedJobBot(
        jobs_file=args.jobs_file,
        profile_file=args.profile_file
    )
    
    # Run the bot
    try:
        result = asyncio.run(bot.run(
            max_applications=args.max_applications,
            log_file=args.log_file,
            verbose=args.verbose,
            headless=args.headless
        ))
        
        sys.exit(0 if result else 1)
        
    except KeyboardInterrupt:
        print("\nBot execution interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
