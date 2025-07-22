#!/usr/bin/env python3
"""
GitHub Integration Module for LinkedIn Job Application Bot
Handles GitHub repository management, issue tracking, and automation.
"""

import os
import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import requests
import base64

@dataclass
class GitHubConfig:
    """Configuration for GitHub integration"""
    token: str = ""
    repo_owner: str = ""
    repo_name: str = ""
    base_url: str = "https://api.github.com"
    webhook_secret: str = ""

@dataclass
class JobApplicationRecord:
    """Record of a job application for GitHub tracking"""
    job_title: str
    company: str
    application_date: datetime
    status: str  # applied, rejected, interview, offer
    platform: str
    job_url: str
    notes: str = ""

class GitHubIntegration:
    """Main GitHub integration class"""
    
    def __init__(self, config: GitHubConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.headers = {
            "Authorization": f"token {self.config.token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "LinkedIn-Job-Bot/1.0"
        }
    
    async def create_job_application_issue(self, job_data: Dict, application_result: Dict) -> Optional[int]:
        """Create a GitHub issue to track job application"""
        try:
            title = f"Job Application: {job_data.get('title', 'Unknown')} at {job_data.get('companyName', 'Unknown Company')}"
            
            body = self._create_issue_body(job_data, application_result)
            
            labels = self._get_application_labels(job_data, application_result)
            
            issue_data = {
                "title": title,
                "body": body,
                "labels": labels
            }
            
            url = f"{self.config.base_url}/repos/{self.config.repo_owner}/{self.config.repo_name}/issues"
            
            response = requests.post(url, headers=self.headers, json=issue_data)
            
            if response.status_code == 201:
                issue_number = response.json()["number"]
                self.logger.info(f"Created GitHub issue #{issue_number} for job application")
                return issue_number
            else:
                self.logger.error(f"Failed to create GitHub issue: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error creating GitHub issue: {e}")
            return None
    
    async def update_application_status(self, issue_number: int, new_status: str, notes: str = "") -> bool:
        """Update the status of a job application issue"""
        try:
            # Get current issue
            url = f"{self.config.base_url}/repos/{self.config.repo_owner}/{self.config.repo_name}/issues/{issue_number}"
            response = requests.get(url, headers=self.headers)
            
            if response.status_code != 200:
                self.logger.error(f"Failed to get issue #{issue_number}")
                return False
            
            issue = response.json()
            
            # Update labels
            current_labels = [label["name"] for label in issue["labels"]]
            new_labels = self._update_status_labels(current_labels, new_status)
            
            # Add comment with status update
            comment_body = f"**Status Update**: {new_status.title()}\n\n"
            if notes:
                comment_body += f"**Notes**: {notes}\n\n"
            comment_body += f"**Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Post comment
            comment_url = f"{url}/comments"
            comment_data = {"body": comment_body}
            
            comment_response = requests.post(comment_url, headers=self.headers, json=comment_data)
            
            # Update labels
            update_data = {"labels": new_labels}
            update_response = requests.patch(url, headers=self.headers, json=update_data)
            
            if comment_response.status_code == 201 and update_response.status_code == 200:
                self.logger.info(f"Updated issue #{issue_number} with status: {new_status}")
                return True
            else:
                self.logger.error(f"Failed to update issue #{issue_number}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error updating application status: {e}")
            return False
    
    async def get_application_statistics(self) -> Dict[str, Any]:
        """Get statistics about job applications from GitHub issues"""
        try:
            # Get all issues with job application labels
            url = f"{self.config.base_url}/repos/{self.config.repo_owner}/{self.config.repo_name}/issues"
            params = {
                "labels": "job-application",
                "state": "all",
                "per_page": 100
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                self.logger.error(f"Failed to get issues: {response.status_code}")
                return {}
            
            issues = response.json()
            
            stats = {
                "total_applications": len(issues),
                "status_breakdown": {},
                "platform_breakdown": {},
                "monthly_applications": {},
                "success_rate": 0.0
            }
            
            for issue in issues:
                labels = [label["name"] for label in issue["labels"]]
                
                # Count by status
                status = self._extract_status_from_labels(labels)
                stats["status_breakdown"][status] = stats["status_breakdown"].get(status, 0) + 1
                
                # Count by platform
                platform = self._extract_platform_from_labels(labels)
                stats["platform_breakdown"][platform] = stats["platform_breakdown"].get(platform, 0) + 1
                
                # Count by month
                created_date = datetime.fromisoformat(issue["created_at"].replace('Z', '+00:00'))
                month_key = created_date.strftime('%Y-%m')
                stats["monthly_applications"][month_key] = stats["monthly_applications"].get(month_key, 0) + 1
            
            # Calculate success rate
            total = stats["total_applications"]
            successful = stats["status_breakdown"].get("interview", 0) + stats["status_breakdown"].get("offer", 0)
            stats["success_rate"] = (successful / total * 100) if total > 0 else 0.0
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting application statistics: {e}")
            return {}
    
    async def backup_application_data(self, applications_data: List[Dict]) -> bool:
        """Backup application data to GitHub repository"""
        try:
            # Create backup file content
            backup_data = {
                "backup_date": datetime.now().isoformat(),
                "applications": applications_data,
                "total_count": len(applications_data)
            }
            
            content = json.dumps(backup_data, indent=2)
            encoded_content = base64.b64encode(content.encode()).decode()
            
            # Create file path with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = f"backups/applications_backup_{timestamp}.json"
            
            # Check if file exists
            url = f"{self.config.base_url}/repos/{self.config.repo_owner}/{self.config.repo_name}/contents/{file_path}"
            
            file_data = {
                "message": f"Backup job applications data - {timestamp}",
                "content": encoded_content,
                "branch": "main"
            }
            
            response = requests.put(url, headers=self.headers, json=file_data)
            
            if response.status_code == 201:
                self.logger.info(f"Successfully backed up application data to {file_path}")
                return True
            else:
                self.logger.error(f"Failed to backup data: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error backing up application data: {e}")
            return False
    
    async def create_weekly_report(self) -> bool:
        """Create a weekly report of job applications"""
        try:
            # Get applications from the last week
            one_week_ago = datetime.now() - timedelta(days=7)
            
            url = f"{self.config.base_url}/repos/{self.config.repo_owner}/{self.config.repo_name}/issues"
            params = {
                "labels": "job-application",
                "state": "all",
                "since": one_week_ago.isoformat(),
                "per_page": 100
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            
            if response.status_code != 200:
                return False
            
            issues = response.json()
            
            # Generate report
            report_title = f"Weekly Job Application Report - {datetime.now().strftime('%Y-%m-%d')}"
            report_body = self._generate_weekly_report_body(issues)
            
            # Create issue for the report
            report_data = {
                "title": report_title,
                "body": report_body,
                "labels": ["weekly-report", "job-application-summary"]
            }
            
            report_response = requests.post(
                f"{self.config.base_url}/repos/{self.config.repo_owner}/{self.config.repo_name}/issues",
                headers=self.headers,
                json=report_data
            )
            
            if report_response.status_code == 201:
                self.logger.info("Created weekly report issue")
                return True
            else:
                self.logger.error(f"Failed to create weekly report: {report_response.status_code}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error creating weekly report: {e}")
            return False
    
    def _create_issue_body(self, job_data: Dict, application_result: Dict) -> str:
        """Create the body content for a job application issue"""
        body = f"""
## Job Details
- **Company**: {job_data.get('companyName', 'N/A')}
- **Title**: {job_data.get('title', 'N/A')}
- **Location**: {job_data.get('location', 'N/A')}
- **Platform**: {job_data.get('platform', 'N/A')}
- **Job URL**: {job_data.get('link', ['N/A'])[0] if job_data.get('link') else 'N/A'}

## Application Details
- **Applied Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **Status**: {application_result.get('status', 'applied')}
- **Success**: {'✅' if application_result.get('success', False) else '❌'}

## Application Result
{application_result.get('message', 'Application submitted successfully')}

## Next Steps
- [ ] Follow up in 1 week
- [ ] Check application status
- [ ] Prepare for potential interview

## Notes
{application_result.get('notes', 'No additional notes')}
        """
        return body.strip()
    
    def _get_application_labels(self, job_data: Dict, application_result: Dict) -> List[str]:
        """Get appropriate labels for the job application issue"""
        labels = ["job-application"]
        
        # Add status label
        status = application_result.get('status', 'applied')
        labels.append(f"status-{status}")
        
        # Add platform label
        platform = job_data.get('platform', 'unknown').lower().replace(' ', '-')
        labels.append(f"platform-{platform}")
        
        # Add success/failure label
        if application_result.get('success', False):
            labels.append("application-success")
        else:
            labels.append("application-failed")
        
        return labels
    
    def _update_status_labels(self, current_labels: List[str], new_status: str) -> List[str]:
        """Update status labels for an issue"""
        # Remove old status labels
        updated_labels = [label for label in current_labels if not label.startswith("status-")]
        
        # Add new status label
        updated_labels.append(f"status-{new_status}")
        
        return updated_labels
    
    def _extract_status_from_labels(self, labels: List[str]) -> str:
        """Extract status from issue labels"""
        for label in labels:
            if label.startswith("status-"):
                return label.replace("status-", "")
        return "unknown"
    
    def _extract_platform_from_labels(self, labels: List[str]) -> str:
        """Extract platform from issue labels"""
        for label in labels:
            if label.startswith("platform-"):
                return label.replace("platform-", "")
        return "unknown"
    
    def _generate_weekly_report_body(self, issues: List[Dict]) -> str:
        """Generate the body content for weekly report"""
        total_applications = len(issues)
        
        if total_applications == 0:
            return "No job applications were submitted this week."
        
        # Count by status and platform
        status_counts = {}
        platform_counts = {}
        
        for issue in issues:
            labels = [label["name"] for label in issue["labels"]]
            status = self._extract_status_from_labels(labels)
            platform = self._extract_platform_from_labels(labels)
            
            status_counts[status] = status_counts.get(status, 0) + 1
            platform_counts[platform] = platform_counts.get(platform, 0) + 1
        
        report = f"""
## Weekly Job Application Summary

### Overview
- **Total Applications**: {total_applications}
- **Report Period**: {(datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')} to {datetime.now().strftime('%Y-%m-%d')}

### Status Breakdown
"""
        
        for status, count in status_counts.items():
            percentage = (count / total_applications) * 100
            report += f"- **{status.title()}**: {count} ({percentage:.1f}%)\n"
        
        report += "\n### Platform Breakdown\n"
        
        for platform, count in platform_counts.items():
            percentage = (count / total_applications) * 100
            report += f"- **{platform.title()}**: {count} ({percentage:.1f}%)\n"
        
        report += f"""

### Applications This Week
"""
        
        for issue in issues[:10]:  # Show first 10
            title = issue["title"]
            created_date = datetime.fromisoformat(issue["created_at"].replace('Z', '+00:00')).strftime('%Y-%m-%d')
            report += f"- [{title}](#{issue['number']}) - {created_date}\n"
        
        if total_applications > 10:
            report += f"\n... and {total_applications - 10} more applications.\n"
        
        return report.strip()

def load_github_config() -> GitHubConfig:
    """Load GitHub configuration from environment variables"""
    return GitHubConfig(
        token=os.getenv('GITHUB_TOKEN', ''),
        repo_owner=os.getenv('GITHUB_REPO_OWNER', ''),
        repo_name=os.getenv('GITHUB_REPO_NAME', ''),
        base_url=os.getenv('GITHUB_API_URL', 'https://api.github.com'),
        webhook_secret=os.getenv('GITHUB_WEBHOOK_SECRET', '')
    )
