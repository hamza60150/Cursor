#!/usr/bin/env python3
"""
UI interaction functions module
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException

def try_xp(driver, xpath: str, timeout: float = 5.0, click: bool = False, scroll: bool = False):
    """Try to find element by XPath"""
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        if scroll:
            scroll_to_view(driver, element)
        if click:
            element.click()
        return element
    except TimeoutException:
        return None

def try_linkText(driver, link_text: str, timeout: float = 5.0):
    """Try to find element by link text"""
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.LINK_TEXT, link_text))
        )
        return element
    except TimeoutException:
        return None

def find_by_class(driver, class_name: str, timeout: float = 10.0):
    """Find element by class name"""
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CLASS_NAME, class_name))
        )
        return element
    except TimeoutException:
        return None

def try_find_by_classes(driver, class_names: list):
    """Try to find element by multiple class names"""
    for class_name in class_names:
        try:
            element = driver.find_element(By.CLASS_NAME, class_name)
            return element
        except NoSuchElementException:
            continue
    return None

def scroll_to_view(driver, element, click: bool = False):
    """Scroll element into view"""
    try:
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        time.sleep(0.5)
        if click:
            element.click()
    except Exception as e:
        print_lg(f"Scroll to view failed: {e}")

def text_input_by_ID(driver, element_id: str, text: str, delay: float = 1.0):
    """Input text by element ID"""
    try:
        element = driver.find_element(By.ID, element_id)
        element.clear()
        time.sleep(delay)
        element.send_keys(text)
        return True
    except Exception as e:
        print_lg(f"Text input by ID failed: {e}")
        return False

def text_input(actions, element, text: str, field_name: str = ""):
    """Input text using actions"""
    try:
        actions.move_to_element(element).click().perform()
        time.sleep(0.5)
        actions.send_keys(text).perform()
        print_lg(f"Text input successful for {field_name}")
        return True
    except Exception as e:
        print_lg(f"Text input failed for {field_name}: {e}")
        return False

def wait_span_click(driver, text: str, timeout: float = 10.0, scrollTop: bool = False, click: bool = True):
    """Wait for and click element with specific text"""
    try:
        xpath = f"//span[normalize-space()='{text}']"
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        if scrollTop:
            driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
        if click:
            element.click()
        return element
    except TimeoutException:
        return None

def multi_sel_noWait(driver, options: list, actions=None):
    """Multi-select without waiting"""
    if not options:
        return
    
    try:
        for option in options:
            try:
                element = driver.find_element(By.XPATH, f"//span[normalize-space()='{option}']")
                if not element.is_selected():
                    element.click()
                    time.sleep(0.5)
            except NoSuchElementException:
                continue
    except Exception as e:
        print_lg(f"Multi-select failed: {e}")

def boolean_button_click(driver, actions, button_text: str):
    """Click boolean button (checkbox/toggle)"""
    try:
        element = driver.find_element(By.XPATH, f"//span[normalize-space()='{button_text}']")
        if not element.is_selected():
            element.click()
            time.sleep(0.5)
    except NoSuchElementException:
        pass