#!/usr/bin/env python3
"""
Adaptive Web Automation Agent for Job Applications
Uses LLM intelligence to navigate any website structure and auto-apply to jobs.
"""

import os
import json
import time
import random
import logging
import asyncio
import base64
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from datetime import datetime
import pickle
import hashlib

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import requests

from llm_integration import LLMIntegration, load_llm_config

@dataclass
class NavigationStep:
    """Represents a single navigation step"""
    action_type: str  # click, fill, select, wait, scroll
    selector: str
    value: Optional[str] = None
    description: str = ""
    confidence: float = 0.0

@dataclass
class WebsiteAnalysis:
    """Analysis of a website's structure"""
    page_type: str  # job_listing, application_form, login, success, error
    detected_elements: List[Dict]
    suggested_actions: List[NavigationStep]
    obstacles: List[str]  # bot_detection, captcha, login_required
    confidence_score: float

@dataclass
class JobApplicationInput:
    """Input data for job application"""
    job_title: str
    parsed_resume: Dict[str, Any]
    target_html: str
    website_url: str
    additional_data: Optional[Dict] = None

class AdaptiveWebAgent:
    """Main adaptive web automation agent"""
    
    def __init__(self, llm_integration: LLMIntegration):
        self.llm = llm_integration
        self.logger = logging.getLogger(__name__)
        self.driver = None
        self.cookies_cache = {}
        self.html_cache = {}
        self.navigation_history = []
        self.retry_strategies = []
        self.current_session_id = self._generate_session_id()
        
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        timestamp = datetime.now().isoformat()
        return hashlib.md5(timestamp.encode()).hexdigest()[:8]
    
    async def initialize_browser(self, headless: bool = False) -> bool:
        """Initialize browser with anti-detection measures"""
        try:
            options = uc.ChromeOptions()
            
            # Anti-detection settings
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-gpu")
            
            if headless:
                options.add_argument("--headless")
            
            # Random user agent
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ]
            options.add_argument(f"--user-agent={random.choice(user_agents)}")
            
            self.driver = uc.Chrome(options=options)
            
            # Execute script to hide automation
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.logger.info("Browser initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize browser: {e}")
            return False
    
    async def auto_apply_job(self, job_input: JobApplicationInput) -> Dict[str, Any]:
        """Main method to auto-apply to a job using adaptive intelligence"""
        try:
            self.logger.info(f"Starting adaptive job application for: {job_input.job_title}")
            
            # Initialize browser
            if not await self.initialize_browser():
                return {"success": False, "error": "Browser initialization failed"}
            
            # Load initial page
            await self._navigate_to_page(job_input.website_url)
            
            # Load and apply cookies if available
            await self._load_cookies(job_input.website_url)
            
            # Start adaptive navigation process
            application_result = await self._adaptive_navigation_loop(job_input)
            
            return application_result
            
        except Exception as e:
            self.logger.error(f"Error in auto_apply_job: {e}")
            return {"success": False, "error": str(e)}
        finally:
            await self._cleanup_browser()
    
    async def _adaptive_navigation_loop(self, job_input: JobApplicationInput) -> Dict[str, Any]:
        """Main adaptive navigation loop with LLM guidance"""
        max_iterations = 20
        iteration = 0
        
        while iteration < max_iterations:
            try:
                iteration += 1
                self.logger.info(f"Adaptive navigation iteration {iteration}/{max_iterations}")
                
                # Get current page HTML
                current_html = await self._get_current_page_html()
                
                # Analyze page with LLM
                analysis = await self._analyze_page_with_llm(current_html, job_input, iteration)
                
                self.logger.info(f"Page analysis: {analysis.page_type} (confidence: {analysis.confidence_score})")
                
                # Handle different page types
                if analysis.page_type == "success":
                    return {"success": True, "message": "Job application completed successfully"}
                elif analysis.page_type == "error":
                    return await self._handle_error_page(analysis, job_input)
                elif analysis.page_type == "bot_detection":
                    await self._handle_bot_detection(analysis)
                elif analysis.page_type == "captcha":
                    await self._handle_captcha(analysis)
                elif analysis.page_type == "login_required":
                    await self._handle_login_requirement(analysis, job_input)
                
                # Execute suggested actions
                action_success = await self._execute_navigation_steps(analysis.suggested_actions, job_input)
                
                if not action_success:
                    # Try alternative strategies
                    alternative_result = await self._try_alternative_strategies(current_html, job_input)
                    if not alternative_result:
                        continue
                
                # Random delay to appear human-like
                await self._human_like_delay()
                
                # Save cookies periodically
                await self._save_cookies(job_input.website_url)
                
            except Exception as e:
                self.logger.error(f"Error in navigation iteration {iteration}: {e}")
                continue
        
        return {"success": False, "error": "Maximum iterations reached without success"}
    
    async def _analyze_page_with_llm(self, html: str, job_input: JobApplicationInput, iteration: int) -> WebsiteAnalysis:
        """Analyze current page using LLM intelligence"""
        try:
            # Clean HTML for LLM analysis
            soup = BeautifulSoup(html, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get relevant elements
            relevant_html = self._extract_relevant_elements(soup)
            
            # Create analysis prompt
            prompt = self._create_analysis_prompt(relevant_html, job_input, iteration)
            
            # Get LLM analysis
            llm_response = await self.llm._call_llm(prompt)
            
            # Parse LLM response
            analysis = self._parse_llm_analysis(llm_response)
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error in LLM analysis: {e}")
            return self._create_fallback_analysis(html)
    
    def _create_analysis_prompt(self, html: str, job_input: JobApplicationInput, iteration: int) -> str:
        """Create comprehensive analysis prompt for LLM"""
        return f"""
You are an expert web automation agent analyzing a job application website. 

CONTEXT:
- Job Title: {job_input.job_title}
- Current Iteration: {iteration}
- Session ID: {self.current_session_id}
- Navigation History: {self.navigation_history[-3:] if self.navigation_history else "None"}

CURRENT PAGE HTML (relevant elements):
{html[:4000]}  # Limit HTML size for LLM

CANDIDATE RESUME DATA:
- Name: {job_input.parsed_resume.get('name', 'N/A')}
- Email: {job_input.parsed_resume.get('email', 'N/A')}
- Phone: {job_input.parsed_resume.get('phone', 'N/A')}
- Skills: {job_input.parsed_resume.get('skills', [])}
- Experience: {job_input.parsed_resume.get('experience', 'N/A')}

ANALYZE THE PAGE AND PROVIDE:
1. Page Type: job_listing, application_form, login, success, error, bot_detection, captcha, or unknown
2. Detected Elements: List of important form fields, buttons, links with their selectors
3. Suggested Actions: Step-by-step navigation actions to apply for the job
4. Obstacles: Any detected obstacles (bot detection, captcha, login requirements)
5. Confidence Score: 0-100 confidence in the analysis

RESPONSE FORMAT (JSON):
{{
    "page_type": "application_form",
    "detected_elements": [
        {{"type": "input", "selector": "#email", "field_type": "email", "required": true}},
        {{"type": "button", "selector": ".apply-btn", "action": "submit_application"}}
    ],
    "suggested_actions": [
        {{"action_type": "fill", "selector": "#email", "value": "email", "description": "Fill email field"}},
        {{"action_type": "click", "selector": ".apply-btn", "description": "Submit application"}}
    ],
    "obstacles": [],
    "confidence_score": 85
}}

Focus on finding:
- Apply buttons or links
- Job application forms
- File upload fields for resume
- Required form fields
- Navigation elements to reach application

Be adaptive and creative in finding ways to apply for the job.
"""
    
    def _extract_relevant_elements(self, soup: BeautifulSoup) -> str:
        """Extract relevant elements for LLM analysis"""
        relevant_tags = []
        
        # Find forms
        forms = soup.find_all('form')
        for form in forms:
            relevant_tags.append(str(form)[:1000])  # Limit size
        
        # Find buttons with job-related text
        buttons = soup.find_all(['button', 'a'], string=lambda text: text and any(
            keyword in text.lower() for keyword in ['apply', 'submit', 'job', 'application', 'continue']
        ))
        for button in buttons:
            relevant_tags.append(str(button))
        
        # Find input fields
        inputs = soup.find_all(['input', 'textarea', 'select'])
        for input_elem in inputs:
            relevant_tags.append(str(input_elem))
        
        # Find elements with job-related classes or IDs
        job_elements = soup.find_all(attrs={'class': lambda x: x and any(
            keyword in ' '.join(x).lower() for keyword in ['job', 'apply', 'application', 'form']
        )})
        for elem in job_elements:
            relevant_tags.append(str(elem)[:500])
        
        return '\n'.join(relevant_tags[:50])  # Limit number of elements
    
    def _parse_llm_analysis(self, llm_response: str) -> WebsiteAnalysis:
        """Parse LLM response into WebsiteAnalysis object"""
        try:
            # Extract JSON from response
            start_idx = llm_response.find('{')
            end_idx = llm_response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = llm_response[start_idx:end_idx]
                data = json.loads(json_str)
                
                # Convert to NavigationStep objects
                suggested_actions = []
                for action in data.get('suggested_actions', []):
                    suggested_actions.append(NavigationStep(
                        action_type=action.get('action_type', 'click'),
                        selector=action.get('selector', ''),
                        value=action.get('value'),
                        description=action.get('description', ''),
                        confidence=action.get('confidence', 70.0)
                    ))
                
                return WebsiteAnalysis(
                    page_type=data.get('page_type', 'unknown'),
                    detected_elements=data.get('detected_elements', []),
                    suggested_actions=suggested_actions,
                    obstacles=data.get('obstacles', []),
                    confidence_score=data.get('confidence_score', 50.0)
                )
        except Exception as e:
            self.logger.error(f"Error parsing LLM analysis: {e}")
        
        return self._create_fallback_analysis("")
    
    async def _execute_navigation_steps(self, steps: List[NavigationStep], job_input: JobApplicationInput) -> bool:
        """Execute the suggested navigation steps"""
        try:
            for step in steps:
                self.logger.info(f"Executing step: {step.description}")
                
                success = await self._execute_single_step(step, job_input)
                if not success:
                    self.logger.warning(f"Step failed: {step.description}")
                    return False
                
                # Record successful step
                self.navigation_history.append({
                    'step': step.description,
                    'action': step.action_type,
                    'selector': step.selector,
                    'timestamp': datetime.now().isoformat()
                })
                
                # Small delay between steps
                await asyncio.sleep(random.uniform(0.5, 1.5))
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error executing navigation steps: {e}")
            return False
    
    async def _execute_single_step(self, step: NavigationStep, job_input: JobApplicationInput) -> bool:
        """Execute a single navigation step"""
        try:
            if step.action_type == "click":
                return await self._click_element(step.selector)
            elif step.action_type == "fill":
                value = self._resolve_fill_value(step.value, job_input)
                return await self._fill_element(step.selector, value)
            elif step.action_type == "select":
                return await self._select_option(step.selector, step.value)
            elif step.action_type == "upload":
                return await self._upload_file(step.selector, job_input.parsed_resume)
            elif step.action_type == "wait":
                await asyncio.sleep(float(step.value or 2))
                return True
            elif step.action_type == "scroll":
                return await self._scroll_to_element(step.selector)
            else:
                self.logger.warning(f"Unknown action type: {step.action_type}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error executing step {step.action_type}: {e}")
            return False
    
    def _resolve_fill_value(self, field_name: str, job_input: JobApplicationInput) -> str:
        """Resolve the value to fill based on field name and resume data"""
        resume = job_input.parsed_resume
        
        field_mapping = {
            'email': resume.get('email', ''),
            'name': resume.get('name', ''),
            'first_name': resume.get('first_name', resume.get('name', '').split()[0] if resume.get('name') else ''),
            'last_name': resume.get('last_name', resume.get('name', '').split()[-1] if resume.get('name') else ''),
            'phone': resume.get('phone', ''),
            'address': resume.get('address', ''),
            'city': resume.get('city', ''),
            'state': resume.get('state', ''),
            'zip': resume.get('zip_code', ''),
            'linkedin': resume.get('linkedin', ''),
            'website': resume.get('website', ''),
            'cover_letter': resume.get('cover_letter', ''),
            'experience': resume.get('experience_years', ''),
            'salary': resume.get('expected_salary', ''),
        }
        
        return field_mapping.get(field_name, field_name)
    
    async def _click_element(self, selector: str) -> bool:
        """Click an element with multiple selector strategies"""
        try:
            # Try different selector strategies
            strategies = [
                lambda: self.driver.find_element(By.CSS_SELECTOR, selector),
                lambda: self.driver.find_element(By.XPATH, selector),
                lambda: self.driver.find_element(By.ID, selector.replace('#', '')),
                lambda: self.driver.find_element(By.CLASS_NAME, selector.replace('.', '')),
            ]
            
            element = None
            for strategy in strategies:
                try:
                    element = strategy()
                    break
                except:
                    continue
            
            if not element:
                return False
            
            # Scroll to element
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            await asyncio.sleep(0.5)
            
            # Try different click methods
            try:
                element.click()
            except:
                # Try JavaScript click
                self.driver.execute_script("arguments[0].click();", element)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error clicking element {selector}: {e}")
            return False
    
    async def _fill_element(self, selector: str, value: str) -> bool:
        """Fill an input element"""
        try:
            element = self.driver.find_element(By.CSS_SELECTOR, selector)
            
            # Clear existing content
            element.clear()
            
            # Type with human-like delay
            for char in value:
                element.send_keys(char)
                await asyncio.sleep(random.uniform(0.05, 0.15))
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error filling element {selector}: {e}")
            return False
    
    async def _handle_bot_detection(self, analysis: WebsiteAnalysis) -> bool:
        """Handle bot detection scenarios"""
        self.logger.warning("Bot detection encountered, implementing countermeasures")
        
        # Strategy 1: Change user agent
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        
        self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": random.choice(user_agents)
        })
        
        # Strategy 2: Random mouse movements
        actions = ActionChains(self.driver)
        for _ in range(5):
            x = random.randint(100, 800)
            y = random.randint(100, 600)
            actions.move_by_offset(x, y)
        actions.perform()
        
        # Strategy 3: Longer delays
        await asyncio.sleep(random.uniform(3, 7))
        
        return True
    
    async def _handle_captcha(self, analysis: WebsiteAnalysis) -> bool:
        """Handle CAPTCHA scenarios"""
        self.logger.warning("CAPTCHA detected - manual intervention may be required")
        
        # For now, wait and hope it resolves or implement CAPTCHA solving service
        await asyncio.sleep(30)
        
        return True
    
    async def _get_current_page_html(self) -> str:
        """Get current page HTML"""
        try:
            return self.driver.page_source
        except Exception as e:
            self.logger.error(f"Error getting page HTML: {e}")
            return ""
    
    async def _navigate_to_page(self, url: str):
        """Navigate to a specific page"""
        try:
            self.driver.get(url)
            await asyncio.sleep(random.uniform(2, 4))
        except Exception as e:
            self.logger.error(f"Error navigating to {url}: {e}")
            raise
    
    async def _load_cookies(self, domain: str):
        """Load cookies for the domain"""
        try:
            cookies_file = f"cookies/{self._get_domain_key(domain)}.pkl"
            if os.path.exists(cookies_file):
                with open(cookies_file, 'rb') as f:
                    cookies = pickle.load(f)
                    for cookie in cookies:
                        self.driver.add_cookie(cookie)
                self.logger.info(f"Loaded cookies for {domain}")
        except Exception as e:
            self.logger.error(f"Error loading cookies: {e}")
    
    async def _save_cookies(self, domain: str):
        """Save cookies for the domain"""
        try:
            os.makedirs("cookies", exist_ok=True)
            cookies_file = f"cookies/{self._get_domain_key(domain)}.pkl"
            with open(cookies_file, 'wb') as f:
                pickle.dump(self.driver.get_cookies(), f)
        except Exception as e:
            self.logger.error(f"Error saving cookies: {e}")
    
    def _get_domain_key(self, url: str) -> str:
        """Get domain key for cookie storage"""
        from urllib.parse import urlparse
        return urlparse(url).netloc.replace('.', '_')
    
    async def _human_like_delay(self):
        """Add human-like delay"""
        delay = random.uniform(1, 3)
        await asyncio.sleep(delay)
    
    async def _cleanup_browser(self):
        """Clean up browser resources"""
        try:
            if self.driver:
                self.driver.quit()
        except Exception as e:
            self.logger.error(f"Error cleaning up browser: {e}")
    
    def _create_fallback_analysis(self, html: str) -> WebsiteAnalysis:
        """Create fallback analysis when LLM fails"""
        return WebsiteAnalysis(
            page_type="unknown",
            detected_elements=[],
            suggested_actions=[],
            obstacles=["llm_analysis_failed"],
            confidence_score=10.0
        )
    
    async def _try_alternative_strategies(self, html: str, job_input: JobApplicationInput) -> bool:
        """Try alternative strategies when main approach fails"""
        # Implement fallback strategies
        self.logger.info("Trying alternative navigation strategies")
        
        # Strategy 1: Look for common apply button patterns
        apply_selectors = [
            "button[contains(text(), 'Apply')]",
            "a[contains(text(), 'Apply')]",
            ".apply-button",
            "#apply-btn",
            "[data-testid*='apply']",
            ".job-apply-button"
        ]
        
        for selector in apply_selectors:
            if await self._click_element(selector):
                return True
        
        return False
    
    async def _handle_error_page(self, analysis: WebsiteAnalysis, job_input: JobApplicationInput) -> Dict[str, Any]:
        """Handle error pages"""
        return {"success": False, "error": "Encountered error page", "analysis": analysis.obstacles}
    
    async def _handle_login_requirement(self, analysis: WebsiteAnalysis, job_input: JobApplicationInput) -> bool:
        """Handle login requirements"""
        self.logger.warning("Login required - attempting automatic login")
        # Implement login logic based on stored credentials
        return False
    
    async def _select_option(self, selector: str, value: str) -> bool:
        """Select option from dropdown"""
        try:
            select_element = Select(self.driver.find_element(By.CSS_SELECTOR, selector))
            select_element.select_by_visible_text(value)
            return True
        except Exception as e:
            self.logger.error(f"Error selecting option: {e}")
            return False
    
    async def _upload_file(self, selector: str, resume_data: Dict) -> bool:
        """Upload resume file"""
        try:
            file_input = self.driver.find_element(By.CSS_SELECTOR, selector)
            resume_path = resume_data.get('file_path', 'resume.pdf')
            if os.path.exists(resume_path):
                file_input.send_keys(os.path.abspath(resume_path))
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error uploading file: {e}")
            return False
    
    async def _scroll_to_element(self, selector: str) -> bool:
        """Scroll to element"""
        try:
            element = self.driver.find_element(By.CSS_SELECTOR, selector)
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            return True
        except Exception as e:
            self.logger.error(f"Error scrolling to element: {e}")
            return False

async def main():
    """Main function for testing"""
    # Initialize LLM
    llm_config = load_llm_config()
    llm = LLMIntegration(llm_config)
    
    # Create agent
    agent = AdaptiveWebAgent(llm)
    
    # Test job input
    job_input = JobApplicationInput(
        job_title="Software Engineer",
        parsed_resume={
            "name": "John Doe",
            "email": "john.doe@example.com",
            "phone": "+1-555-123-4567",
            "skills": ["Python", "JavaScript", "React"],
            "experience": "5 years of software development"
        },
        target_html="",
        website_url="https://example-job-site.com/apply"
    )
    
    # Run application
    result = await agent.auto_apply_job(job_input)
    print(f"Application result: {result}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
