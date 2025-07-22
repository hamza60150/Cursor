#!/usr/bin/env python3
"""
FIXED Auto Apply Agent - Improved Element Interaction
Fixes "element not interactable" issues with better wait conditions and interaction strategies.
"""

import os
import json
import time
import random
import logging
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import pickle

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException, StaleElementReferenceException
import undetected_chromedriver as uc
from bs4 import BeautifulSoup
import openai

@dataclass
class JobApplication:
    """Single job application data"""
    job_url: str
    job_title: str
    company: str
    resume_data: Dict[str, Any]

class AutoApplyAgent:
    """FIXED Auto-apply functionality with improved element interaction"""
    
    def __init__(self, openai_api_key: str, headless: bool = False):
        self.openai_api_key = openai_api_key
        openai.api_key = openai_api_key
        self.headless = headless
        self.driver = None
        self.wait = None
        self.logger = self._setup_logging()
        
        # Navigation history for learning
        self.navigation_history = []
        self.successful_patterns = {}
        self.failed_patterns = {}
        
        # Retry settings
        self.max_retries = 3
        self.max_navigation_attempts = 15
        
    def _setup_logging(self):
        """Setup logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('auto_apply_fixed.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    
    def _init_browser(self):
        """Initialize stealth browser with better settings"""
        try:
            options = uc.ChromeOptions()
            
            # Enhanced anti-detection settings
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-web-security")
            options.add_argument("--disable-features=VizDisplayCompositor")
            options.add_argument("--start-maximized")
            
            if self.headless:
                options.add_argument("--headless")
            
            # Random user agent
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            ]
            options.add_argument(f"--user-agent={random.choice(user_agents)}")
            
            self.driver = uc.Chrome(options=options)
            self.wait = WebDriverWait(self.driver, 10)
            
            # Enhanced stealth
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": random.choice(user_agents)
            })
            
            self.logger.info("Browser initialized successfully with enhanced settings")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize browser: {e}")
            return False
    
    def apply_to_jobs(self, jobs_file: str, resume_file: str) -> Dict[str, Any]:
        """Main method - apply to all jobs in the JSON file"""
        try:
            # Load job applications
            with open(jobs_file, 'r') as f:
                jobs_data = json.load(f)
            
            # Load parsed resume
            with open(resume_file, 'r') as f:
                resume_data = json.load(f)
            
            self.logger.info(f"Loaded {len(jobs_data)} jobs and resume data")
            
            # Initialize browser
            if not self._init_browser():
                return {"error": "Failed to initialize browser"}
            
            results = {
                "total_jobs": len(jobs_data),
                "successful_applications": 0,
                "failed_applications": 0,
                "results": []
            }
            
            # Process each job
            for i, job_data in enumerate(jobs_data):
                self.logger.info(f"Processing job {i+1}/{len(jobs_data)}: {job_data.get('job_title', 'Unknown')}")
                
                job_app = JobApplication(
                    job_url=job_data.get('job_url', ''),
                    job_title=job_data.get('job_title', 'Unknown'),
                    company=job_data.get('company', 'Unknown'),
                    resume_data=resume_data
                )
                
                # Apply to single job with retries
                job_result = self._apply_to_single_job_with_retries(job_app)
                
                if job_result['success']:
                    results['successful_applications'] += 1
                else:
                    results['failed_applications'] += 1
                
                results['results'].append(job_result)
                
                # Random delay between jobs
                delay = random.uniform(5, 15)
                self.logger.info(f"Waiting {delay:.1f} seconds before next job...")
                time.sleep(delay)
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in apply_to_jobs: {e}")
            return {"error": str(e)}
        finally:
            self._cleanup()
    
    def _apply_to_single_job_with_retries(self, job_app: JobApplication) -> Dict[str, Any]:
        """Apply to single job with retry logic"""
        for attempt in range(self.max_retries):
            try:
                self.logger.info(f"Attempt {attempt + 1}/{self.max_retries} for {job_app.job_title}")
                
                result = self._apply_to_single_job(job_app)
                
                if result['success']:
                    self._save_successful_pattern(job_app.job_url, result.get('navigation_pattern', []))
                    return result
                else:
                    self._save_failed_pattern(job_app.job_url, result.get('error', ''))
                    
            except Exception as e:
                self.logger.error(f"Attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retries - 1:
                    self.logger.info("Retrying with fresh browser...")
                    self._restart_browser()
                    time.sleep(random.uniform(3, 8))
        
        return {
            "job_title": job_app.job_title,
            "job_url": job_app.job_url,
            "success": False,
            "error": "Max retries exceeded",
            "attempts": self.max_retries
        }
    
    def _apply_to_single_job(self, job_app: JobApplication) -> Dict[str, Any]:
        """Core logic to apply to a single job"""
        try:
            # Navigate to job URL
            self.logger.info(f"Navigating to: {job_app.job_url}")
            self.driver.get(job_app.job_url)
            
            # Wait for page to load
            self._wait_for_page_load()
            
            # Load cookies if available
            self._load_cookies(job_app.job_url)
            
            navigation_pattern = []
            
            # Main navigation loop with OpenAI guidance
            for iteration in range(self.max_navigation_attempts):
                self.logger.info(f"Navigation iteration {iteration + 1}/{self.max_navigation_attempts}")
                
                # Wait for page to be ready
                self._wait_for_page_ready()
                
                # Get current page HTML
                current_html = self._get_clean_html()
                
                # Ask OpenAI what to do next
                ai_response = self._get_openai_navigation_guidance(
                    current_html, job_app, iteration, navigation_pattern
                )
                
                if not ai_response:
                    continue
                
                # Execute AI's suggested action
                action_result = self._execute_ai_action_improved(ai_response, job_app)
                navigation_pattern.append(action_result)
                
                # Check if we've successfully applied
                if action_result.get('action_type') == 'success':
                    self._save_cookies(job_app.job_url)
                    return {
                        "job_title": job_app.job_title,
                        "job_url": job_app.job_url,
                        "success": True,
                        "message": "Application submitted successfully",
                        "navigation_steps": len(navigation_pattern),
                        "navigation_pattern": navigation_pattern
                    }
                
                # Check for obstacles and handle them
                if action_result.get('obstacle'):
                    obstacle_handled = self._handle_obstacle(action_result['obstacle'], job_app)
                    if not obstacle_handled:
                        break
                
                # Random delay between actions
                time.sleep(random.uniform(2, 5))
            
            return {
                "job_title": job_app.job_title,
                "job_url": job_app.job_url,
                "success": False,
                "error": "Could not complete application after maximum attempts",
                "navigation_steps": len(navigation_pattern),
                "navigation_pattern": navigation_pattern
            }
            
        except Exception as e:
            self.logger.error(f"Error applying to {job_app.job_title}: {e}")
            return {
                "job_title": job_app.job_title,
                "job_url": job_app.job_url,
                "success": False,
                "error": str(e)
            }
    
    def _wait_for_page_load(self):
        """Wait for page to fully load"""
        try:
            # Wait for document ready state
            self.wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
            
            # Additional wait for dynamic content
            time.sleep(random.uniform(2, 4))
            
            # Wait for body to be present
            self.wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
        except TimeoutException:
            self.logger.warning("Page load timeout, continuing anyway")
    
    def _wait_for_page_ready(self):
        """Wait for page to be ready for interaction"""
        try:
            # Wait for jQuery if present
            try:
                self.wait.until(lambda driver: driver.execute_script("return typeof jQuery === 'undefined' || jQuery.active === 0"))
            except:
                pass
            
            # Wait for any loading indicators to disappear
            try:
                self.wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR, ".loading, .spinner, [data-loading]")))
            except:
                pass
            
            # Small random delay
            time.sleep(random.uniform(1, 2))
            
        except Exception as e:
            self.logger.debug(f"Page ready check failed: {e}")
    
    def _get_openai_navigation_guidance(self, html: str, job_app: JobApplication, 
                                      iteration: int, navigation_history: List) -> Dict:
        """Get navigation guidance from OpenAI"""
        try:
            # Create comprehensive prompt
            prompt = self._create_navigation_prompt(html, job_app, iteration, navigation_history)
            
            # Call OpenAI
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system", 
                        "content": "You are an expert web automation agent. Analyze HTML and provide specific actions to apply for jobs. Focus on finding APPLY buttons and application forms. Be very specific with selectors."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            # Parse OpenAI response
            ai_text = response.choices[0].message.content
            return self._parse_openai_response(ai_text)
            
        except Exception as e:
            self.logger.error(f"OpenAI API error: {e}")
            return None
    
    def _create_navigation_prompt(self, html: str, job_app: JobApplication, 
                                iteration: int, navigation_history: List) -> str:
        """Create comprehensive prompt for OpenAI"""
        
        # Clean and truncate HTML
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove scripts and styles
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Focus on relevant elements
        relevant_elements = []
        
        # Find buttons with apply-related text
        apply_buttons = soup.find_all(['button', 'a'], string=lambda text: text and any(
            keyword in text.lower() for keyword in ['apply', 'submit', 'continue', 'next', 'job']
        ))[:5]
        for btn in apply_buttons:
            relevant_elements.append(f"APPLY BUTTON: {str(btn)}")
        
        # Find forms
        forms = soup.find_all('form')[:2]
        for form in forms:
            relevant_elements.append(f"FORM: {str(form)[:800]}")
        
        # Find input fields
        inputs = soup.find_all(['input', 'textarea', 'select'])[:10]
        for inp in inputs:
            relevant_elements.append(f"INPUT: {str(inp)}")
        
        clean_html = '\n'.join(relevant_elements)[:3500]  # Limit size
        
        prompt = f"""
URGENT: I need to apply for this job automatically. Analyze the HTML and give me ONE specific action.

JOB: {job_app.job_title} at {job_app.company}
URL: {job_app.job_url}

CANDIDATE DATA:
- Name: {job_app.resume_data.get('name', 'N/A')}
- Email: {job_app.resume_data.get('email', 'N/A')}
- Phone: {job_app.resume_data.get('phone', 'N/A')}

CURRENT PAGE ELEMENTS:
{clean_html}

CONTEXT:
- Iteration: {iteration + 1}
- Previous actions: {[h.get('description', '') for h in navigation_history[-3:]] if navigation_history else 'None'}

TASK: Find the APPLY button or application form and tell me exactly what to do.

LOOK FOR:
1. "Apply" or "Apply Now" buttons
2. "Easy Apply" buttons (LinkedIn)
3. Application forms with fields to fill
4. "Submit Application" buttons
5. Success/confirmation messages

PROVIDE RESPONSE IN THIS EXACT JSON FORMAT:
{{
    "action_type": "click|fill|upload|submit|success",
    "selector": "exact CSS selector or button text",
    "value": "value to fill if filling field",
    "description": "what you're doing",
    "confidence": 85
}}

BE VERY SPECIFIC WITH SELECTORS. Use:
- CSS selectors like "button.apply-btn" or "#apply-button"
- Exact button text if no good selector
- Class names or IDs when available

RESPOND WITH ONLY THE JSON, NO OTHER TEXT.
"""
        
        return prompt
    
    def _parse_openai_response(self, response_text: str) -> Dict:
        """Parse OpenAI response into actionable data"""
        try:
            # Extract JSON from response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != 0:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error parsing OpenAI response: {e}")
            return None
    
    def _execute_ai_action_improved(self, ai_response: Dict, job_app: JobApplication) -> Dict:
        """IMPROVED: Execute the action suggested by AI with better error handling"""
        try:
            action_type = ai_response.get('action_type', '')
            selector = ai_response.get('selector', '')
            value = ai_response.get('value', '')
            description = ai_response.get('description', '')
            
            self.logger.info(f"Executing: {action_type} - {description}")
            
            result = {
                "action_type": action_type,
                "selector": selector,
                "description": description,
                "success": False,
                "obstacle": None
            }
            
            if action_type == "click":
                result["success"] = self._click_element_improved(selector)
                
            elif action_type == "fill":
                # Map the value to actual resume data
                actual_value = self._map_form_value(value, job_app.resume_data)
                result["success"] = self._fill_element_improved(selector, actual_value)
                
            elif action_type == "upload":
                result["success"] = self._upload_resume_improved(selector, job_app.resume_data)
                
            elif action_type == "submit":
                result["success"] = self._click_element_improved(selector)
                time.sleep(3)  # Wait for submission
                
            elif action_type == "success":
                result["success"] = True
                result["action_type"] = "success"
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error executing AI action: {e}")
            return {"action_type": "error", "success": False, "error": str(e)}
    
    def _click_element_improved(self, selector: str) -> bool:
        """IMPROVED: Click element with multiple strategies and better waits"""
        try:
            element = None
            
            # Strategy 1: Try exact selector
            try:
                element = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
            except:
                pass
            
            # Strategy 2: Try as button text
            if not element:
                try:
                    element = self.wait.until(EC.element_to_be_clickable((By.XPATH, f"//button[contains(text(), '{selector}')]")))
                except:
                    pass
            
            # Strategy 3: Try as link text
            if not element:
                try:
                    element = self.wait.until(EC.element_to_be_clickable((By.PARTIAL_LINK_TEXT, selector)))
                except:
                    pass
            
            # Strategy 4: Try different selector formats
            if not element:
                selectors_to_try = [
                    selector,
                    f"#{selector}",
                    f".{selector}",
                    f"[data-testid='{selector}']",
                    f"[aria-label*='{selector}']"
                ]
                
                for sel in selectors_to_try:
                    try:
                        element = self.driver.find_element(By.CSS_SELECTOR, sel)
                        if element.is_displayed() and element.is_enabled():
                            break
                    except:
                        continue
            
            if element:
                # Scroll to element
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
                time.sleep(1)
                
                # Wait for element to be clickable
                try:
                    self.wait.until(EC.element_to_be_clickable(element))
                except:
                    pass
                
                # Multiple click strategies
                try:
                    # Strategy 1: Normal click
                    element.click()
                    self.logger.info(f"Successfully clicked element: {selector}")
                    return True
                except:
                    try:
                        # Strategy 2: JavaScript click
                        self.driver.execute_script("arguments[0].click();", element)
                        self.logger.info(f"Successfully JS-clicked element: {selector}")
                        return True
                    except:
                        try:
                            # Strategy 3: Action chains click
                            ActionChains(self.driver).move_to_element(element).click().perform()
                            self.logger.info(f"Successfully action-clicked element: {selector}")
                            return True
                        except:
                            pass
            
            self.logger.warning(f"Could not click element: {selector}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error clicking element {selector}: {e}")
            return False
    
    def _fill_element_improved(self, selector: str, value: str) -> bool:
        """IMPROVED: Fill form element with better waits and error handling"""
        try:
            element = None
            
            # Try to find the element
            try:
                element = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
            except:
                # Try alternative selectors
                selectors_to_try = [
                    f"input[name='{selector}']",
                    f"#{selector}",
                    f".{selector}",
                    f"[placeholder*='{selector}']"
                ]
                
                for sel in selectors_to_try:
                    try:
                        element = self.driver.find_element(By.CSS_SELECTOR, sel)
                        break
                    except:
                        continue
            
            if element:
                # Scroll to element
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", element)
                time.sleep(0.5)
                
                # Wait for element to be interactable
                try:
                    self.wait.until(EC.element_to_be_clickable(element))
                except:
                    pass
                
                # Clear and fill
                try:
                    element.clear()
                    time.sleep(0.5)
                    
                    # Type with human-like delay
                    for char in str(value):
                        element.send_keys(char)
                        time.sleep(random.uniform(0.05, 0.15))
                    
                    self.logger.info(f"Successfully filled element: {selector} with: {value}")
                    return True
                    
                except ElementNotInteractableException:
                    # Try JavaScript if normal typing fails
                    try:
                        self.driver.execute_script("arguments[0].value = arguments[1];", element, value)
                        self.driver.execute_script("arguments[0].dispatchEvent(new Event('input', {bubbles: true}));", element)
                        self.logger.info(f"Successfully JS-filled element: {selector}")
                        return True
                    except:
                        pass
            
            self.logger.warning(f"Could not fill element: {selector}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error filling element {selector}: {e}")
            return False
    
    def _upload_resume_improved(self, selector: str, resume_data: Dict) -> bool:
        """IMPROVED: Upload resume file with better error handling"""
        try:
            # Create temporary resume file if needed
            resume_path = resume_data.get('resume_file_path', 'temp_resume.txt')
            
            if not os.path.exists(resume_path):
                # Create temporary resume file
                with open('temp_resume.txt', 'w') as f:
                    f.write(f"Name: {resume_data.get('name', '')}\n")
                    f.write(f"Email: {resume_data.get('email', '')}\n")
                    f.write(f"Phone: {resume_data.get('phone', '')}\n")
                    f.write(f"Skills: {', '.join(resume_data.get('skills', []))}\n")
                    f.write(f"Experience: {resume_data.get('experience', '')}\n")
                resume_path = 'temp_resume.txt'
            
            # Find file input
            file_input = None
            try:
                file_input = self.driver.find_element(By.CSS_SELECTOR, selector)
            except:
                # Try alternative selectors for file inputs
                selectors_to_try = [
                    "input[type='file']",
                    "[accept*='pdf']",
                    "[accept*='doc']"
                ]
                
                for sel in selectors_to_try:
                    try:
                        file_input = self.driver.find_element(By.CSS_SELECTOR, sel)
                        break
                    except:
                        continue
            
            if file_input:
                file_input.send_keys(os.path.abspath(resume_path))
                self.logger.info(f"Successfully uploaded resume: {resume_path}")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error uploading resume: {e}")
            return False
    
    def _map_form_value(self, field_name: str, resume_data: Dict) -> str:
        """Map form field to resume data"""
        field_mapping = {
            'name': resume_data.get('name', ''),
            'first_name': resume_data.get('first_name', resume_data.get('name', '').split()[0] if resume_data.get('name') else ''),
            'last_name': resume_data.get('last_name', resume_data.get('name', '').split()[-1] if resume_data.get('name') else ''),
            'email': resume_data.get('email', ''),
            'phone': resume_data.get('phone', ''),
            'address': resume_data.get('address', ''),
            'city': resume_data.get('city', ''),
            'state': resume_data.get('state', ''),
            'zip': resume_data.get('zip_code', ''),
            'linkedin': resume_data.get('linkedin', ''),
            'website': resume_data.get('website', ''),
            'cover_letter': resume_data.get('cover_letter', f"I am interested in the position and believe my skills would be a great fit."),
            'experience': resume_data.get('experience_years', ''),
            'salary': resume_data.get('expected_salary', ''),
        }
        
        return field_mapping.get(field_name.lower(), field_name)
    
    def _handle_obstacle(self, obstacle_type: str, job_app: JobApplication) -> bool:
        """Handle various obstacles"""
        self.logger.warning(f"Handling obstacle: {obstacle_type}")
        
        if obstacle_type == "login":
            return self._handle_login()
        elif obstacle_type == "captcha":
            self.logger.warning("CAPTCHA detected - waiting...")
            time.sleep(10)
            return True
        elif obstacle_type == "error":
            return self._handle_error_page()
        
        return False
    
    def _handle_login(self) -> bool:
        """Basic login handling"""
        self.logger.warning("Login required but no credentials provided")
        return False
    
    def _handle_error_page(self) -> bool:
        """Handle error pages"""
        try:
            self.driver.back()
            time.sleep(2)
            return True
        except:
            return False
    
    def _get_clean_html(self) -> str:
        """Get cleaned HTML of current page"""
        try:
            return self.driver.page_source
        except Exception as e:
            self.logger.error(f"Error getting HTML: {e}")
            return ""
    
    def _load_cookies(self, url: str):
        """Load cookies for domain"""
        try:
            domain = self._get_domain(url)
            cookies_file = f"cookies_{domain}.pkl"
            
            if os.path.exists(cookies_file):
                with open(cookies_file, 'rb') as f:
                    cookies = pickle.load(f)
                    for cookie in cookies:
                        try:
                            self.driver.add_cookie(cookie)
                        except:
                            pass
                self.logger.info(f"Loaded cookies for {domain}")
        except Exception as e:
            self.logger.error(f"Error loading cookies: {e}")
    
    def _save_cookies(self, url: str):
        """Save cookies for domain"""
        try:
            domain = self._get_domain(url)
            cookies_file = f"cookies_{domain}.pkl"
            
            with open(cookies_file, 'wb') as f:
                pickle.dump(self.driver.get_cookies(), f)
                
        except Exception as e:
            self.logger.error(f"Error saving cookies: {e}")
    
    def _get_domain(self, url: str) -> str:
        """Extract domain from URL"""
        from urllib.parse import urlparse
        return urlparse(url).netloc.replace('.', '_')
    
    def _save_successful_pattern(self, url: str, pattern: List):
        """Save successful navigation pattern"""
        domain = self._get_domain(url)
        if domain not in self.successful_patterns:
            self.successful_patterns[domain] = []
        self.successful_patterns[domain].append(pattern)
    
    def _save_failed_pattern(self, url: str, error: str):
        """Save failed pattern to avoid"""
        domain = self._get_domain(url)
        if domain not in self.failed_patterns:
            self.failed_patterns[domain] = []
        self.failed_patterns[domain].append(error)
    
    def _restart_browser(self):
        """Restart browser for fresh session"""
        try:
            if self.driver:
                self.driver.quit()
            time.sleep(2)
            self._init_browser()
        except Exception as e:
            self.logger.error(f"Error restarting browser: {e}")
    
    def _cleanup(self):
        """Cleanup resources"""
        try:
            if self.driver:
                self.driver.quit()
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

def main():
    """Main function for testing"""
    import argparse
    
    parser = argparse.ArgumentParser(description='FIXED Auto Apply Agent')
    parser.add_argument('--jobs-file', required=True, help='JSON file with job applications')
    parser.add_argument('--resume-file', required=True, help='JSON file with parsed resume')
    parser.add_argument('--openai-key', required=True, help='OpenAI API key')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    
    args = parser.parse_args()
    
    # Create agent
    agent = AutoApplyAgent(
        openai_api_key=args.openai_key,
        headless=args.headless
    )
    
    # Run applications
    results = agent.apply_to_jobs(args.jobs_file, args.resume_file)
    
    # Save results
    with open(f"application_results_fixed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"Completed: {results.get('successful_applications', 0)} successful, {results.get('failed_applications', 0)} failed")

if __name__ == "__main__":
    main()
