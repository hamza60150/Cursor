#!/usr/bin/env python3
"""
Chrome browser setup module
"""

import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# Global variables for driver and actions
driver = None
wait = None
actions = None

def setup_driver(headless: bool = False):
    """Setup Chrome driver with undetected-chromedriver"""
    global driver, wait, actions
    
    options = uc.ChromeOptions()
    
    if headless:
        options.add_argument('--headless')
    
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    driver = uc.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    wait = WebDriverWait(driver, 10)
    actions = ActionChains(driver)
    
    return driver

def get_driver():
    """Get the global driver instance"""
    return driver

def get_wait():
    """Get the global wait instance"""
    return wait

def get_actions():
    """Get the global actions instance"""
    return actions