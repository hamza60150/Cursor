#!/usr/bin/env python3
"""
LinkedIn Job Fetcher Module
Fetches relevant jobs based on user description and saves them to applicablejobs.csv
"""

import os
import csv
import re
import time
from datetime import datetime
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.select import Select
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, NoSuchWindowException, ElementNotInteractableException, WebDriverException

# Import configuration and modules
from config.personals import *
from config.questions import *
from config.search import *
from config.settings import *
from config.secrets import username, password, use_AI, ai_provider

from modules.open_chrome import *
from modules.helpers import *
from modules.clickers_and_finders import *
from modules.validator import validate_config
from modules.ai.openaiConnections import ai_create_openai_client, ai_extract_skills, ai_answer_question, ai_close_openai_client
from modules.ai.deepseekConnections import deepseek_create_client, deepseek_extract_skills, deepseek_answer_question
from modules.ai.geminiConnections import gemini_create_client, gemini_extract_skills, gemini_answer_question

@dataclass
class JobInfo:
    """Data class to store job information"""
    job_id: str
    title: str
    company: str
    work_location: str
    work_style: str
    job_link: str
    description: str
    experience_required: int
    date_posted: str
    easy_apply_available: bool

class JobFetcher:
    """Class to handle job fetching functionality"""
    
    def __init__(self):
        self.applied_jobs = set()
        self.rejected_jobs = set()
        self.blacklisted_companies = set()
        self.fetched_jobs = []
        self.driver = None
        self.wait = None
        self.actions = None
        self.aiClient = None
        
    def initialize_driver(self):
        """Initialize the web driver and related objects"""
        self.driver = setup_driver(headless=False)
        self.wait = WebDriverWait(self.driver, 10)
        self.actions = get_actions()
        
    def initialize_ai_client(self):
        """Initialize AI client if enabled"""
        if use_AI:
            if ai_provider == "openai":
                self.aiClient = ai_create_openai_client()
            elif ai_provider == "deepseek":
                self.aiClient = deepseek_create_client()
            elif ai_provider == "gemini":
                self.aiClient = gemini_create_client()
            print_lg(f"AI client initialized: {ai_provider}")
        
    def is_logged_in_LN(self) -> bool:
        """Check if user is logged-in in LinkedIn"""
        if self.driver.current_url == "https://www.linkedin.com/feed/": 
            return True
        if try_linkText(self.driver, "Sign in"): 
            return False
        if try_xp(self.driver, '//button[@type="submit" and contains(text(), "Sign in")]'):  
            return False
        if try_linkText(self.driver, "Join now"): 
            return False
        print_lg("Didn't find Sign in link, so assuming user is logged in!")
        return True

    def login_LN(self) -> None:
        """Login to LinkedIn using credentials from secrets.py"""
        print_lg("Starting LinkedIn login process...")
        self.driver.get("https://www.linkedin.com/login")
        
        try:
            self.wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Forgot password?")))
            print_lg("Login page loaded successfully")
            
            # Enter username
            try:
                text_input_by_ID(self.driver, "username", username, 1)
                print_lg("Username entered successfully")
            except Exception as e:
                print_lg("Couldn't find username field.")
                print_lg(e)
                
            # Enter password
            try:
                text_input_by_ID(self.driver, "password", password, 1)
                print_lg("Password entered successfully")
            except Exception as e:
                print_lg("Couldn't find password field.")
                print_lg(e)
            
            # Click sign in button
            self.driver.find_element(By.XPATH, '//button[@type="submit" and contains(text(), "Sign in")]').click()
            print_lg("Sign in button clicked")
            
        except Exception as e1:
            print_lg(f"Error during login form filling: {e1}")
            try:
                profile_button = find_by_class(self.driver, "profile__details")
                profile_button.click()
                print_lg("Clicked profile button as fallback")
            except Exception as e2:
                print_lg("Couldn't Login!")
                print_lg(e2)

        # Wait for successful login
        try:
            self.wait.until(EC.url_to_be("https://www.linkedin.com/feed/"))
            print_lg("Login successful! Redirected to feed page.")
            return True
        except Exception as e:
            print_lg("Seems like login attempt failed! Possibly due to wrong credentials or already logged in!")
            print_lg("Trying manual login retry...")
            manual_login_retry(self.is_logged_in_LN, 2)
            return False

    def check_sign_in(self) -> bool:
        """Check if sign in was successful"""
        print_lg("Checking sign in status...")
        
        # Check if we're on the feed page
        if self.driver.current_url == "https://www.linkedin.com/feed/":
            print_lg("✅ Successfully signed in - on feed page")
            return True
            
        # Check for sign in elements
        if try_linkText(self.driver, "Sign in"):
            print_lg("❌ Not signed in - Sign in link found")
            return False
            
        if try_xp(self.driver, '//button[@type="submit" and contains(text(), "Sign in")]'):
            print_lg("❌ Not signed in - Sign in button found")
            return False
            
        if try_linkText(self.driver, "Join now"):
            print_lg("❌ Not signed in - Join now link found")
            return False
            
        print_lg("✅ Sign in check passed - assuming logged in")
        return True

    def navigate_to_jobs(self):
        """Navigate to LinkedIn Jobs page"""
        print_lg("Navigating to LinkedIn Jobs...")
        self.driver.get("https://www.linkedin.com/jobs/")
        buffer(2)
        print_lg("Successfully navigated to Jobs page")

    def set_search_location(self) -> None:
        """Set search location"""
        if search_location.strip():
            try:
                print_lg(f'Setting search location as: "{search_location.strip()}"')
                search_location_ele = try_xp(self.driver, ".//input[@aria-label='City, state, or zip code'and not(@disabled)]", False)
                if search_location_ele:
                    text_input(self.actions, search_location_ele, search_location, "Search Location")
                    print_lg("Search location set successfully")
                else:
                    print_lg("Search location field not found, trying alternative method")
                    try_xp(self.driver, ".//label[@class='jobs-search-box__input-icon jobs-search-box__keywords-label']")
                    self.actions.send_keys(Keys.TAB, Keys.TAB).perform()
                    self.actions.key_down(Keys.CONTROL).send_keys("a").key_up(Keys.CONTROL).perform()
                    self.actions.send_keys(search_location.strip()).perform()
                    time.sleep(2)
                    self.actions.send_keys(Keys.ENTER).perform()
                    try_xp(self.driver, ".//button[@aria-label='Cancel']")
            except Exception as e:
                try_xp(self.driver, ".//button[@aria-label='Cancel']")
                print_lg("Failed to update search location, continuing with default location!", e)

    def apply_filters(self) -> None:
        """Apply job search filters"""
        print_lg("Applying job search filters...")
        self.set_search_location()

        try:
            recommended_wait = 1 if click_gap < 1 else 0

            # Click "All filters" button
            all_filters_button = self.wait.until(EC.presence_of_element_located((By.XPATH, '//button[normalize-space()="All filters"]')))
            all_filters_button.click()
            print_lg("Clicked 'All filters' button")
            buffer(recommended_wait)

            # Apply sort by filter
            if sort_by:
                wait_span_click(self.driver, sort_by)
                print_lg(f"Applied sort by: {sort_by}")
                
            # Apply date posted filter
            if date_posted:
                wait_span_click(self.driver, date_posted)
                print_lg(f"Applied date posted: {date_posted}")
            buffer(recommended_wait)

            # Apply experience level filter
            if experience_level:
                multi_sel_noWait(self.driver, experience_level) 
                print_lg(f"Applied experience level: {experience_level}")
                
            # Apply companies filter
            if companies:
                multi_sel_noWait(self.driver, companies, self.actions)
                print_lg(f"Applied companies filter: {companies}")
                
            if experience_level or companies: 
                buffer(recommended_wait)

            # Apply job type filter
            if job_type:
                multi_sel_noWait(self.driver, job_type)
                print_lg(f"Applied job type: {job_type}")
                
            # Apply on-site filter
            if on_site:
                multi_sel_noWait(self.driver, on_site)
                print_lg(f"Applied on-site: {on_site}")
                
            if job_type or on_site: 
                buffer(recommended_wait)

            # Turn on Easy Apply filter
            if easy_apply_only: 
                boolean_button_click(self.driver, self.actions, "Easy Apply")
                print_lg("Turned on Easy Apply filter")
            
            # Apply location filter
            if location:
                multi_sel_noWait(self.driver, location)
                print_lg(f"Applied location: {location}")
                
            # Apply industry filter
            if industry:
                multi_sel_noWait(self.driver, industry)
                print_lg(f"Applied industry: {industry}")
                
            if location or industry: 
                buffer(recommended_wait)

            # Apply job function filter
            if job_function:
                multi_sel_noWait(self.driver, job_function)
                print_lg(f"Applied job function: {job_function}")
                
            # Apply job titles filter
            if job_titles:
                multi_sel_noWait(self.driver, job_titles)
                print_lg(f"Applied job titles: {job_titles}")
                
            if job_function or job_titles: 
                buffer(recommended_wait)

            # Apply additional filters
            if under_10_applicants: 
                boolean_button_click(self.driver, self.actions, "Under 10 applicants")
                print_lg("Applied under 10 applicants filter")
                
            if in_your_network: 
                boolean_button_click(self.driver, self.actions, "In your network")
                print_lg("Applied in your network filter")
                
            if fair_chance_employer: 
                boolean_button_click(self.driver, self.actions, "Fair Chance Employer")
                print_lg("Applied fair chance employer filter")

            # Apply salary filter
            if salary:
                wait_span_click(self.driver, salary)
                print_lg(f"Applied salary: {salary}")
            buffer(recommended_wait)
            
            # Apply benefits filter
            if benefits:
                multi_sel_noWait(self.driver, benefits)
                print_lg(f"Applied benefits: {benefits}")
                
            # Apply commitments filter
            if commitments:
                multi_sel_noWait(self.driver, commitments)
                print_lg(f"Applied commitments: {commitments}")
                
            if benefits or commitments: 
                buffer(recommended_wait)

            # Click "Show results" button
            show_results_button: WebElement = self.driver.find_element(By.XPATH, '//button[contains(@aria-label, "Apply current filters to show")]')
            show_results_button.click()
            print_lg("Clicked 'Show results' button")

        except Exception as e:
            print_lg("Setting the preferences failed!")
            print_lg(e)

    def get_page_info(self) -> Tuple[Optional[WebElement], Optional[int]]:
        """Get pagination element and current page number"""
        try:
            pagination_element = try_find_by_classes(self.driver, ["jobs-search-pagination__pages", "artdeco-pagination", "artdeco-pagination__pages"])
            scroll_to_view(self.driver, pagination_element)
            current_page = int(pagination_element.find_element(By.XPATH, "//button[contains(@class, 'active')]").text)
            print_lg(f"Found pagination, current page: {current_page}")
        except Exception as e:
            print_lg("Failed to find Pagination element, hence couldn't scroll till end!")
            pagination_element = None
            current_page = None
            print_lg(e)
        return pagination_element, current_page

    def get_job_main_details(self, job: WebElement) -> Tuple[str, str, str, str, str, bool]:
        """Get job main details"""
        job_details_button = job.find_element(By.TAG_NAME, 'a')
        scroll_to_view(self.driver, job_details_button, True)
        job_id = job.get_dom_attribute('data-occludable-job-id')
        title = job_details_button.text
        title = title[:title.find("\n")]
        
        other_details = job.find_element(By.CLASS_NAME, 'artdeco-entity-lockup__subtitle').text
        index = other_details.find(' · ')
        company = other_details[:index]
        work_location = other_details[index+3:]
        work_style = work_location[work_location.rfind('(')+1:work_location.rfind(')')]
        work_location = work_location[:work_location.rfind('(')].strip()
        
        # Skip if previously rejected due to blacklist or already applied
        skip = False
        if company in self.blacklisted_companies:
            print_lg(f'Skipping "{title} | {company}" job (Blacklisted Company). Job ID: {job_id}!')
            skip = True
        elif job_id in self.rejected_jobs: 
            print_lg(f'Skipping previously rejected "{title} | {company}" job. Job ID: {job_id}!')
            skip = True
        try:
            if job.find_element(By.CLASS_NAME, "job-card-container__footer-job-state").text == "Applied":
                skip = True
                print_lg(f'Already applied to "{title} | {company}" job. Job ID: {job_id}!')
        except: 
            pass
        try: 
            if not skip: 
                job_details_button.click()
        except Exception as e:
            print_lg(f'Failed to click "{title} | {company}" job on details button. Job ID: {job_id}!') 
            discard_job()
            job_details_button.click()
        buffer(click_gap)
        return (job_id, title, company, work_location, work_style, skip)

    def check_blacklist(self, job_id: str, company: str) -> Tuple[Set[str], Set[str], WebElement]:
        """Check for blacklisted words in About Company"""
        jobs_top_card = try_find_by_classes(self.driver, ["job-details-jobs-unified-top-card__primary-description-container","job-details-jobs-unified-top-card__primary-description","jobs-unified-top-card__primary-description","jobs-details__main-content"])
        about_company_org = find_by_class(self.driver, "jobs-company__box")
        scroll_to_view(self.driver, about_company_org)
        about_company_org = about_company_org.text
        about_company = about_company_org.lower()
        skip_checking = False
        for word in about_company_good_words:
            if word.lower() in about_company:
                print_lg(f'Found the word "{word}". So, skipped checking for blacklist words.')
                skip_checking = True
                break
        if not skip_checking:
            for word in about_company_bad_words: 
                if word.lower() in about_company: 
                    self.rejected_jobs.add(job_id)
                    self.blacklisted_companies.add(company)
                    raise ValueError(f'\n"{about_company_org}"\n\nContains "{word}".')
        buffer(click_gap)
        scroll_to_view(self.driver, jobs_top_card)
        return self.rejected_jobs, self.blacklisted_companies, jobs_top_card

    def extract_years_of_experience(self, text: str) -> int:
        """Extract years of experience required from job description"""
        re_experience = re.compile(r'[(]?\s*(\d+)\s*[)]?\s*[-to]*\d*[+]*\s*year[s]?', re.IGNORECASE)
        matches = re.findall(re_experience, text)
        if len(matches) == 0: 
            print_lg(f'\n{text}\n\nCouldn\'t find experience requirement in About the Job!')
            return 0
        return max([int(match) for match in matches if int(match) <= 12])

    def get_job_description(self) -> Tuple[str, int, bool, Optional[str], Optional[str]]:
        """Extract job description and check if job should be skipped"""
        try:
            jobDescription = "Unknown"
            experience_required = "Unknown"
            found_masters = 0
            jobDescription = find_by_class(self.driver, "jobs-box__html-content").text
            jobDescriptionLow = jobDescription.lower()
            skip = False
            skipReason = None
            skipMessage = None
            
            for word in bad_words:
                if word.lower() in jobDescriptionLow:
                    skipMessage = f'\n{jobDescription}\n\nContains bad word "{word}". Skipping this job!\n'
                    skipReason = "Found a Bad Word in About Job"
                    skip = True
                    break
                    
            if not skip and security_clearance == False and ('polygraph' in jobDescriptionLow or 'clearance' in jobDescriptionLow or 'secret' in jobDescriptionLow):
                skipMessage = f'\n{jobDescription}\n\nFound "Clearance" or "Polygraph". Skipping this job!\n'
                skipReason = "Asking for Security clearance"
                skip = True
                
            if not skip:
                if did_masters and 'master' in jobDescriptionLow:
                    print_lg(f'Found the word "master" in \n{jobDescription}')
                    found_masters = 2
                experience_required = self.extract_years_of_experience(jobDescription)
                if current_experience > -1 and experience_required > current_experience + found_masters:
                    skipMessage = f'\n{jobDescription}\n\nExperience required {experience_required} > Current Experience {current_experience + found_masters}. Skipping this job!\n'
                    skipReason = "Required experience is high"
                    skip = True
        except Exception as e:
            if jobDescription == "Unknown":    
                print_lg("Unable to extract job description!")
            else:
                experience_required = "Error in extraction"
                print_lg("Unable to extract years of experience required!")
        finally:
            return jobDescription, experience_required, skip, skipReason, skipMessage

    def check_easy_apply_availability(self) -> bool:
        """Check if Easy Apply is available for the current job"""
        try:
            easy_apply_button = self.driver.find_element(By.XPATH, ".//button[contains(@class,'jobs-apply-button') and contains(@class, 'artdeco-button--3') and contains(@aria-label, 'Easy')]")
            return True
        except NoSuchElementException:
            return False

    def calculate_date_posted(self, time_posted_text: str) -> str:
        """Calculate the date when job was posted"""
        return calculate_date_posted(time_posted_text)

    def fetch_jobs_for_search_term(self, search_term: str, max_jobs: int = 50) -> List[JobInfo]:
        """Fetch jobs for a specific search term"""
        print_lg(f'\n>>>> Now searching for "{search_term}" <<<<\n\n')
        
        # Navigate to search URL
        search_url = f"https://www.linkedin.com/jobs/search/?keywords={search_term}"
        self.driver.get(search_url)
        print_lg(f"Navigated to search URL: {search_url}")

        # Apply filters
        self.apply_filters()
        print_lg("Filters applied successfully")

        fetched_jobs = []
        current_count = 0
        
        try:
            while current_count < max_jobs:
                # Wait until job listings are loaded
                self.wait.until(EC.presence_of_all_elements_located((By.XPATH, "//li[@data-occludable-job-id]")))
                print_lg("Job listings loaded")

                pagination_element, current_page = self.get_page_info()

                # Find all job listings in current page
                buffer(3)
                job_listings = self.driver.find_elements(By.XPATH, "//li[@data-occludable-job-id]")  
                print_lg(f"Found {len(job_listings)} job listings on current page")

                for job in job_listings:
                    if current_count >= max_jobs: 
                        break
                    print_lg("\n-@-\n")

                    job_id, title, company, work_location, work_style, skip = self.get_job_main_details(job)
                    
                    if skip: 
                        continue

                    job_link = "https://www.linkedin.com/jobs/view/"+job_id
                    date_listed = "Unknown"

                    try:
                        self.rejected_jobs, self.blacklisted_companies, jobs_top_card = self.check_blacklist(job_id, company)
                    except ValueError as e:
                        print_lg(e, 'Skipping this job!\n')
                        continue
                    except Exception as e:
                        print_lg("Failed to scroll to About Company!")

                    # Calculate date posted
                    try:
                        time_posted_text = jobs_top_card.find_element(By.XPATH, './/span[contains(normalize-space(), " ago")]').text
                        print("Time Posted: " + time_posted_text)
                        date_listed = self.calculate_date_posted(time_posted_text.strip())
                    except Exception as e:
                        print_lg("Failed to calculate the date posted!", e)

                    description, experience_required, skip, reason, message = self.get_job_description()
                    if skip:
                        print_lg(message)
                        self.rejected_jobs.add(job_id)
                        continue

                    # Check if Easy Apply is available
                    easy_apply_available = self.check_easy_apply_availability()
                    if easy_apply_available:
                        print_lg(f"✅ Easy Apply available for {title} | {company}")
                    else:
                        print_lg(f"❌ Easy Apply not available for {title} | {company}")

                    # Create JobInfo object
                    job_info = JobInfo(
                        job_id=job_id,
                        title=title,
                        company=company,
                        work_location=work_location,
                        work_style=work_style,
                        job_link=job_link,
                        description=description,
                        experience_required=experience_required if isinstance(experience_required, int) else 0,
                        date_posted=date_listed,
                        easy_apply_available=easy_apply_available
                    )
                    
                    fetched_jobs.append(job_info)
                    current_count += 1
                    print_lg(f'Fetched "{title} | {company}" job. Job ID: {job_id}')

                # Switch to next page
                if pagination_element == None:
                    print_lg("Couldn't find pagination element, probably at the end page of results!")
                    break
                try:
                    pagination_element.find_element(By.XPATH, f"//button[@aria-label='Page {current_page+1}']").click()
                    print_lg(f"\n>-> Now on Page {current_page+1} \n")
                except NoSuchElementException:
                    print_lg(f"\n>-> Didn't find Page {current_page+1}. Probably at the end page of results!\n")
                    break

        except Exception as e:
            print_lg("Failed to fetch job listings!")
            print_lg(e)

        return fetched_jobs

    def save_jobs_to_csv(self, jobs: List[JobInfo], filename: str = "applicablejobs.csv"):
        """Save fetched jobs to CSV file"""
        try:
            with open(filename, mode='w', newline='', encoding='utf-8') as csv_file:
                fieldnames = ['Job ID', 'Title', 'Company', 'Work Location', 'Work Style', 'Job Link', 'Description', 'Experience Required', 'Date Posted', 'Easy Apply Available']
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                writer.writeheader()
                
                for job in jobs:
                    writer.writerow({
                        'Job ID': job.job_id,
                        'Title': job.title,
                        'Company': job.company,
                        'Work Location': job.work_location,
                        'Work Style': job.work_style,
                        'Job Link': job.job_link,
                        'Description': job.description,
                        'Experience Required': job.experience_required,
                        'Date Posted': job.date_posted,
                        'Easy Apply Available': job.easy_apply_available
                    })
            
            print_lg(f"Successfully saved {len(jobs)} jobs to {filename}")
        except Exception as e:
            print_lg("Failed to save jobs to CSV!", e)

    def fetch_all_jobs(self, search_terms: List[str], max_jobs_per_search: int = 50) -> List[JobInfo]:
        """Fetch jobs for all search terms"""
        all_jobs = []
        
        if randomize_search_order:
            from random import shuffle
            shuffle(search_terms)
            
        for search_term in search_terms:
            print_lg("\n________________________________________________________________________________________________________________________\n")
            jobs = self.fetch_jobs_for_search_term(search_term, max_jobs_per_search)
            all_jobs.extend(jobs)
            
        return all_jobs

def main_fetch():
    """Main function for job fetching"""
    try:
        print_lg("Starting LinkedIn Job Fetcher...")
        
        # Validate configuration
        validate_config()
        print_lg("Configuration validated successfully")
        
        # Initialize fetcher
        fetcher = JobFetcher()
        fetcher.initialize_driver()
        fetcher.initialize_ai_client()
        
        # Login to LinkedIn
        print_lg("Step 1: Logging into LinkedIn...")
        if not fetcher.is_logged_in_LN(): 
            fetcher.login_LN()
        
        # Check sign in status
        print_lg("Step 2: Checking sign in status...")
        if not fetcher.check_sign_in():
            print_lg("❌ Sign in failed. Please check your credentials in config/secrets.py")
            return
        
        # Navigate to jobs
        print_lg("Step 3: Navigating to Jobs page...")
        fetcher.navigate_to_jobs()
        
        # Fetch jobs for all search terms
        print_lg("Step 4: Fetching jobs...")
        all_jobs = fetcher.fetch_all_jobs(search_terms)
        
        # Save to CSV
        print_lg("Step 5: Saving jobs to CSV...")
        fetcher.save_jobs_to_csv(all_jobs, "applicablejobs.csv")
        
        print_lg(f"\n✅ Job fetching completed successfully!")
        print_lg(f"Total jobs fetched: {len(all_jobs)}")
        print_lg(f"Jobs with Easy Apply: {sum(1 for job in all_jobs if job.easy_apply_available)}")
        print_lg(f"Jobs without Easy Apply: {sum(1 for job in all_jobs if not job.easy_apply_available)}")
        print_lg(f"Jobs saved to: applicablejobs.csv")
        
    except Exception as e:
        print_lg("❌ Error in job fetching:", e)
        raise e

if __name__ == "__main__":
    main_fetch()