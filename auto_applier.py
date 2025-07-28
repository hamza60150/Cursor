#!/usr/bin/env python3
"""
LinkedIn Auto Applier Module
Automatically applies to jobs from applicable.csv file
"""

import os
import csv
import re
import pyautogui
import time
from random import choice, shuffle, randint
from datetime import datetime
from typing import List, Dict, Set, Optional, Tuple, Literal
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
from config.secrets import use_AI, username, password, ai_provider
from config.settings import *

from modules.open_chrome import *
from modules.helpers import *
from modules.clickers_and_finders import *
from modules.validator import validate_config
from modules.ai.openaiConnections import ai_create_openai_client, ai_extract_skills, ai_answer_question, ai_close_openai_client
from modules.ai.deepseekConnections import deepseek_create_client, deepseek_extract_skills, deepseek_answer_question
from modules.ai.geminiConnections import gemini_create_client, gemini_extract_skills, gemini_answer_question

pyautogui.FAILSAFE = False

@dataclass
class JobApplication:
    """Data class to store job application information"""
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

class AutoApplier:
    """Class to handle auto-application functionality"""
    
    def __init__(self):
        self.applied_jobs = set()
        self.rejected_jobs = set()
        self.blacklisted_companies = set()
        self.randomly_answered_questions = set()
        self.easy_applied_count = 0
        self.external_jobs_count = 0
        self.failed_count = 0
        self.skip_count = 0
        self.dailyEasyApplyLimitReached = False
        self.tabs_count = 1
        self.useNewResume = True
        self.aiClient = None
        self.driver = None
        self.wait = None
        self.actions = None
        
        # Process personal information
        self.first_name = first_name.strip()
        self.middle_name = middle_name.strip()
        self.last_name = last_name.strip()
        self.full_name = self.first_name + " " + self.middle_name + " " + self.last_name if self.middle_name else self.first_name + " " + self.last_name
        
        # Process salary information
        self.desired_salary_lakhs = str(round(desired_salary / 100000, 2))
        self.desired_salary_monthly = str(round(desired_salary/12, 2))
        self.desired_salary = str(desired_salary)
        
        self.current_ctc_lakhs = str(round(current_ctc / 100000, 2))
        self.current_ctc_monthly = str(round(current_ctc/12, 2))
        self.current_ctc = str(current_ctc)
        
        # Process notice period
        self.notice_period_months = str(notice_period//30)
        self.notice_period_weeks = str(notice_period//7)
        self.notice_period = str(notice_period)
        
    def initialize_driver(self):
        """Initialize the web driver and related objects"""
        self.driver = driver
        self.wait = WebDriverWait(self.driver, 10)
        self.actions = actions
        
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
        """Login to LinkedIn"""
        self.driver.get("https://www.linkedin.com/login")
        try:
            self.wait.until(EC.presence_of_element_located((By.LINK_TEXT, "Forgot password?")))
            try:
                text_input_by_ID(self.driver, "username", username, 1)
            except Exception as e:
                print_lg("Couldn't find username field.")
            try:
                text_input_by_ID(self.driver, "password", password, 1)
            except Exception as e:
                print_lg("Couldn't find password field.")
            
            self.driver.find_element(By.XPATH, '//button[@type="submit" and contains(text(), "Sign in")]').click()
        except Exception as e1:
            try:
                profile_button = find_by_class(self.driver, "profile__details")
                profile_button.click()
            except Exception as e2:
                print_lg("Couldn't Login!")

        try:
            self.wait.until(EC.url_to_be("https://www.linkedin.com/feed/"))
            return print_lg("Login successful!")
        except Exception as e:
            print_lg("Seems like login attempt failed! Possibly due to wrong credentials or already logged in! Try logging in manually!")
            manual_login_retry(self.is_logged_in_LN, 2)

    def initialize_ai_client(self):
        """Initialize AI client if enabled"""
        if use_AI:
            if ai_provider == "openai":
                self.aiClient = ai_create_openai_client()
            elif ai_provider == "deepseek":
                self.aiClient = deepseek_create_client()
            elif ai_provider == "gemini":
                self.aiClient = gemini_create_client()

    def load_jobs_from_csv(self, filename: str = "applicable.csv") -> List[JobApplication]:
        """Load jobs from CSV file"""
        jobs = []
        try:
            with open(filename, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    job = JobApplication(
                        job_id=row['Job ID'],
                        title=row['Title'],
                        company=row['Company'],
                        work_location=row['Work Location'],
                        work_style=row['Work Style'],
                        job_link=row['Job Link'],
                        description=row['Description'],
                        experience_required=int(row['Experience Required']) if row['Experience Required'].isdigit() else 0,
                        date_posted=row['Date Posted'],
                        easy_apply_available=row['Easy Apply Available'].lower() == 'true'
                    )
                    jobs.append(job)
            print_lg(f"Loaded {len(jobs)} jobs from {filename}")
        except FileNotFoundError:
            print_lg(f"File {filename} not found. Please run job_fetcher.py first.")
        except Exception as e:
            print_lg(f"Error loading jobs from {filename}: {e}")
        return jobs

    def get_applied_job_ids(self) -> Set[str]:
        """Get set of already applied job IDs"""
        job_ids = set()
        try:
            with open(file_name, 'r', encoding='utf-8') as file:
                reader = csv.reader(file)
                for row in reader:
                    job_ids.add(row[0])
        except FileNotFoundError:
            print_lg(f"The CSV file '{file_name}' does not exist.")
        return job_ids

    def upload_resume(self, modal: WebElement, resume: str) -> Tuple[bool, str]:
        """Upload resume to the application"""
        try:
            modal.find_element(By.NAME, "file").send_keys(os.path.abspath(resume))
            return True, os.path.basename(default_resume_path)
        except: 
            return False, "Previous resume"

    def answer_common_questions(self, label: str, answer: str) -> str:
        """Answer common questions based on label"""
        if 'sponsorship' in label or 'visa' in label: 
            answer = require_visa
        return answer

    def answer_questions(self, modal: WebElement, questions_list: set, work_location: str, job_description: str | None = None) -> set:
        """Answer questions in the application form"""
        all_questions = modal.find_elements(By.XPATH, ".//div[@data-test-form-element]")

        for Question in all_questions:
            # Check if it's a select Question
            select = try_xp(Question, ".//select", False)
            if select:
                label_org = "Unknown"
                try:
                    label = Question.find_element(By.TAG_NAME, "label")
                    label_org = label.find_element(By.TAG_NAME, "span").text
                except: 
                    pass
                answer = 'Yes'
                label = label_org.lower()
                select = Select(select)
                selected_option = select.first_selected_option.text
                optionsText = []
                options = '"List of phone country codes"'
                if label != "phone country code":
                    optionsText = [option.text for option in select.options]
                    options = "".join([f' "{option}",' for option in optionsText])
                prev_answer = selected_option
                if overwrite_previous_answers or selected_option == "Select an option":
                    if 'email' in label or 'phone' in label: 
                        answer = prev_answer
                    elif 'gender' in label or 'sex' in label: 
                        answer = gender
                    elif 'disability' in label: 
                        answer = disability_status
                    elif 'proficiency' in label: 
                        answer = 'Professional'
                    elif any(loc_word in label for loc_word in ['location', 'city', 'state', 'country']):
                        if 'country' in label:
                            answer = country 
                        elif 'state' in label:
                            answer = state
                        elif 'city' in label:
                            answer = current_city if current_city else work_location
                        else:
                            answer = work_location
                    else: 
                        answer = self.answer_common_questions(label, answer)
                    try: 
                        select.select_by_visible_text(answer)
                    except NoSuchElementException as e:
                        possible_answer_phrases = []
                        if answer == 'Decline':
                            possible_answer_phrases = ["Decline", "not wish", "don't wish", "Prefer not", "not want"]
                        elif 'yes' in answer.lower():
                            possible_answer_phrases = ["Yes", "Agree", "I do", "I have"]
                        elif 'no' in answer.lower():
                            possible_answer_phrases = ["No", "Disagree", "I don't", "I do not"]
                        else:
                            possible_answer_phrases = [answer]
                            possible_answer_phrases.append(answer.lower())
                            possible_answer_phrases.append(answer.upper())
                            possible_answer_phrases.append(''.join(c for c in answer if c.isalnum()))
                        
                        foundOption = False
                        for phrase in possible_answer_phrases:
                            for option in optionsText:
                                if phrase.lower() in option.lower() or option.lower() in phrase.lower():
                                    select.select_by_visible_text(option)
                                    answer = option
                                    foundOption = True
                                    break
                        if not foundOption:
                            print_lg(f'Failed to find an option with text "{answer}" for question labelled "{label_org}", answering randomly!')
                            select.select_by_index(randint(1, len(select.options)-1))
                            answer = select.first_selected_option.text
                            self.randomly_answered_questions.add((f'{label_org} [ {options} ]',"select"))
                questions_list.add((f'{label_org} [ {options} ]', answer, "select", prev_answer))
                continue
            
            # Check if it's a radio Question
            radio = try_xp(Question, './/fieldset[@data-test-form-builder-radio-button-form-component="true"]', False)
            if radio:
                prev_answer = None
                label = try_xp(radio, './/span[@data-test-form-builder-radio-button-form-component__title]', False)
                try: 
                    label = find_by_class(label, "visually-hidden", 2.0)
                except: 
                    pass
                label_org = label.text if label else "Unknown"
                answer = 'Yes'
                label = label_org.lower()

                label_org += ' [ '
                options = radio.find_elements(By.TAG_NAME, 'input')
                options_labels = []
                
                for option in options:
                    id = option.get_attribute("id")
                    option_label = try_xp(radio, f'.//label[@for="{id}"]', False)
                    options_labels.append(f'"{option_label.text if option_label else "Unknown"}"<{option.get_attribute("value")}>')
                    if option.is_selected(): 
                        prev_answer = options_labels[-1]
                    label_org += f' {options_labels[-1]},'

                if overwrite_previous_answers or prev_answer is None:
                    if 'citizenship' in label or 'employment eligibility' in label: 
                        answer = us_citizenship
                    elif 'veteran' in label or 'protected' in label: 
                        answer = veteran_status
                    elif 'disability' in label or 'handicapped' in label: 
                        answer = disability_status
                    else: 
                        answer = self.answer_common_questions(label, answer)
                    foundOption = try_xp(radio, f".//label[normalize-space()='{answer}']", False)
                    if foundOption: 
                        self.actions.move_to_element(foundOption).click().perform()
                    else:    
                        possible_answer_phrases = ["Decline", "not wish", "don't wish", "Prefer not", "not want"] if answer == 'Decline' else [answer]
                        ele = options[0]
                        answer = options_labels[0]
                        for phrase in possible_answer_phrases:
                            for i, option_label in enumerate(options_labels):
                                if phrase in option_label:
                                    foundOption = options[i]
                                    ele = foundOption
                                    answer = f'Decline ({option_label})' if len(possible_answer_phrases) > 1 else option_label
                                    break
                            if foundOption: 
                                break
                        self.actions.move_to_element(ele).click().perform()
                        if not foundOption: 
                            self.randomly_answered_questions.add((f'{label_org} ]',"radio"))
                else: 
                    answer = prev_answer
                questions_list.add((label_org+" ]", answer, "radio", prev_answer))
                continue
            
            # Check if it's a text question
            text = try_xp(Question, ".//input[@type='text']", False)
            if text: 
                do_actions = False
                label = try_xp(Question, ".//label[@for]", False)
                try: 
                    label = label.find_element(By.CLASS_NAME,'visually-hidden')
                except: 
                    pass
                label_org = label.text if label else "Unknown"
                answer = ""
                label = label_org.lower()

                prev_answer = text.get_attribute("value")
                if not prev_answer or overwrite_previous_answers:
                    if 'experience' in label or 'years' in label: 
                        answer = years_of_experience
                    elif 'phone' in label or 'mobile' in label: 
                        answer = phone_number
                    elif 'street' in label: 
                        answer = street
                    elif 'city' in label or 'location' in label or 'address' in label:
                        answer = current_city if current_city else work_location
                        do_actions = True
                    elif 'signature' in label: 
                        answer = self.full_name
                    elif 'name' in label:
                        if 'full' in label: 
                            answer = self.full_name
                        elif 'first' in label and 'last' not in label: 
                            answer = self.first_name
                        elif 'middle' in label and 'last' not in label: 
                            answer = self.middle_name
                        elif 'last' in label and 'first' not in label: 
                            answer = self.last_name
                        elif 'employer' in label: 
                            answer = recent_employer
                        else: 
                            answer = self.full_name
                    elif 'notice' in label:
                        if 'month' in label:
                            answer = self.notice_period_months
                        elif 'week' in label:
                            answer = self.notice_period_weeks
                        else: 
                            answer = self.notice_period
                    elif 'salary' in label or 'compensation' in label or 'ctc' in label or 'pay' in label: 
                        if 'current' in label or 'present' in label:
                            if 'month' in label:
                                answer = self.current_ctc_monthly
                            elif 'lakh' in label:
                                answer = self.current_ctc_lakhs
                            else:
                                answer = self.current_ctc
                        else:
                            if 'month' in label:
                                answer = self.desired_salary_monthly
                            elif 'lakh' in label:
                                answer = self.desired_salary_lakhs
                            else:
                                answer = self.desired_salary
                    elif 'linkedin' in label: 
                        answer = linkedIn
                    elif 'website' in label or 'blog' in label or 'portfolio' in label or 'link' in label: 
                        answer = website
                    elif 'scale of 1-10' in label: 
                        answer = confidence_level
                    elif 'headline' in label: 
                        answer = linkedin_headline
                    elif ('hear' in label or 'come across' in label) and 'this' in label and ('job' in label or 'position' in label): 
                        answer = "https://github.com/GodsScion/Auto_job_applier_linkedIn"
                    elif 'state' in label or 'province' in label: 
                        answer = state
                    elif 'zip' in label or 'postal' in label or 'code' in label: 
                        answer = zipcode
                    elif 'country' in label: 
                        answer = country
                    else: 
                        answer = self.answer_common_questions(label, answer)
                    
                    if answer == "":
                        if use_AI and self.aiClient:
                            try:
                                if ai_provider.lower() == "openai":
                                    answer = ai_answer_question(self.aiClient, label_org, question_type="text", job_description=job_description, user_information_all=user_information_all)
                                elif ai_provider.lower() == "deepseek":
                                    answer = deepseek_answer_question(self.aiClient, label_org, options=None, question_type="text", job_description=job_description, about_company=None, user_information_all=user_information_all)
                                elif ai_provider.lower() == "gemini":
                                    answer = gemini_answer_question(self.aiClient, label_org, options=None, question_type="text", job_description=job_description, about_company=None, user_information_all=user_information_all)
                                else:
                                    self.randomly_answered_questions.add((label_org, "text"))
                                    answer = years_of_experience
                                if answer and isinstance(answer, str) and len(answer) > 0:
                                    print_lg(f'AI Answered received for question "{label_org}" \nhere is answer: "{answer}"')
                                else:
                                    self.randomly_answered_questions.add((label_org, "text"))
                                    answer = years_of_experience
                            except Exception as e:
                                print_lg("Failed to get AI answer!", e)
                                self.randomly_answered_questions.add((label_org, "text"))
                                answer = years_of_experience
                        else:
                            self.randomly_answered_questions.add((label_org, "text"))
                            answer = years_of_experience
                    text.clear()
                    text.send_keys(answer)
                    if do_actions:
                        time.sleep(2)
                        self.actions.send_keys(Keys.ARROW_DOWN)
                        self.actions.send_keys(Keys.ENTER).perform()
                questions_list.add((label, text.get_attribute("value"), "text", prev_answer))
                continue

            # Check if it's a textarea question
            text_area = try_xp(Question, ".//textarea", False)
            if text_area:
                label = try_xp(Question, ".//label[@for]", False)
                label_org = label.text if label else "Unknown"
                label = label_org.lower()
                answer = ""
                prev_answer = text_area.get_attribute("value")
                if not prev_answer or overwrite_previous_answers:
                    if 'summary' in label: 
                        answer = linkedin_summary
                    elif 'cover' in label: 
                        answer = cover_letter
                    if answer == "":
                        if use_AI and self.aiClient:
                            try:
                                if ai_provider.lower() == "openai":
                                    answer = ai_answer_question(self.aiClient, label_org, question_type="textarea", job_description=job_description, user_information_all=user_information_all)
                                elif ai_provider.lower() == "deepseek":
                                    answer = deepseek_answer_question(self.aiClient, label_org, options=None, question_type="textarea", job_description=job_description, about_company=None, user_information_all=user_information_all)
                                elif ai_provider.lower() == "gemini":
                                    answer = gemini_answer_question(self.aiClient, label_org, options=None, question_type="textarea", job_description=job_description, about_company=None, user_information_all=user_information_all)
                                else:
                                    self.randomly_answered_questions.add((label_org, "textarea"))
                                    answer = ""
                                if answer and isinstance(answer, str) and len(answer) > 0:
                                    print_lg(f'AI Answered received for question "{label_org}" \nhere is answer: "{answer}"')
                                else:
                                    self.randomly_answered_questions.add((label_org, "textarea"))
                                    answer = ""
                            except Exception as e:
                                print_lg("Failed to get AI answer!", e)
                                self.randomly_answered_questions.add((label_org, "textarea"))
                                answer = ""
                        else:
                            self.randomly_answered_questions.add((label_org, "textarea"))
                text_area.clear()
                text_area.send_keys(answer)
                if do_actions:
                    time.sleep(2)
                    self.actions.send_keys(Keys.ARROW_DOWN)
                    self.actions.send_keys(Keys.ENTER).perform()
                questions_list.add((label, text_area.get_attribute("value"), "textarea", prev_answer))
                continue

            # Check if it's a checkbox question
            checkbox = try_xp(Question, ".//input[@type='checkbox']", False)
            if checkbox:
                label = try_xp(Question, ".//span[@class='visually-hidden']", False)
                label_org = label.text if label else "Unknown"
                label = label_org.lower()
                answer = try_xp(Question, ".//label[@for]", False)
                answer = answer.text if answer else "Unknown"
                prev_answer = checkbox.is_selected()
                checked = prev_answer
                if not prev_answer:
                    try:
                        self.actions.move_to_element(checkbox).click().perform()
                        checked = True
                    except Exception as e: 
                        print_lg("Checkbox click failed!", e)
                        pass
                questions_list.add((f'{label} ([X] {answer})', checked, "checkbox", prev_answer))
                continue

        # Select todays date
        try_xp(self.driver, "//button[contains(@aria-label, 'This is today')]")

        return questions_list

    def follow_company(self, modal: WebElement) -> None:
        """Follow or un-follow easy applied companies based on follow_companies setting"""
        try:
            follow_checkbox_input = try_xp(modal, ".//input[@id='follow-company-checkbox' and @type='checkbox']", False)
            if follow_checkbox_input and follow_checkbox_input.is_selected() != follow_companies:
                try_xp(modal, ".//label[@for='follow-company-checkbox']")
        except Exception as e:
            print_lg("Failed to update follow companies checkbox!", e)

    def discard_job(self) -> None:
        """Discard the job application"""
        self.actions.send_keys(Keys.ESCAPE).perform()
        wait_span_click(self.driver, 'Discard', 2)

    def apply_to_job(self, job: JobApplication) -> bool:
        """Apply to a single job"""
        try:
            print_lg(f"\nApplying to: {job.title} | {job.company}")
            
            # Navigate to job page
            self.driver.get(job.job_link)
            buffer(click_gap)
            
            # Check if Easy Apply is available
            if not job.easy_apply_available:
                print_lg(f"Easy Apply not available for {job.title} | {job.company}")
                return False
                
            # Click Easy Apply button
            try:
                easy_apply_button = self.driver.find_element(By.XPATH, ".//button[contains(@class,'jobs-apply-button') and contains(@class, 'artdeco-button--3') and contains(@aria-label, 'Easy')]")
                easy_apply_button.click()
            except NoSuchElementException:
                print_lg(f"Easy Apply button not found for {job.title} | {job.company}")
                return False
                
            # Handle application process
            try:
                modal = find_by_class(self.driver, "jobs-easy-apply-modal")
                wait_span_click(modal, "Next", 1)
                
                resume = "Previous resume"
                next_button = True
                questions_list = set()
                next_counter = 0
                
                while next_button:
                    next_counter += 1
                    if next_counter >= 15: 
                        if pause_at_failed_question:
                            pyautogui.alert("Couldn't answer one or more questions.\nPlease click \"Continue\" once done.\nDO NOT CLICK Back, Next or Review button in LinkedIn.\n\n\n\n\nYou can turn off \"Pause at failed question\" setting in config.py", "Help Needed", "Continue")
                            next_counter = 1
                            continue
                        if questions_list: 
                            print_lg("Stuck for one or some of the following questions...", questions_list)
                        raise Exception("Seems like stuck in a continuous loop of next, probably because of new questions.")
                    
                    questions_list = self.answer_questions(modal, questions_list, job.work_location, job_description=job.description)
                    
                    if self.useNewResume:
                        uploaded, resume = self.upload_resume(modal, default_resume_path)
                        if uploaded:
                            self.useNewResume = False
                            
                    try: 
                        next_button = modal.find_element(By.XPATH, './/span[normalize-space(.)="Review"]') 
                    except NoSuchElementException:  
                        next_button = modal.find_element(By.XPATH, './/button[contains(span, "Next")]')
                    try: 
                        next_button.click()
                    except ElementClickInterceptedException: 
                        break
                    buffer(click_gap)

            except NoSuchElementException:
                print_lg("Failed to find Next button or modal")
                return False
            finally:
                if questions_list: 
                    print_lg("Answered the following questions...", questions_list)
                    print("\n\n" + "\n".join(str(question) for question in questions_list) + "\n\n")
                    
                wait_span_click(self.driver, "Review", 1, scrollTop=True)
                
                if pause_before_submit:
                    decision = pyautogui.confirm('1. Please verify your information.\n2. If you edited something, please return to this final screen.\n3. DO NOT CLICK "Submit Application".\n\n\n\n\nYou can turn off "Pause before submit" setting in config.py\nTo TEMPORARILY disable pausing, click "Disable Pause"', "Confirm your information",["Disable Pause", "Discard Application", "Submit Application"])
                    if decision == "Discard Application": 
                        raise Exception("Job application discarded by user!")
                    pause_before_submit = False if "Disable Pause" == decision else True
                    
                self.follow_company(modal)
                
                if wait_span_click(self.driver, "Submit application", 2, scrollTop=True): 
                    if not wait_span_click(self.driver, "Done", 2): 
                        self.actions.send_keys(Keys.ESCAPE).perform()
                    print_lg(f"Successfully applied to {job.title} | {job.company}")
                    return True
                else:
                    print_lg("Failed to submit application")
                    return False
                    
        except Exception as e:
            print_lg(f"Failed to apply to {job.title} | {job.company}: {e}")
            self.discard_job()
            return False

    def submitted_jobs(self, job: JobApplication, resume: str, questions_list: set, application_link: str = "Easy Applied"):
        """Save submitted job information to CSV"""
        try:
            with open(file_name, mode='a', newline='', encoding='utf-8') as csv_file:
                fieldnames = ['Job ID', 'Title', 'Company', 'Work Location', 'Work Style', 'About Job', 'Experience required', 'Skills required', 'HR Name', 'HR Link', 'Resume', 'Re-posted', 'Date Posted', 'Date Applied', 'Job Link', 'External Job link', 'Questions Found', 'Connect Request']
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
                if csv_file.tell() == 0: 
                    writer.writeheader()
                writer.writerow({
                    'Job ID': job.job_id, 
                    'Title': job.title, 
                    'Company': job.company, 
                    'Work Location': job.work_location, 
                    'Work Style': job.work_style, 
                    'About Job': job.description, 
                    'Experience required': job.experience_required, 
                    'Skills required': "Needs an AI", 
                    'HR Name': "Unknown", 
                    'HR Link': "Unknown", 
                    'Resume': resume, 
                    'Re-posted': False, 
                    'Date Posted': job.date_posted, 
                    'Date Applied': datetime.now(), 
                    'Job Link': job.job_link, 
                    'External Job link': application_link, 
                    'Questions Found': questions_list, 
                    'Connect Request': "In Development"
                })
            csv_file.close()
        except Exception as e:
            print_lg("Failed to update submitted jobs list!", e)

    def apply_to_jobs(self, jobs: List[JobApplication], max_applications: int = 10):
        """Apply to multiple jobs"""
        applied_jobs = self.get_applied_job_ids()
        
        for i, job in enumerate(jobs):
            if i >= max_applications:
                break
                
            if job.job_id in applied_jobs:
                print_lg(f"Already applied to {job.title} | {job.company}")
                continue
                
            if self.dailyEasyApplyLimitReached:
                print_lg("Daily Easy Apply limit reached!")
                break
                
            success = self.apply_to_job(job)
            
            if success:
                self.easy_applied_count += 1
                self.submitted_jobs(job, "Previous resume", set())
                applied_jobs.add(job.job_id)
            else:
                self.failed_count += 1

def main_apply():
    """Main function for auto-applying"""
    try:
        validate_config()
        
        applier = AutoApplier()
        applier.initialize_driver()
        applier.initialize_ai_client()
        
        # Login to LinkedIn
        if not applier.is_logged_in_LN(): 
            applier.login_LN()
        
        # Load jobs from CSV
        jobs = applier.load_jobs_from_csv()
        
        if not jobs:
            print_lg("No jobs found in applicable.csv. Please run job_fetcher.py first.")
            return
            
        # Filter jobs with Easy Apply
        easy_apply_jobs = [job for job in jobs if job.easy_apply_available]
        
        print_lg(f"Found {len(jobs)} total jobs, {len(easy_apply_jobs)} with Easy Apply")
        
        # Apply to jobs
        applier.apply_to_jobs(easy_apply_jobs, max_applications=10)
        
        print_lg(f"\nApplication Summary:")
        print_lg(f"Successfully applied: {applier.easy_applied_count}")
        print_lg(f"Failed applications: {applier.failed_count}")
        print_lg(f"Randomly answered questions: {len(applier.randomly_answered_questions)}")
        
    except Exception as e:
        print_lg("Error in auto-applying:", e)
        raise e

if __name__ == "__main__":
    main_apply()